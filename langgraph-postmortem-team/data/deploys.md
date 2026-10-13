# Deploy and config history, Marlin platform, 2026-03-10 to 2026-03-14

## 2026-03-12 mobile app 8.4.0 release
Mobile app 8.4.0 rolled out to 100% of users on 3/12. Release note: "More resilient checkout: failed requests are retried up to 5 times." Reviewed by lena.o, approved by the mobile lead. The retry helper has no backoff or jitter and no server-side kill switch.

## 2026-03-13 cfg-2288 payments timeouts
Config revision cfg-2288 (last known good) set `db.pool_max=40` and `payments.timeout_ms=3000`. Applied 3/13 at 16:20 with no incidents.

## 2026-03-14 cfg-2291 database pool tuning
Config revision cfg-2291 applied at 13:58 by deploy-bot, authored by sam.r. Change description: "tune DB pool for cost: pool_max 40 -> 4 per pod, pool_min 4 -> 1". The PR title says "per pod" but sam.r's intent in the PR thread was "4 per node group", expecting the value to be spread across 12 pods. No schema validation existed for pool_max. One approval, from a reviewer who did not run it in staging.

## 2026-03-14 rollback gate policy
The rollback pipeline requires a passing canary health check before reverting any config revision. Policy added 2025-11 after a bad rollback. There is no documented bypass. The `--skip-canary` flag exists in deploy-bot but requires a deploy-admin approval; three people hold the role, none on call that afternoon.

## 2026-03-14 alert configuration
Alert CheckoutErrorRate pages when the 5xx rate exceeds 5% over a 5-minute window. Latency alerts for POST /checkout page only above p95 5 s. Config cfg-2291 applied at 13:58, first user-visible degradation at 14:03, page fired at 14:05:40.

## 2026-03-14 recent change freeze status
No change freeze was active. Two other deploys landed on 3/14 before noon: search-api 4.12.1 and a docs site update. Neither touches checkout or its database.
