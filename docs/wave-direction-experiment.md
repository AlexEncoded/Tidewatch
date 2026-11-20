# GNSS directional-wave experiment

Tidewatch contains an offline prototype in
`apps/api/app/domain/wave_direction_experiment.py`. It uses synchronized
surface elevation (`eta`) and east/north GNSS velocity (`u`, `v`) samples,
Welch averaged spectra, and first directional moments across resolvable bins
in a selected frequency band. It reports the mean compass bearing **towards**
which waves travel at the elevation spectral peak and diagnostic per-frequency
directions; it does not claim to find the peak of a full spreading distribution.

The prototype rejects irregular sample cadence, non-finite values, invalid
frequency bands, and records too short for multiple spectral segments. It does
not interpolate gaps, estimate a full directional spreading spectrum, or
publish a result through the API. Callers must screen sensor quality before
passing samples. Its concentration value measures the length of the first
directional moment; the 0.1 cutoff is a screening heuristic, not a calibrated
quality threshold, and a weak value suppresses the angle. It removes a
least-squares linear trend from each Welch segment before spectral analysis;
this reduces slow drift sensitivity but is not a complete GNSS-drift correction.

The underlying `eta/u/v` approach derives directional moments from auto- and
cross-spectra of elevation and horizontal velocities. See the GNSS buoy method
in [Lin et al. (2017), Appendix B](https://pmc.ncbi.nlm.nih.gov/articles/PMC5298745/).
That paper's field comparison is evidence for a particular receiver and setup,
not for Tidewatch hardware. NDBC's established directional buoy procedures use
earth-referenced motion and cross-spectra as well, with pitch, roll, and azimuth
measurements ([NDBC analysis procedures](https://www.ndbc.noaa.gov/wavemeas.pdf)).

Current tests use deterministic synthetic plane waves and a two-frequency
mixed sea to verify compass conversion, peak-frequency selection, linear-drift
detrending, rejection of missing horizontal energy, and cadence/frequency
guards. This is an algorithm check only. It does not assess directional
spreading when multiple headings share a frequency. Before
operational use, Tidewatch still needs Doppler-derived velocity quality and
cadence documentation, representative records, comparison with an independent
directional reference buoy, and tests for mixed seas, drift, gaps, and
directional spreading. The API continues to expose height and period only.

## Offline CSV evaluation

Use the [CSV template](wave-direction-template.csv) with one row per
synchronized sample. `reference_direction_towards_degrees` must be an
independent reference bearing in compass degrees clockwise from true north.
Each `window_id` has one constant reference bearing and one split (`calibration`
or `validation`); windows may not overlap in time. Mark rejected samples as
`suspect` or `invalid`. The evaluator excludes those rows and does not fill the
resulting gaps. `hdop` and `satellites` are optional diagnostic columns; choose
receiver-specific filters with `--maximum-hdop` or `--minimum-satellites`.
When a filter is requested, its column is required and rows with missing values
are excluded. The report records each exclusion count and the selected limits.

Run it with an explicit frequency band chosen for the sampling protocol:

```bash
python scripts/evaluate-wave-direction.py data/labeled-directions.csv \
  --minimum-frequency-hz 0.05 --maximum-frequency-hz 0.4 \
  --minimum-window-duration-seconds 512 --segment-length 128 \
  --maximum-hdop 2.0 --minimum-satellites 8
```

The JSON report records the input SHA-256, quality counts, per-window sample
cadence, HDOP and satellite availability and summaries (median, maximum HDOP,
and minimum satellite count), estimates, withheld angles, and circular angular
error metrics for each split, including the effective Welch segment length and
count. Each estimate also includes resolved frequency bins with relative
elevation energy and a first-moment direction and concentration where available;
this is diagnostic and does not reconstruct a directional distribution.
Metadata summaries describe accepted good-quality samples, including
accepted samples when no GNSS threshold was configured. Calibration and
validation are report-only groups; no parameter is selected or fitted. The tool
requires uniform good-sample cadence and multiple overlapping Welch segments.
The minimum window duration is mandatory and must be chosen for the receiver,
sea-state protocol, and reference instrument; the example value is illustrative,
not a universal scientific threshold.
Mean signed error is calculated circularly and is omitted when its direction is
undefined because errors cancel around the circle.
HDOP and satellite thresholds must be justified for the receiver and deployment;
the example values are illustrative, not quality standards.
Synthetic values can check code behavior but must not be treated as calibration
or field validation evidence.

## Field-validation checklist

This is a campaign-planning checklist, not a validated acquisition standard.
GNSS buoy studies have compared measurements against independent wave
instrumentation, while operational directional-buoy procedures also track
motion and heading quality ([GPS buoy field study](https://doi.org/10.1175/JTECH-D-11-00128.1),
[NDBC analysis procedures](https://www.ndbc.noaa.gov/wavemeas.pdf)). Those results
do not establish acceptance limits for Tidewatch hardware.

Before collecting a validation dataset, record:

1. **Instrument configuration:** buoy and receiver model, antenna placement,
   firmware, GNSS processing mode, IMU model and calibration, coordinate frame,
   sensor offsets, and whether horizontal velocity is Doppler-derived or
   calculated from positions. Keep the native receiver and IMU files.
2. **Time and sampling:** UTC clock source, measured clock offset between
   streams, sample rates, observed cadence, dropped-sample indicators, and the
   procedure used to synchronize GNSS, IMU, and reference records. Do not hide
   gaps by interpolation for this evaluator.
3. **Independent reference:** use a directional wave instrument with its own
   documented heading convention and quality flags. Record its location,
   separation from the test buoy, water depth, and time alignment; report these
   because they affect how representative a comparison can be.
4. **Predeclared analysis:** choose the frequency band, minimum window duration,
   Welch segment length, GNSS quality limits, and acceptable circular angular
   error before evaluating the held-out windows. These values must come from
   the receiver and campaign protocol; this document sets no universal values.
5. **Separate windows:** assign complete, non-overlapping time windows to
   calibration or validation before inspecting their errors. Preserve the raw
   records, labels, quality decisions, evaluator command, and report hash for
   reproducibility.
6. **Review results by conditions:** report circular error, withheld estimates,
   sample coverage, and reference/instrument quality by sea state and deployment.
   A good aggregate score must not conceal a condition where the estimate is
   unreliable.

Treat the result as exploratory until the selected reference, hardware setup,
and acceptance criteria have been reviewed for the intended deployment.
