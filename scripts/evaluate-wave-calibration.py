"""Compare the experimental GNSS/IMU estimate with independently measured waves."""

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def load_windows(path: Path) -> dict[str, list[WaveCalibrationWindow]]:
    grouped: dict[str, dict] = {}
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")
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
            if measured_at in entry["timestamps"]:
                raise ValueError(
                    f"Line {line_number}: duplicate timestamp in window {window_id!r}"
                )
            entry["timestamps"].add(measured_at)
            if altitude is not None:
                entry["altitudes"].append(altitude)
            if acceleration is not None:
                entry["accelerations"].append(acceleration)

    result = {"calibration": [], "validation": []}
    for window_id, values in grouped.items():
        if len(values["altitudes"]) < 2 or len(values["accelerations"]) < 2:
            raise ValueError(
                f"Window {window_id!r} needs at least two GNSS and two IMU samples"
            )
        result[values["split"]].append(
            WaveCalibrationWindow(
                gnss_altitudes_m=tuple(values["altitudes"]),
                imu_vertical_accelerations_mps2=tuple(values["accelerations"]),
                reference_wave_height_m=values["reference"],
            )
        )
    if not result["calibration"] or not result["validation"]:
        raise ValueError("CSV must contain at least one calibration and validation window")
    return result


def _optional_number(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("sensor values must be finite")
    return number


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
        splits = load_windows(args.csv_path)
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
            "calibration_windows": len(splits["calibration"]),
            "validation_windows": len(splits["validation"]),
            "baseline_factor": args.baseline_factor,
            "selected_factor": selected_factor,
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
