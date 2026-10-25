import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.domain.wave_calibration import (
    WaveCalibrationWindow,
    evaluate_factor,
    select_factor,
)


def test_select_factor_minimizes_calibration_error() -> None:
    windows = [
        WaveCalibrationWindow((0.0, 0.1), (0.0, 0.5), 0.15),
        WaveCalibrationWindow((0.0, 0.3), (0.0, 1.0), 0.35),
    ]

    factor, metrics = select_factor(windows, (0.0, 0.2, 0.4, 0.6))

    assert factor == 0.4
    assert metrics["rmse_m"] == 0


def test_select_factor_rejects_empty_windows_and_invalid_candidates() -> None:
    window = WaveCalibrationWindow((0.0, 0.1), (0.0, 0.5), 0.15)

    with pytest.raises(ValueError, match="At least one calibration window"):
        select_factor([], (0.1,))

    with pytest.raises(ValueError, match="factor between 0 and 10"):
        select_factor([window], (-1.0, 11.0))


@pytest.mark.parametrize(
    ("gnss_altitudes", "imu_accelerations"),
    (
        ((0.0, 0.1), ()),
        ((), (0.0, 0.5)),
    ),
)
def test_evaluate_factor_requires_both_sensor_modalities(
    gnss_altitudes: tuple[float, ...],
    imu_accelerations: tuple[float, ...],
) -> None:
    window = WaveCalibrationWindow(gnss_altitudes, imu_accelerations, 0.15)

    with pytest.raises(ValueError, match="enough GNSS and IMU samples"):
        evaluate_factor([window], 0.1)


def test_wave_calibration_cli_reports_holdout_metrics(tmp_path: Path) -> None:
    input_path = tmp_path / "labeled-waves.csv"
    rows = [
        ("train-a", "calibration", "2026-01-01T00:00:00Z", 0.0, 0.0, 0.15),
        ("train-a", "calibration", "2026-01-01T00:00:01Z", 0.1, 0.5, 0.15),
        ("train-b", "calibration", "2026-01-01T00:01:00Z", 0.0, 0.0, 0.35),
        ("train-b", "calibration", "2026-01-01T00:01:01Z", 0.3, 1.0, 0.35),
        ("holdout", "validation", "2026-01-01T00:02:00Z", 0.0, 0.0, 0.26),
        ("holdout", "validation", "2026-01-01T00:02:01Z", 0.2, 0.8, 0.26),
    ]
    with input_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(
            (
                "window_id",
                "split",
                "measured_at",
                "gnss_altitude_m",
                "imu_vertical_acceleration_mps2",
                "reference_wave_height_m",
            )
        )
        writer.writerows(rows)

    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(input_path),
            "--max-factor",
            "1.0",
            "--step",
            "0.1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)

    assert report["selected_factor"] == 0.4
    assert report["dataset"]["file_name"] == input_path.name
    assert report["dataset"]["sha256"] == hashlib.sha256(input_path.read_bytes()).hexdigest()
    assert report["dataset"]["quality_filter"] == {
        "accepted_good_samples": 6,
        "column_present": False,
        "excluded_invalid_samples": 0,
        "excluded_suspect_samples": 0,
    }
    assert report["search"] == {
        "candidate_count": 11,
        "max_factor": 1.0,
        "min_factor": 0.0,
        "step": 0.1,
    }
    assert report["validation_windows"] == 1
    assert report["window_coverage"]["validation"] == [
        {
            "window_id": "holdout",
            "duration_seconds": 1.0,
            "gnss_samples": 2,
            "imu_samples": 2,
            "gnss_median_interval_seconds": 1.0,
            "gnss_max_interval_seconds": 1.0,
            "imu_median_interval_seconds": 1.0,
            "imu_max_interval_seconds": 1.0,
        }
    ]
    assert report["calibration_metrics"]["rmse_m"] == 0
    assert report["calibration_baseline_metrics"]["rmse_m"] > 0
    assert report["validation_selected_metrics"]["rmse_m"] == 0
    assert report["validation_baseline_metrics"]["rmse_m"] > 0


@pytest.mark.parametrize(
    ("max_factor", "step", "candidate_count"),
    ((1.0, 0.3, 5), (1e-15, 1.0, 2)),
)
def test_wave_calibration_cli_includes_max_factor(
    tmp_path: Path, max_factor: float, step: float, candidate_count: int
) -> None:
    input_path = tmp_path / "non-divisible-search.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m\n"
        "train,calibration,2026-01-01T00:00:00Z,0.0,0.0,0.15\n"
        "train,calibration,2026-01-01T00:00:01Z,0.1,0.5,0.15\n"
        "holdout,validation,2026-01-01T00:01:00Z,0.0,0.0,0.26\n"
        "holdout,validation,2026-01-01T00:01:01Z,0.2,0.8,0.26\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(input_path),
            "--max-factor",
            str(max_factor),
            "--step",
            str(step),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    search = json.loads(result.stdout)["search"]
    assert search["candidate_count"] == candidate_count
    assert search["max_factor"] == max_factor


def test_wave_calibration_cli_rejects_candidate_count_over_limit(
    tmp_path: Path,
) -> None:
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"
    step = 10 / 100_000.5

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(tmp_path / "not-read.csv"),
            "--step",
            str(step),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "more than 100,001 factor candidates" in result.stderr
    assert "Traceback" not in result.stderr


def test_wave_calibration_cli_excludes_non_good_quality_samples(tmp_path: Path) -> None:
    input_path = tmp_path / "quality-labeled-waves.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m,quality\n"
        "train,calibration,2026-01-01T00:00:00Z,0.0,0.0,0.15,good\n"
        "train,calibration,2026-01-01T00:00:01Z,0.1,0.5,0.15,good\n"
        "train,calibration,2026-01-01T00:00:02Z,1000,1000,0.15,suspect\n"
        "holdout,validation,2026-01-01T00:01:00Z,0.0,0.0,0.26,good\n"
        "holdout,validation,2026-01-01T00:01:01Z,0.2,0.8,0.26,good\n"
        "holdout,validation,2026-01-01T00:01:02Z,1000,1000,0.26,invalid\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(input_path),
            "--max-factor",
            "1.0",
            "--step",
            "0.1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["selected_factor"] == 0.4
    assert report["window_coverage"]["calibration"][0]["gnss_samples"] == 2
    assert report["window_coverage"]["validation"][0]["imu_samples"] == 2
    assert report["dataset"]["quality_filter"] == {
        "accepted_good_samples": 4,
        "column_present": True,
        "excluded_invalid_samples": 1,
        "excluded_suspect_samples": 1,
    }


def test_wave_calibration_cli_reports_truncated_csv_without_traceback(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "truncated.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m\n"
        "window-a,calibration,2026-01-01T00:00:00Z,0.0\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [sys.executable, str(script), str(input_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Line 2: incomplete CSV row" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("header", "error"),
    (
        (
            "window_id,split,measured_at,gnss_altitude_m,"
            "imu_vertical_acceleration_mps2,reference_wave_height_m,"
            "gnss_altitude_m",
            "CSV contains duplicate columns: gnss_altitude_m",
        ),
        (
            "window_id,split,measured_at,gnss_altitude_m,"
            "imu_vertical_acceleration_mps2,reference_wave_height_m,",
            "CSV contains an empty column name",
        ),
    ),
)
def test_wave_calibration_cli_rejects_ambiguous_column_headers(
    tmp_path: Path, header: str, error: str
) -> None:
    input_path = tmp_path / "ambiguous-headers.csv"
    input_path.write_text(header + "\n", encoding="utf-8")
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [sys.executable, str(script), str(input_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert error in result.stderr
    assert "Traceback" not in result.stderr


def test_wave_calibration_cli_rejects_naive_timestamps(tmp_path: Path) -> None:
    input_path = tmp_path / "naive-timestamp.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m\n"
        "window-a,calibration,2026-01-01T00:00:00,0.0,0.0,0.15\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [sys.executable, str(script), str(input_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "timestamp must include a timezone" in result.stderr
    assert "Traceback" not in result.stderr


def test_wave_calibration_cli_rejects_duplicate_instants_in_window(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "duplicate-instants.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m\n"
        "window-a,calibration,2026-01-01T00:00:00Z,0.0,0.0,0.15\n"
        "window-a,calibration,2026-01-01T01:00:00+01:00,0.1,0.5,0.15\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [sys.executable, str(script), str(input_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "duplicate timestamp in window" in result.stderr
    assert "Traceback" not in result.stderr


def test_wave_calibration_cli_accepts_synchronized_sensor_rows(tmp_path: Path) -> None:
    input_path = tmp_path / "synchronized-sensors.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m\n"
        "train,calibration,2026-01-01T00:00:00Z,0.0,,0.15\n"
        "train,calibration,2026-01-01T00:00:00+00:00,,0.0,0.15\n"
        "train,calibration,2026-01-01T00:00:01Z,0.1,,0.15\n"
        "train,calibration,2026-01-01T00:00:01+00:00,,0.5,0.15\n"
        "train,calibration,2026-01-01T00:00:04Z,0.3,,0.15\n"
        "train,calibration,2026-01-01T00:00:04+00:00,,1.0,0.15\n"
        "holdout,validation,2026-01-01T00:01:00Z,0.0,,0.26\n"
        "holdout,validation,2026-01-01T00:01:00+00:00,,0.0,0.26\n"
        "holdout,validation,2026-01-01T00:01:01Z,0.2,,0.26\n"
        "holdout,validation,2026-01-01T00:01:01+00:00,,0.8,0.26\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [sys.executable, str(script), str(input_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["window_coverage"]["calibration"][0]["gnss_samples"] == 3
    assert report["window_coverage"]["calibration"][0]["imu_samples"] == 3
    assert report["window_coverage"]["calibration"][0]["gnss_median_interval_seconds"] == 2.0
    assert report["window_coverage"]["calibration"][0]["gnss_max_interval_seconds"] == 3.0
    assert report["window_coverage"]["calibration"][0]["imu_median_interval_seconds"] == 2.0
    assert report["window_coverage"]["calibration"][0]["imu_max_interval_seconds"] == 3.0


def test_wave_calibration_cli_rejects_timestamp_reuse_across_splits(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "overlapping-splits.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m\n"
        "train,calibration,2026-01-01T00:00:00Z,0.0,0.0,0.15\n"
        "holdout,validation,2026-01-01T00:00:00+00:00,0.1,0.5,0.15\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [sys.executable, str(script), str(input_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "timestamp is reused by window 'holdout' after 'train'" in result.stderr
    assert "Traceback" not in result.stderr


def test_wave_calibration_cli_rejects_overlapping_time_windows(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "overlapping-time-windows.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m\n"
        "train,calibration,2026-01-01T00:00:00Z,0.0,0.0,0.15\n"
        "train,calibration,2026-01-01T00:00:10Z,0.1,0.5,0.15\n"
        "holdout,validation,2026-01-01T00:00:05Z,0.0,0.0,0.15\n"
        "holdout,validation,2026-01-01T00:00:15Z,0.1,0.5,0.15\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [sys.executable, str(script), str(input_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Calibration window 'train' overlaps validation window 'holdout' in time" in result.stderr
    assert "Traceback" not in result.stderr


def test_wave_calibration_cli_rejects_disjoint_sensor_time_ranges(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "disjoint-sensors.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m\n"
        "train,calibration,2026-01-01T00:00:00Z,0.0,,0.15\n"
        "train,calibration,2026-01-01T00:00:01Z,0.1,,0.15\n"
        "train,calibration,2026-01-01T00:00:10Z,,0.0,0.15\n"
        "train,calibration,2026-01-01T00:00:11Z,,0.5,0.15\n"
        "holdout,validation,2026-01-01T00:01:00Z,0.0,0.0,0.26\n"
        "holdout,validation,2026-01-01T00:01:01Z,0.2,0.8,0.26\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [sys.executable, str(script), str(input_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Window 'train' has no overlapping GNSS and IMU sample ranges" in result.stderr
    assert "Traceback" not in result.stderr


def test_wave_calibration_cli_limits_sensor_samples_to_shared_time_range(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "shared-sensor-range.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m\n"
        "train,calibration,2026-01-01T00:00:00Z,100.0,,0.075\n"
        "train,calibration,2026-01-01T00:00:01Z,0.0,0.0,0.075\n"
        "train,calibration,2026-01-01T00:00:02Z,0.1,0.5,0.075\n"
        "holdout,validation,2026-01-01T00:01:00Z,0.0,0.0,0.26\n"
        "holdout,validation,2026-01-01T00:01:01Z,0.2,0.8,0.26\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(input_path),
            "--max-factor",
            "1.0",
            "--step",
            "0.1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["selected_factor"] == 0.1
    assert report["window_coverage"]["calibration"] == [
        {
            "window_id": "train",
            "duration_seconds": 1.0,
            "gnss_samples": 2,
            "imu_samples": 2,
            "gnss_median_interval_seconds": 1.0,
            "gnss_max_interval_seconds": 1.0,
            "imu_median_interval_seconds": 1.0,
            "imu_max_interval_seconds": 1.0,
        }
    ]


def test_wave_calibration_cli_rejects_good_rows_without_sensor_samples(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "empty-good-row.csv"
    input_path.write_text(
        "window_id,split,measured_at,gnss_altitude_m,"
        "imu_vertical_acceleration_mps2,reference_wave_height_m\n"
        "train,calibration,2026-01-01T00:00:00Z,0.0,0.0,0.15\n"
        "train,calibration,2026-01-01T00:00:01Z,0.1,0.5,0.15\n"
        "train,calibration,2026-01-01T00:00:02Z,,,0.15\n"
        "holdout,validation,2026-01-01T00:01:00Z,0.0,0.0,0.26\n"
        "holdout,validation,2026-01-01T00:01:01Z,0.2,0.8,0.26\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"

    result = subprocess.run(
        [sys.executable, str(script), str(input_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Line 4: good-quality row must contain a GNSS or IMU sample" in result.stderr
    assert "Traceback" not in result.stderr
