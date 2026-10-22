# Offline wave-estimator evaluation

The GNSS/IMU wave-height estimate is experimental and its default IMU factor is
not a field calibration. This tool evaluates candidate factors against an
independent wave-height reference; it does not update API configuration or
change production behavior.

The live estimate combines GNSS and IMU samples only within the time interval
covered by both streams. If their windows do not overlap, the API reports
insufficient data instead of combining unrelated sensor ranges.

Prepare a CSV with one row per synchronized sensor sample and these columns:

| Column | Meaning |
|---|---|
| `window_id` | Identifier shared by samples from one evaluation window |
| `split` | `calibration` or `validation`; keep validation windows out of tuning |
| `measured_at` | ISO 8601 sample time with an explicit UTC offset or `Z` |
| `gnss_altitude_m` | GNSS altitude in meters |
| `imu_vertical_acceleration_mps2` | Vertical acceleration in m/s² |
| `reference_wave_height_m` | Independently measured wave height in meters for the window |
| `quality` (optional) | `good`, `suspect` or `invalid`; only `good` samples are evaluated |

The reference value must remain constant within each window. Each window needs
at least two GNSS and two IMU samples inside the time range shared by both
modalities. Empty sensor cells are allowed when the other samples in that
window satisfy this minimum. The evaluator excludes samples outside the shared
GNSS/IMU time range and reports coverage for the retained interval. Use
synchronized timestamps on every row; timestamps must include a timezone and
cannot repeat anywhere in the CSV. Calibration and validation window time
ranges must also not overlap, even when their sample timestamps differ. This
prevents temporal leakage between calibration and validation. Keep the GNSS and
IMU values from the same instant on the same row (an unavailable modality may be
blank). Use a documented,
independently measured reference source; do not use simulator output as
calibration evidence. If the optional `quality` column is omitted, all rows are
treated as `good` for backward compatibility; the JSON report records whether
quality filtering was available and how many rows were excluded.

Run the evaluator from the repository root:

```bash
python scripts/evaluate-wave-calibration.py data/labeled-waves.csv
```

It selects the factor with the lowest RMSE on `calibration` windows, then
reports MAE, RMSE and signed bias for both the baseline and selected factor on
the untouched `validation` windows. The JSON report also lists each window's
sample counts by sensor and elapsed duration. Since the estimator uses a range
over each window, compare results only across windows with durations appropriate
to the same measurement protocol; investigate large duration differences
before interpreting the error metrics. It includes the input file's SHA-256 and
the factor-search bounds and step so the results can be traced back to their
exact data and settings. The default search spans 0–10 in increments of 0.01.
To change the search resolution or baseline:

```bash
python scripts/evaluate-wave-calibration.py data/labeled-waves.csv \
  --baseline-factor 0.1 --max-factor 5 --step 0.005
```

Keep the source data, sensor synchronization method, window definition and
reference instrument uncertainty with any evaluation report. A lower validation
error is evidence only for that dataset and setup; domain review is still
required before considering a buoy-specific factor.
