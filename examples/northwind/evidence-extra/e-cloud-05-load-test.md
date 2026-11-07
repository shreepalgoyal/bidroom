---
id: E-CLOUD-05
title: Load tested at 60,000 registered users and 2,000 concurrent sessions
claim: The platform is load tested at 60,000 registered users and 2,000 concurrent sessions with no degradation, and autoscales to a tenfold traffic spike within four minutes.
tags: [hosting, load test, concurrent sessions, 60000 users, 2000 concurrent, autoscaling, performance]
categories: [hosting]
approved: false
owner: Platform lead
last_verified: 2026-10-27
source: trust.harborfinch.example/performance/load-test-2026
---

The October 2026 test ran against the production topology for four hours at 2,000 concurrent sessions. Median response stayed under 280 ms and the 99th percentile under 900 ms, with no errors. A separate spike test drove ten times the normal council-tax deadline traffic; the autoscaler added capacity in four minutes and the service stayed within its latency target. Full JMeter plans and Grafana captures are in the performance annex.
