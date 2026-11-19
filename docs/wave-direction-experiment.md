# GNSS directional-wave experiment

Tidewatch contains an offline prototype in
`apps/api/app/domain/wave_direction_experiment.py`. It uses synchronized
surface elevation (`eta`) and east/north GNSS velocity (`u`, `v`) samples,
Welch averaged spectra, and the first directional moment at the elevation
spectral peak. It reports a mean compass bearing **towards** which waves travel
at that frequency; it does not claim to find the peak of a full spreading
distribution.

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
resulting gaps.

Run it with an explicit frequency band chosen for the sampling protocol:

```bash
python scripts/evaluate-wave-direction.py data/labeled-directions.csv \
  --minimum-frequency-hz 0.05 --maximum-frequency-hz 0.4 \
  --minimum-window-duration-seconds 512 --segment-length 128
```

The JSON report records the input SHA-256, quality counts, per-window sample
cadence, estimates, withheld angles, and circular angular error metrics for each
split, including the effective Welch segment length and count. Calibration and
validation are report-only groups; no parameter is selected or fitted. The tool
requires uniform good-sample cadence and multiple overlapping Welch segments.
The minimum window duration is mandatory and must be chosen for the receiver,
sea-state protocol, and reference instrument; the example value is illustrative,
not a universal scientific threshold.
Mean signed error is calculated circularly and is omitted when its direction is
undefined because errors cancel around the circle.
Synthetic values can check code behavior but must not be treated as calibration
or field validation evidence.
