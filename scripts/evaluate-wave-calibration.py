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

from app.domain.analytics.wave_calibration import (  # noqa: E402
    WaveCalibrationWindow,
    evaluate_factor,
    select_factor,
)
from app.domain.analytics.wave import estimate_wave  # noqa: E402


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
    quality_row_counts = {"good": 0, "suspect": 0, "invalid": 0}
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames or ()
        if any(not (name or "").strip() for name in fieldnames):
            raise ValueError("CSV contains an empty column name")
        duplicate_columns = sorted(
            name for name in set(fieldnames) if fieldnames.count(name) > 1
        )
        if duplicate_columns:
            raise ValueError(
                f"CSV contains duplicate columns: {', '.join(duplicate_columns)}"
            )
        missing = REQUIRED_COLUMNS - set(fieldnames)
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")
        quality_column_present = "quality" in fieldnames
        uncertainty_column_present = "reference_uncertainty_m" in fieldnames
        for line_number, row in enumerate(reader, start=2):
            if row.get(None):
                raise ValueError(f"Line {line_number}: too many CSV fields")
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
            if quality not in quality_row_counts:
                raise ValueError(
                    f"Line {line_number}: quality must be 'good', 'suspect' or 'invalid'"
                )
            quality_row_counts[quality] += 1
            if quality != "good":
                continue
            try:
                reference = float(row["reference_wave_height_m"])
                altitude = _optional_number(row["gnss_altitude_m"])
                acceleration = _optional_number(
                    row["imu_vertical_acceleration_mps2"]
                )
                uncertainty = (
                    _optional_number(row["reference_uncertainty_m"])
                    if uncertainty_column_present
                    else None
                )
            except TypeError as exc:
                raise ValueError(f"Line {line_number}: incomplete CSV row") from exc
            except ValueError as exc:
                raise ValueError(f"Line {line_number}: invalid numeric value") from exc
            if not math.isfinite(reference) or reference < 0:
                raise ValueError(
                    f"Line {line_number}: reference height must be finite and non-negative"
                )
            if uncertainty_column_present and (
                uncertainty is None or uncertainty <= 0
            ):
                raise ValueError(
                    f"Line {line_number}: reference uncertainty must be finite and positive"
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
                    "reference_uncertainty": uncertainty,
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
            previous_uncertainty = entry["reference_uncertainty"]
            if previous_uncertainty is not None and uncertainty is not None:
                uncertainty_matches = math.isclose(
                    previous_uncertainty, uncertainty, rel_tol=1e-6, abs_tol=1e-6
                )
            else:
                uncertainty_matches = previous_uncertainty is uncertainty
            if not uncertainty_matches:
                raise ValueError(
                    f"Line {line_number}: reference uncertainty changes within "
                    f"window {window_id!r}"
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
                reference_uncertainty_m=values["reference_uncertainty"],
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
        "accepted_good_rows": quality_row_counts["good"],
        "excluded_suspect_rows": quality_row_counts["suspect"],
        "excluded_invalid_rows": quality_row_counts["invalid"],
    }
    all_intervals = sorted(
        (start_at, end_at, window_id, split)
        for split, split_intervals in intervals.items()
        for window_id, start_at, end_at in split_intervals
    )
    active_interval = None
    for current_interval in all_intervals:
        if active_interval is not None and current_interval[0] <= active_interval[1]:
            _, _, previous_id, previous_split = active_interval
            _, _, current_id, current_split = current_interval
            raise ValueError(
                f"{previous_split.title()} window {previous_id!r} overlaps "
                f"{current_split} window {current_id!r} in time"
            )
        if active_interval is None or current_interval[1] > active_interval[1]:
            active_interval = current_interval
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


def _window_estimates(
    windows: list[WaveCalibrationWindow],
    coverage: list[dict],
    baseline_factor: float,
    selected_factor: float,
) -> list[dict]:
    results = []
    for window, metadata in zip(windows, coverage, strict=True):
        baseline = estimate_wave(
            window.gnss_altitudes_m,
            window.imu_vertical_accelerations_mps2,
            baseline_factor,
        ).estimated_wave_height_m
        selected = estimate_wave(
            window.gnss_altitudes_m,
            window.imu_vertical_accelerations_mps2,
            selected_factor,
        ).estimated_wave_height_m
        if baseline is None or selected is None:
            raise ValueError("Every evaluated window must produce a wave-height estimate")
        results.append(
            {
                "window_id": metadata["window_id"],
                "reference_wave_height_m": window.reference_wave_height_m,
                "reference_uncertainty_m": window.reference_uncertainty_m,
                "baseline_estimated_wave_height_m": baseline,
                "baseline_error_m": round(
                    baseline - window.reference_wave_height_m, 6
                ),
                "selected_estimated_wave_height_m": selected,
                "selected_error_m": round(
                    selected - window.reference_wave_height_m, 6
                ),
                "baseline_error_in_reference_uncertainties": (
                    round(
                        (baseline - window.reference_wave_height_m)
                        / window.reference_uncertainty_m,
                        6,
                    )
                    if window.reference_uncertainty_m is not None
                    else None
                ),
                "selected_error_in_reference_uncertainties": (
                    round(
                        (selected - window.reference_wave_height_m)
                        / window.reference_uncertainty_m,
                        6,
                    )
                    if window.reference_uncertainty_m is not None
                    else None
                ),
            }
        )
    return results


def _factor_candidates(max_factor: float, step: float) -> list[float]:
    ratio = max_factor / step
    nearest_step_count = round(ratio)
    reaches_maximum = math.isclose(
        ratio, nearest_step_count, rel_tol=1e-12, abs_tol=0.0
    )
    full_step_count = (
        nearest_step_count if reaches_maximum else math.floor(ratio)
    )
    candidate_count = full_step_count + 1 + (not reaches_maximum)
    if candidate_count > 100_001:
        raise ValueError("--step would produce more than 100,001 factor candidates")

    candidates = [index * step for index in range(full_step_count + 1)]
    if reaches_maximum:
        candidates[-1] = max_factor
    else:
        candidates.append(max_factor)
    has_duplicate_candidates = any(
        current <= previous
        for previous, current in zip(candidates, candidates[1:])
    )
    if has_duplicate_candidates:
        raise ValueError("--step is too small to produce distinct factor candidates")
    return candidates


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
    try:
        candidates = _factor_candidates(args.max_factor, args.step)
    except ValueError as exc:
        parser.error(str(exc))

    try:
        splits, window_coverage, quality_summary = load_windows(args.csv_path)
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
            "window_estimates": {
                split: _window_estimates(
                    splits[split],
                    window_coverage[split],
                    args.baseline_factor,
                    selected_factor,
                )
                for split in ("calibration", "validation")
            },
            "calibration_baseline_metrics": evaluate_factor(
                splits["calibration"], args.baseline_factor
            ),
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
