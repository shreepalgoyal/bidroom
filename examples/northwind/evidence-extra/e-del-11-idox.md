---
id: E-DEL-11
title: IDOX Uniform integration for planning and environmental health
claim: A certified integration with the Council's existing IDOX Uniform system keeps planning applications and environmental health records in sync, bi-directionally, without manual re-keying.
tags: [integration, idox, idox uniform, planning, environmental health, records, api]
categories: [integration]
approved: false
owner: Integration lead
last_verified: 2026-10-25
source: trust.harborfinch.example/integrations/idox-uniform
---

The integration uses IDOX's supported API, not screen-scraping. A planning application submitted through the portal creates a case in Uniform within 30 seconds and status changes flow back to the resident's account. Environmental health records follow the same pattern. The connector is live at two councils, handles retries and dead-letter queues, and is covered by the integration test pack in the annex.
