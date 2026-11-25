# Telecom change validation

Compare synthetic LTE site KPIs across a planned change. This tool reports a lab recommendation and performs no network or rollback actions.

```sh
python3 validate.py examples/before.csv examples/rollback.csv examples/policy.json
```

Swap `rollback.csv` for `pass.csv` or `review.csv` to reproduce the other outcomes. Compare against [pass](examples/pass.json), [review](examples/review.json), or [rollback](examples/rollback.json).

Each CSV row contains a unique site ID, window duration in minutes, attach attempts, successful attaches, and median successful attach latency in milliseconds. Before and after files identify their respective windows. Compare equivalent durations and use the same latency definition. Latency is shown for context. The policy specifies a minimum count per site per window and a rollback threshold in percentage points. A missing site, mismatched duration, or insufficient count requires review. Among comparable sites, a drop at or above the threshold recommends rollback. The most severe site controls the recommendation. Aggregate rates use summed counts, and are descriptive even when a site requires review.

## Sample change record

**LAB-017** covers SITE-01 through SITE-03 in two 30-minute windows. Compare [before](examples/before.csv) and [after](examples/rollback.csv) under the [lab thresholds](examples/policy.json).

SITE-03 fell from 198/200 (99%) to 182/200 (91%), crossing the 5-point threshold despite the combined rate rising from 98.05% to 98.62%. Separate SITE-03 for investigation and compare the attach failure stages with the pre-change sample. After the lab correction, collect another comparable window with at least 100 attempts on each site and repeat the same checks before proceeding.
