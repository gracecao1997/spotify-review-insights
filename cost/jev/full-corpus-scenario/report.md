# Jev pilot measurements and projection

Pilot: 100 / 100 completed.

| Experiment | Measured seconds | Known API USD | New enrichment calls |
|---|---:|---:|---:|
| cold | 53.951 | 0.005730 | 100 |
| warm | 0.149 | 0.000000 | 0 |

## Estimates, not executed results

| Scenario | Projected API USD | Projected one-worker hours |
|---|---:|---:|
| base_exact_cache | 25.3485 | 22.21 |
| conservative_20_percent_extra | 30.4182 | 26.64 |
| no_result_reuse | 34.4466 | 30.16 |

## Measured per-stage usage

| Stage | Calls | Input tokens | Output tokens | Known API USD |
|---|---:|---:|---:|---:|
| enrich | 100 | 122787 | 21250 | 0.005157054 |
| verify | 10 | 13645 | 2122 | 0.000573090 |
| group | 1 | 1780 | 113 | 0.000000000 |
| memo | 1 | 2154 | 318 | 0.000000000 |

Cost per 1,000 inputs: $0.057301440; per completed record: $0.000057301; throughput: 1.8535 records/second.

## Editable planning controls
{
  "budget_usd": 10,
  "reserve_margin_usd": 1,
  "dispatch_limit_usd": 9,
  "max_workers": 2,
  "local_output_token_cap": 2200,
  "jev_output_cap": "fixed response schema; not a generative-token setting",
  "fallback_fraction": 0,
  "fallback_unit_usd": null,
  "fallback_unit_seconds": null,
  "scope": "Calculator planning controls; does not mutate execution settings. Actual paid run uses ledger and saved experiment controls."
}

Scenario budget warnings: {"base_exact_cache": true, "conservative_20_percent_extra": true, "no_result_reuse": true}

- Worker/output settings describe scenario limits; no measured speedup or token-saving claim is made. Paid fallback is disabled in the executed pipeline.
- Measured pilot retries are included; conservative scenario adds another 20%.
- Runtime extrapolates one worker and can vary with server load; no measured parallel speedup is claimed.
- Estimates describe the target run, excluding sunk development spend. Check the shared budget ledger before scaling.
- Unknown usage prevents a complete cost result. Local hardware/energy costs are unmeasured.
- Quality and checkpoint completion must also be checked before scaling.
