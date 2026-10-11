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
        ("train-a", "calibration", 0.0, 0.0, 0.15),
        ("train-a", "calibration", 0.1, 0.5, 0.15),
        ("train-b", "calibration", 0.0, 0.0, 0.35),
        ("train-b", "calibration", 0.3, 1.0, 0.35),
        ("holdout", "validation", 0.0, 0.0, 0.26),
        ("holdout", "validation", 0.2, 0.8, 0.26),
    ]
    with input_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(
            (
                "window_id",
                "split",
                "gnss_altitude_m",
                "imu_vertical_acceleration_mps2",
                "reference_wave_height_m",
            )
        )
        writer.writerows(rows)

    script = Path(__file__).resolve().parents[3] / "scripts" / "evaluate-wave-calibration.py"
    result = subprocess.run(
        [sys.executable, str(script), str(input_path), "--step", "0.1"],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)

    assert report["selected_factor"] == 0.4
    assert report["validation_windows"] == 1
    assert report["validation_selected_metrics"]["rmse_m"] == 0
    assert report["validation_baseline_metrics"]["rmse_m"] > 0
