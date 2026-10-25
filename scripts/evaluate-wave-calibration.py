"""Compare the experimental GNSS/IMU estimate with independently measured waves."""

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

API_ROOT = Path(__file__).resolve().parents[1] / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.domain.wave_calibration import (  # noqa: E402
    WaveCalibrationWindow,
    evaluate_factor,
    select_factor,
)


REQUIRED_COLUMNS = {
    "window_id",
    "split",
    "measured_at",
    "gnss_altitude_m",
    "imu_vertical_acceleration_mps2",
    "reference_wave_height_m",
}


def load_windows(
    path: Path,
) -> tuple[
    dict[str, list[WaveCalibrationWindow]],
    dict[str, list[dict]],
    dict[str, object],
]:
    grouped: dict[str, dict] = {}
    seen_timestamps: dict[datetime, tuple[str, set[str]]] = {}
    quality_column_present = False
    quality_counts = {"good": 0, "suspect": 0, "invalid": 0}
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")
        quality_column_present = "quality" in (reader.fieldnames or ())
        for line_number, row in enumerate(reader, start=2):
            window_id = (row["window_id"] or "").strip()
            split = (row["split"] or "").strip().lower()
            if not window_id or split not in {"calibration", "validation"}:
                raise ValueError(
                    f"Line {line_number}: window_id is required and split must be "
                    "'calibration' or 'validation'"
                )
            try:
                measured_at = _parse_timestamp(row["measured_at"])
            except ValueError as exc:
                raise ValueError(f"Line {line_number}: {exc}") from exc
            quality_value = row.get("quality") if quality_column_present else "good"
            quality = (quality_value or "").strip().lower()
            if quality not in quality_counts:
                raise ValueError(
                    f"Line {line_number}: quality must be 'good', 'suspect' or 'invalid'"
                )
            quality_counts[quality] += 1
            if quality != "good":
                continue
            try:
                reference = float(row["reference_wave_height_m"])
                altitude = _optional_number(row["gnss_altitude_m"])
                acceleration = _optional_number(
                    row["imu_vertical_acceleration_mps2"]
                )
            except TypeError as exc:
                raise ValueError(f"Line {line_number}: incomplete CSV row") from exc
            except ValueError as exc:
                raise ValueError(f"Line {line_number}: invalid numeric value") from exc
            if not math.isfinite(reference) or reference < 0:
                raise ValueError(
                    f"Line {line_number}: reference height must be finite and non-negative"
                )
            if altitude is None and acceleration is None:
                raise ValueError(
                    f"Line {line_number}: good-quality row must contain a GNSS or IMU sample"
                )
            entry = grouped.setdefault(
                window_id,
                {
                    "split": split,
                    "reference": reference,
                    "altitudes": [],
                    "accelerations": [],
                    "timestamps": set(),
                },
            )
            if entry["split"] != split:
                raise ValueError(f"Window {window_id!r} appears in both data splits")
            if not math.isclose(entry["reference"], reference, rel_tol=1e-6, abs_tol=1e-6):
                raise ValueError(
                    f"Line {line_number}: reference height changes within window {window_id!r}"
                )
            modalities = {
                name
                for name, value in (
                    ("GNSS", altitude),
                    ("IMU", acceleration),
                )
                if value is not None
            }
            previous = seen_timestamps.get(measured_at)
            if previous is not None:
                previous_window, previous_modalities = previous
                if previous_window != window_id:
                    raise ValueError(
                        f"Line {line_number}: timestamp is reused by window "
                        f"{window_id!r} after {previous_window!r}"
                    )
                if previous_modalities.intersection(modalities):
                    raise ValueError(
                        f"Line {line_number}: duplicate timestamp in window {window_id!r}"
                    )
                previous_modalities.update(modalities)
            else:
                seen_timestamps[measured_at] = (window_id, modalities)
            entry["timestamps"].add(measured_at)
            if altitude is not None:
                entry["altitudes"].append((measured_at, altitude))
            if acceleration is not None:
                entry["accelerations"].append((measured_at, acceleration))

    result = {"calibration": [], "validation": []}
    coverage = {"calibration": [], "validation": []}
    intervals = {"calibration": [], "validation": []}
    for window_id, values in grouped.items():
        split = values["split"]
        start_at = min(values["timestamps"])
        end_at = max(values["timestamps"])
        intervals[split].append((window_id, start_at, end_at))
        if not values["altitudes"] or not values["accelerations"]:
            raise ValueError(
                f"Window {window_id!r} needs GNSS and IMU samples with overlapping ranges"
            )
        shared_start = max(
            min(timestamp for timestamp, _ in values["altitudes"]),
            min(timestamp for timestamp, _ in values["accelerations"]),
        )
        shared_end = min(
            max(timestamp for timestamp, _ in values["altitudes"]),
            max(timestamp for timestamp, _ in values["accelerations"]),
        )
        if shared_start > shared_end:
            raise ValueError(
                f"Window {window_id!r} has no overlapping GNSS and IMU sample ranges"
            )
        altitudes = [
            value
            for timestamp, value in values["altitudes"]
            if shared_start <= timestamp <= shared_end
        ]
        accelerations = [
            value
            for timestamp, value in values["accelerations"]
            if shared_start <= timestamp <= shared_end
        ]
        if len(altitudes) < 2 or len(accelerations) < 2:
            raise ValueError(
                f"Window {window_id!r} needs at least two GNSS and two IMU samples "
                "inside their shared time range"
            )
        result[split].append(
            WaveCalibrationWindow(
                gnss_altitudes_m=tuple(altitudes),
                imu_vertical_accelerations_mps2=tuple(accelerations),
                reference_wave_height_m=values["reference"],
            )
        )
        coverage[split].append(
            {
                "window_id": window_id,
                "duration_seconds": (shared_end - shared_start).total_seconds(),
                "gnss_samples": len(altitudes),
                "imu_samples": len(accelerations),
                "gnss_median_interval_seconds": _median_interval_seconds(
                    values["altitudes"], shared_start, shared_end
                ),
                "gnss_max_interval_seconds": _max_interval_seconds(
                    values["altitudes"], shared_start, shared_end
                ),
                "imu_median_interval_seconds": _median_interval_seconds(
                    values["accelerations"], shared_start, shared_end
                ),
                "imu_max_interval_seconds": _max_interval_seconds(
                    values["accelerations"], shared_start, shared_end
                ),
            }
        )
    if not result["calibration"] or not result["validation"]:
        raise ValueError("CSV must contain at least one calibration and validation window")
    quality_summary = {
        "column_present": quality_column_present,
        "accepted_good_samples": quality_counts["good"],
        "excluded_suspect_samples": quality_counts["suspect"],
        "excluded_invalid_samples": quality_counts["invalid"],
    }
    calibration = sorted(intervals["calibration"], key=lambda item: item[1])
    validation = sorted(intervals["validation"], key=lambda item: item[1])
    calibration_index = validation_index = 0
    while calibration_index < len(calibration) and validation_index < len(validation):
        calibration_id, calibration_start, calibration_end = calibration[calibration_index]
        validation_id, validation_start, validation_end = validation[validation_index]
        if calibration_start <= validation_end and validation_start <= calibration_end:
            raise ValueError(
                f"Calibration window {calibration_id!r} overlaps validation "
                f"window {validation_id!r} in time"
            )
        if calibration_end < validation_end:
            calibration_index += 1
        else:
            validation_index += 1
    return result, coverage, quality_summary


def _optional_number(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("sensor values must be finite")
    return number


def _sample_intervals_seconds(
    samples: list[tuple[datetime, float]], start: datetime, end: datetime
) -> list[float]:
    timestamps = sorted(
        timestamp for timestamp, _ in samples if start <= timestamp <= end
    )
    return [
        (current - previous).total_seconds()
        for previous, current in zip(timestamps, timestamps[1:])
    ]


def _median_interval_seconds(
    samples: list[tuple[datetime, float]], start: datetime, end: datetime
) -> float:
    return round(median(_sample_intervals_seconds(samples, start, end)), 6)


def _max_interval_seconds(
    samples: list[tuple[datetime, float]], start: datetime, end: datetime
) -> float:
    return round(max(_sample_intervals_seconds(samples, start, end)), 6)


def _parse_timestamp(value: str | None) -> datetime:
    if not value:
        raise ValueError("Line timestamp is required")
    try:
        timestamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Line timestamp must be ISO 8601") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("Line timestamp must include a timezone")
    return timestamp.astimezone(timezone.utc)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="CSV containing labeled windows")
    parser.add_argument("--baseline-factor", type=float, default=0.1)
    parser.add_argument("--max-factor", type=float, default=10.0)
    parser.add_argument("--step", type=float, default=0.01)
    args = parser.parse_args()
    if not math.isfinite(args.baseline_factor) or not (0 <= args.baseline_factor <= 10):
        parser.error("--baseline-factor must be between 0 and 10")
    if (
        not math.isfinite(args.max_factor)
        or not (0 < args.max_factor <= 10)
        or not math.isfinite(args.step)
        or args.step <= 0
    ):
        parser.error("--max-factor must be in (0, 10] and --step must be positive")
    step_count = math.floor(args.max_factor / args.step)
    if step_count > 100_000:
        parser.error("--step would produce more than 100,001 factor candidates")

    try:
        splits, window_coverage, quality_summary = load_windows(args.csv_path)
        candidates = [
            round(index * args.step, 10)
            for index in range(step_count + 1)
        ]
        if candidates[-1] < args.max_factor:
            candidates.append(args.max_factor)
        selected_factor, calibration_metrics = select_factor(
            splits["calibration"], candidates
        )
        report = {
            "warning": "Offline experiment only; do not apply without domain review.",
            "dataset": {
                "file_name": args.csv_path.name,
                "sha256": _sha256_file(args.csv_path),
                "quality_filter": quality_summary,
            },
            "search": {
                "min_factor": candidates[0],
                "max_factor": candidates[-1],
                "step": args.step,
                "candidate_count": len(candidates),
            },
            "calibration_windows": len(splits["calibration"]),
            "validation_windows": len(splits["validation"]),
            "baseline_factor": args.baseline_factor,
            "selected_factor": selected_factor,
            "window_coverage": window_coverage,
            "calibration_metrics": calibration_metrics,
            "validation_baseline_metrics": evaluate_factor(
                splits["validation"], args.baseline_factor
            ),
            "validation_selected_metrics": evaluate_factor(
                splits["validation"], selected_factor
            ),
        }
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
