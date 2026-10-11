import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.domain.wave_calibration import WaveCalibrationWindow, select_factor


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
        [sys.executable, str(script), str(input_path), "--step", "0.1"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)

    assert report["selected_factor"] == 0.4
    assert report["validation_windows"] == 1
    assert report["window_coverage"]["validation"] == [
        {
            "window_id": "holdout",
            "duration_seconds": 1.0,
            "gnss_samples": 2,
            "imu_samples": 2,
        }
    ]
    assert report["validation_selected_metrics"]["rmse_m"] == 0
    assert report["validation_baseline_metrics"]["rmse_m"] > 0


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
