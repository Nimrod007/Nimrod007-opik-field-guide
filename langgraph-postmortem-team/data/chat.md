# Incident channel #inc-checkout-0314 (excerpts, UTC)

## 14:06 page acknowledged
priya.n (on-call): ack. Checkout 503s at 18%. Starting with the payments gateway, the logs are full of payments-gw timeouts. Pinging the payments team.

## 14:11 payments provider ruled out
dmitri.k (payments): gateway is healthy on our side, p95 is 180 ms, and the provider status page is green. Those timeouts are probably symptoms, not the cause. About 5 minutes were spent on this.

## 14:17 retries noticed
lena.o (mobile): the traffic jump is our fault in part. App 8.4.0 shipped on 3/12 with the new retry helper and no backoff. I can ask for a server-side kill switch but nobody has the flag name handy.

## 14:22 connection pool suspected
tomas.b (platform): checkout-api pods show 4/4 connections in use on every pod. That looks like the pool setting changed. Checking recent config revisions. Who touched cfg-2291?

## 14:26 rollback blocked
priya.n: tried rolling back cfg-2291, the canary gate fails because the canary has the same bad pool setting. Do we have an override? Asked in #platform and waiting for someone with deploy-admin rights.

## 14:39 override approved
tomas.b: I have admin. Approving the skip-canary rollback now. Priya, run it with the flag. Note for the review: the runbook never mentions the override and it took 13 minutes to find who could approve it.

## 14:53 all clear
priya.n: error rate flat, latency normal. Declaring recovered at 14:52. Follow-ups: pool config validation, retry backoff in the app, alert threshold review, runbook for forced rollbacks.
