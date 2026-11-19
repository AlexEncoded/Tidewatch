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
quality threshold, and a weak value suppresses the angle.

The underlying `eta/u/v` approach derives directional moments from auto- and
cross-spectra of elevation and horizontal velocities. See the GNSS buoy method
in [Lin et al. (2017), Appendix B](https://pmc.ncbi.nlm.nih.gov/articles/PMC5298745/).
That paper's field comparison is evidence for a particular receiver and setup,
not for Tidewatch hardware. NDBC's established directional buoy procedures use
earth-referenced motion and cross-spectra as well, with pitch, roll, and azimuth
measurements ([NDBC analysis procedures](https://www.ndbc.noaa.gov/wavemeas.pdf)).

Current tests use deterministic synthetic plane waves to verify the compass
conversion, peak-frequency selection, rejection of missing horizontal energy,
and cadence/frequency guards. This is an algorithm check only. Before
operational use, Tidewatch still needs Doppler-derived velocity quality and
cadence documentation, representative records, comparison with an independent
directional reference buoy, and tests for mixed seas, drift, gaps, and
directional spreading. The API continues to expose height and period only.
