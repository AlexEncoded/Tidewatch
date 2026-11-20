import csv
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "evaluate-wave-direction.py"
FIELDS = (
    "window_id",
    "split",
    "measured_at",
    "elevation_m",
    "velocity_east_mps",
    "velocity_north_mps",
    "reference_direction_towards_degrees",
    "quality",
    "hdop",
    "satellites",
)


def _write_dataset(
    path: Path,
    *,
    no_horizontal_motion: bool = False,
    include_bad_fixes: bool = False,
) -> None:
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDS)
        writer.writeheader()
        for window_id, split, start, direction in (
            ("calibration-1", "calibration", datetime(2026, 1, 1, tzinfo=timezone.utc), 120),
            ("validation-1", "validation", datetime(2026, 1, 1, 1, tzinfo=timezone.utc), 120),
        ):
            bearing = math.radians(direction)
            if include_bad_fixes:
                writer.writerow(
                    {
                        "window_id": window_id,
                        "split": split,
                        "measured_at": (start - timedelta(seconds=1)).isoformat(),
                        "elevation_m": 500,
                        "velocity_east_mps": 500,
                        "velocity_north_mps": 500,
                        "reference_direction_towards_degrees": direction,
                        "quality": "good",
                        "hdop": 5,
                        "satellites": 12,
                    }
                )
            for index in range(128):
                elevation = math.cos(2 * math.pi * index / 8)
                horizontal_speed = 0 if no_horizontal_motion else 0.15 * elevation
                writer.writerow(
                    {
                        "window_id": window_id,
                        "split": split,
                        "measured_at": (start + timedelta(seconds=index)).isoformat(),
                        "elevation_m": elevation,
                        "velocity_east_mps": horizontal_speed * math.sin(bearing),
                        "velocity_north_mps": horizontal_speed * math.cos(bearing),
                        "reference_direction_towards_degrees": direction,
                        "quality": "good",
                        "hdop": 0.8,
                        "satellites": 12,
                    }
                )
            if include_bad_fixes:
                writer.writerow(
                    {
                        "window_id": window_id,
                        "split": split,
                        "measured_at": (start + timedelta(seconds=128)).isoformat(),
                        "elevation_m": 500,
                        "velocity_east_mps": 500,
                        "velocity_north_mps": 500,
                        "reference_direction_towards_degrees": direction,
                        "quality": "good",
                        "hdop": 0.8,
                        "satellites": 3,
                    }
                )
            writer.writerow(
                {
                    "window_id": window_id,
                    "split": split,
                    "measured_at": (
                        start + timedelta(seconds=129 if include_bad_fixes else 128)
                    ).isoformat(),
                    "elevation_m": 500,
                    "velocity_east_mps": 500,
                    "velocity_north_mps": 500,
                    "reference_direction_towards_degrees": direction,
                    "quality": "suspect",
                    "hdop": 0.8,
                    "satellites": 12,
                }
            )


def _run_evaluator(
    path: Path, extra_args: tuple[str, ...] = ()
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(path),
            "--minimum-frequency-hz",
            "0.05",
            "--maximum-frequency-hz",
            "0.4",
            "--minimum-window-duration-seconds",
            "120",
            "--segment-length",
            "64",
            *extra_args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_wave_direction_cli_reports_holdout_angular_metrics(tmp_path: Path) -> None:
    dataset = tmp_path / "labeled-directions.csv"
    _write_dataset(dataset)

    result = _run_evaluator(dataset)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["metrics"]["calibration"]["mean_absolute_error_degrees"] == 0
    assert report["metrics"]["validation"]["root_mean_square_error_degrees"] == 0
    assert report["window_estimates"]["validation"][0][
        "estimated_mean_direction_towards_degrees"
    ] == 120
    assert report["window_coverage"]["calibration"][0]["good_samples"] == 128
    assert report["window_coverage"]["calibration"][0]["segment_length"] == 64
    coverage = report["window_coverage"]["calibration"][0]
    assert coverage["hdop_samples"] == 128
    assert coverage["hdop_missing_samples"] == 0
    assert coverage["hdop_median"] == 0.8
    assert coverage["hdop_max"] == 0.8
    assert coverage["satellite_samples"] == 128
    assert coverage["satellite_missing_samples"] == 0
    assert coverage["satellites_min"] == 12
    assert coverage["satellites_median"] == 12
    assert report["dataset"]["quality_filter"] == {
        "accepted_good_rows": 256,
        "column_present": True,
        "excluded_hdop_rows": 0,
        "excluded_invalid_rows": 0,
        "excluded_missing_hdop_rows": 0,
        "excluded_missing_satellite_rows": 0,
        "excluded_satellite_rows": 0,
        "excluded_suspect_rows": 2,
        "good_quality_rows": 256,
        "maximum_hdop": None,
        "minimum_satellites": None,
    }
    assert report["dataset"]["sha256"] == hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert report["warning"].startswith("Offline exploratory estimate only")


def test_wave_direction_cli_reports_windows_without_an_angle(tmp_path: Path) -> None:
    dataset = tmp_path / "no-horizontal-motion.csv"
    _write_dataset(dataset, no_horizontal_motion=True)

    result = _run_evaluator(dataset)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["metrics"]["validation"]["estimated_windows"] == 0
    assert report["metrics"]["validation"]["withheld_windows"] == 1
    assert report["window_estimates"]["validation"][0][
        "estimated_mean_direction_towards_degrees"
    ] is None


def test_wave_direction_cli_rejects_irregular_cadence_without_traceback(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "irregular-directions.csv"
    _write_dataset(dataset)
    content = dataset.read_text(encoding="utf-8")
    content = content.replace(
        "2026-01-01T00:00:30+00:00",
        "2026-01-01T00:00:30.200000+00:00",
        1,
    )
    dataset.write_text(content, encoding="utf-8")

    result = _run_evaluator(dataset)

    assert result.returncode == 2
    assert "uniform cadence without gaps" in result.stderr
    assert "Traceback" not in result.stderr


def test_wave_direction_cli_rejects_windows_shorter_than_protocol_minimum(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "short-directions.csv"
    _write_dataset(dataset)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(dataset),
            "--minimum-frequency-hz",
            "0.05",
            "--maximum-frequency-hz",
            "0.4",
            "--minimum-window-duration-seconds",
            "128",
            "--segment-length",
            "64",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "below the required 128s" in result.stderr
    assert "Traceback" not in result.stderr


def test_wave_direction_cli_filters_hdop_and_satellite_counts(tmp_path: Path) -> None:
    dataset = tmp_path / "gnss-quality-directions.csv"
    _write_dataset(dataset, include_bad_fixes=True)

    result = _run_evaluator(
        dataset,
        extra_args=("--maximum-hdop", "2.0", "--minimum-satellites", "8"),
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["metrics"]["validation"]["mean_absolute_error_degrees"] == 0
    assert report["dataset"]["quality_filter"] == {
        "accepted_good_rows": 256,
        "column_present": True,
        "excluded_hdop_rows": 2,
        "excluded_invalid_rows": 0,
        "excluded_missing_hdop_rows": 0,
        "excluded_missing_satellite_rows": 0,
        "excluded_satellite_rows": 2,
        "excluded_suspect_rows": 2,
        "good_quality_rows": 260,
        "maximum_hdop": 2.0,
        "minimum_satellites": 8,
    }


def test_wave_direction_cli_reports_missing_optional_gnss_metadata(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "legacy-directions.csv"
    _write_dataset(dataset)
    with dataset.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fields = [field for field in reader.fieldnames or [] if field not in {"hdop", "satellites"}]
        rows = list(reader)
    with dataset.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in rows)

    result = _run_evaluator(dataset)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    coverage = report["window_coverage"]["validation"][0]
    assert coverage["hdop_samples"] == 0
    assert coverage["hdop_missing_samples"] == 128
    assert coverage["hdop_median"] is None
    assert coverage["hdop_max"] is None
    assert coverage["satellite_samples"] == 0
    assert coverage["satellite_missing_samples"] == 128
    assert coverage["satellites_min"] is None
    assert coverage["satellites_median"] is None

    filtered = _run_evaluator(dataset, extra_args=("--maximum-hdop", "2.0"))
    assert filtered.returncode == 2
    assert "requires an hdop CSV column" in filtered.stderr
    assert "Traceback" not in filtered.stderr
