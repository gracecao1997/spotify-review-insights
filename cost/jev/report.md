# Jev pilot measurements and projection

Pilot: 100 / 100 completed.

| Experiment | Measured seconds | Known API USD | New enrichment calls |
|---|---:|---:|---:|
| cold | 53.951 | 0.005730 | 100 |
| warm | 0.149 | 0.000000 | 0 |

## Estimates, not executed results

| Scenario | Projected API USD | Projected one-worker hours |
|---|---:|---:|
| base_exact_cache | 4.0849 | 3.59 |
| conservative_20_percent_extra | 4.9019 | 4.30 |
| no_result_reuse | 5.2144 | 4.57 |

- Measured pilot retries are included; conservative scenario adds another 20%.
- Runtime extrapolates one worker and can vary with server load; no measured parallel speedup is claimed.
- Estimates describe the target run, excluding sunk development spend. Check the shared budget ledger before scaling.
- Unknown usage prevents a complete cost result. Local hardware/energy costs are unmeasured.
- Quality and checkpoint completion must also be checked before scaling.
