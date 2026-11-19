"""Evaluate offline GNSS eta/u/v direction estimates against reference bearings."""

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

API_ROOT = Path(__file__).resolve().parents[1] / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.domain.wave_direction_experiment import (  # noqa: E402
    WaveDirectionSample,
    estimate_mean_direction_at_peak_frequency,
)


REQUIRED_COLUMNS = {
    "window_id",
    "split",
    "measured_at",
    "elevation_m",
    "velocity_east_mps",
    "velocity_north_mps",
    "reference_direction_towards_degrees",
}
VALID_QUALITIES = {"good", "suspect", "invalid"}


def load_windows(path: Path) -> tuple[dict[str, dict], dict[str, object]]:
    windows: dict[str, dict] = {}
    seen_timestamps: dict[datetime, str] = {}
    quality_counts = {quality: 0 for quality in VALID_QUALITIES}
    quality_column_present = False
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames or []
        if any(not (name or "").strip() for name in fieldnames):
            raise ValueError("CSV contains an empty column name")
        duplicates = sorted(name for name in set(fieldnames) if fieldnames.count(name) > 1)
        if duplicates:
            raise ValueError(f"CSV contains duplicate columns: {', '.join(duplicates)}")
        missing = REQUIRED_COLUMNS - set(fieldnames)
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")
        quality_column_present = "quality" in fieldnames
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
            timestamp = _parse_timestamp(row["measured_at"], line_number)
            quality = (
                (row.get("quality") or "good").strip().lower()
                if quality_column_present
                else "good"
            )
            if quality not in VALID_QUALITIES:
                raise ValueError(
                    f"Line {line_number}: quality must be 'good', 'suspect' or 'invalid'"
                )
            quality_counts[quality] += 1
            previous_window = seen_timestamps.get(timestamp)
            if previous_window is not None:
                raise ValueError(
                    f"Line {line_number}: timestamp is duplicated in window "
                    f"{window_id!r} or reused after {previous_window!r}"
                )
            seen_timestamps[timestamp] = window_id
            reference = _finite_number(
                row["reference_direction_towards_degrees"], line_number
            )
            if not 0 <= reference < 360:
                raise ValueError(
                    f"Line {line_number}: reference direction must be in [0, 360)"
                )
            entry = windows.setdefault(
                window_id,
                {
                    "split": split,
                    "reference": reference,
                    "timestamps": [],
                    "samples": [],
                },
            )
            if entry["split"] != split:
                raise ValueError(f"Window {window_id!r} appears in both data splits")
            if not math.isclose(entry["reference"], reference, abs_tol=1e-6):
                raise ValueError(
                    f"Line {line_number}: reference direction changes within "
                    f"window {window_id!r}"
                )
            entry["timestamps"].append(timestamp)
            if quality != "good":
                continue
            sample = WaveDirectionSample(
                measured_at=timestamp,
                elevation_m=_finite_number(row["elevation_m"], line_number),
                velocity_east_mps=_finite_number(
                    row["velocity_east_mps"], line_number
                ),
                velocity_north_mps=_finite_number(
                    row["velocity_north_mps"], line_number
                ),
            )
            entry["samples"].append(sample)

    if not windows:
        raise ValueError("CSV contains no data windows")
    split_counts = {
        split: sum(window["split"] == split for window in windows.values())
        for split in ("calibration", "validation")
    }
    if not all(split_counts.values()):
        raise ValueError("CSV must contain calibration and validation windows")

    ordered_intervals = sorted(
        (min(window["timestamps"]), max(window["timestamps"]), window_id, window["split"])
        for window_id, window in windows.items()
    )
    previous: tuple[datetime, datetime, str, str] | None = None
    for current in ordered_intervals:
        if previous is not None and current[0] <= previous[1]:
            raise ValueError(
                f"{previous[3].title()} window {previous[2]!r} overlaps "
                f"{current[3]} window {current[2]!r} in time"
            )
        previous = current

    quality_summary = {
        "column_present": quality_column_present,
        "accepted_good_rows": quality_counts["good"],
        "excluded_suspect_rows": quality_counts["suspect"],
        "excluded_invalid_rows": quality_counts["invalid"],
    }
    return windows, quality_summary


def evaluate_windows(
    windows: dict[str, dict],
    *,
    minimum_frequency_hz: float,
    maximum_frequency_hz: float,
    segment_length: int | None,
) -> tuple[dict[str, list[dict]], dict[str, list[dict]], dict[str, dict]]:
    estimates = {"calibration": [], "validation": []}
    coverage = {"calibration": [], "validation": []}
    for window_id, window in windows.items():
        samples = sorted(window["samples"], key=lambda sample: sample.measured_at)
        try:
            estimate = estimate_mean_direction_at_peak_frequency(
                samples,
                minimum_frequency_hz=minimum_frequency_hz,
                maximum_frequency_hz=maximum_frequency_hz,
                segment_length=segment_length,
            )
        except ValueError as exc:
            raise ValueError(f"Window {window_id!r}: {exc}") from exc
        timestamps = [sample.measured_at for sample in samples]
        intervals = [
            (right - left).total_seconds()
            for left, right in zip(timestamps, timestamps[1:])
        ]
        error = (
            _signed_angular_error(
                estimate.mean_direction_towards_degrees,
                window["reference"],
            )
            if estimate.mean_direction_towards_degrees is not None
            else None
        )
        estimates[window["split"]].append(
            {
                "window_id": window_id,
                "reference_direction_towards_degrees": window["reference"],
                "estimated_mean_direction_towards_degrees": (
                    estimate.mean_direction_towards_degrees
                ),
                "signed_error_degrees": round(error, 3) if error is not None else None,
                "absolute_error_degrees": round(abs(error), 3) if error is not None else None,
                "peak_frequency_hz": estimate.peak_frequency_hz,
                "directional_concentration": estimate.directional_concentration,
            }
        )
        coverage[window["split"]].append(
            {
                "window_id": window_id,
                "good_samples": len(samples),
                "duration_seconds": round(
                    (timestamps[-1] - timestamps[0]).total_seconds(), 6
                ),
                "median_interval_seconds": round(median(intervals), 6),
                "maximum_interval_seconds": round(max(intervals), 6),
                "segments": estimate.segment_count,
                "segment_length": estimate.segment_length,
            }
        )
    return (
        estimates,
        coverage,
        {split: _error_metrics(rows) for split, rows in estimates.items()},
    )


def _error_metrics(rows: list[dict]) -> dict:
    errors = [
        row["signed_error_degrees"]
        for row in rows
        if row["signed_error_degrees"] is not None
    ]
    if not errors:
        return {
            "estimated_windows": 0,
            "withheld_windows": len(rows),
            "mean_absolute_error_degrees": None,
            "root_mean_square_error_degrees": None,
            "mean_signed_error_degrees": None,
        }
    return {
        "estimated_windows": len(errors),
        "withheld_windows": len(rows) - len(errors),
        "mean_absolute_error_degrees": round(mean(abs(error) for error in errors), 3),
        "root_mean_square_error_degrees": round(
            math.sqrt(mean(error**2 for error in errors)), 3
        ),
        "mean_signed_error_degrees": round(mean(errors), 3),
    }


def _signed_angular_error(estimate: float, reference: float) -> float:
    return (estimate - reference + 180) % 360 - 180


def _finite_number(value: str | None, line_number: int) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Line {line_number}: invalid or missing numeric value") from exc
    if not math.isfinite(number):
        raise ValueError(f"Line {line_number}: numeric values must be finite")
    return number


def _parse_timestamp(value: str | None, line_number: int) -> datetime:
    if not value:
        raise ValueError(f"Line {line_number}: timestamp is required")
    try:
        timestamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Line {line_number}: timestamp must be ISO 8601") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"Line {line_number}: timestamp must include a timezone")
    return timestamp.astimezone(timezone.utc)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="CSV containing labeled direction windows")
    parser.add_argument("--minimum-frequency-hz", type=float, required=True)
    parser.add_argument("--maximum-frequency-hz", type=float, required=True)
    parser.add_argument("--segment-length", type=int)
    args = parser.parse_args()
    if (
        not math.isfinite(args.minimum_frequency_hz)
        or not math.isfinite(args.maximum_frequency_hz)
        or not 0 < args.minimum_frequency_hz < args.maximum_frequency_hz
    ):
        parser.error("frequency bounds must be finite, positive and increasing")
    try:
        windows, quality_summary = load_windows(args.csv_path)
        estimates, coverage, metrics = evaluate_windows(
            windows,
            minimum_frequency_hz=args.minimum_frequency_hz,
            maximum_frequency_hz=args.maximum_frequency_hz,
            segment_length=args.segment_length,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    report = {
        "warning": "Offline exploratory estimate only; not validated for operational use.",
        "dataset": {
            "file_name": args.csv_path.name,
            "sha256": _sha256_file(args.csv_path),
            "quality_filter": quality_summary,
        },
        "frequency_band_hz": [args.minimum_frequency_hz, args.maximum_frequency_hz],
        "segment_length": args.segment_length,
        "window_counts": {split: len(rows) for split, rows in estimates.items()},
        "metrics": metrics,
        "window_coverage": coverage,
        "window_estimates": estimates,
    }
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
