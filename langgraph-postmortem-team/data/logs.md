# Service logs: Marlin checkout, 2026-03-14 (UTC)

## 13:58 checkout-api config reload
checkout-api pods (12 replicas) reloaded config revision cfg-2291. Line: `db.pool_max=4 (was 40)`. Each pod now holds at most 4 database connections. Reload finished at 13:59 on all 12 pods without errors.

## 14:03 connection wait timeouts begin
checkout-api: `WARN pool exhausted, waited 2000ms for connection` first appears at 14:03:12 on 9 of 12 pods. p95 latency for POST /checkout climbs from 310 ms to 2.4 s within two minutes. Error rate is still under 1%.

## 14:05 error rate crosses alert threshold
POST /checkout returns HTTP 503 for 18% of requests at 14:05. The log line `ERR upstream payments-gw timeout after 3000ms` appears in about a third of failures, because requests holding a payments call also wait on the database pool before commit.

## 14:15 request volume doubles
Inbound POST /checkout rate rises from 410 req/s to 880 req/s although user traffic is flat. 71% of the extra requests carry header `x-client-retry: 1..5` and come from mobile app build 8.4.0, with retries sent back to back with no delay.

## 14:24 rollback job fails its canary gate
deploy-bot: `rollback cfg-2291 -> cfg-2288 aborted: canary health check failed (error rate 22% > 2%)`. The canary pod runs the same bad pool setting, so the gate that protects rollbacks blocked the rollback itself.

## 14:41 manual override applied
deploy-bot: `rollback cfg-2291 -> cfg-2288 forced by priya.n with --skip-canary`. Pods reload cfg-2288 between 14:41 and 14:43; `db.pool_max=40` is restored on all 12 pods.

## 14:52 recovery
POST /checkout error rate falls below 1% at 14:49 and p95 latency returns to 330 ms at 14:52. Request rate normalises to 420 req/s by 14:55 as retries drain. Incident closed at 14:52.
