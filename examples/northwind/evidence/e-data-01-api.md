---
id: E-DATA-01
title: OpenAPI 3.1 REST API and webhooks
claim: Every core resource is available through a documented REST API with OpenAPI 3.1, and signed webhooks cover case, status and payment events.
tags: [integration, api, openapi, rest, webhooks]
categories: [integration]
approved: true
owner: Engineering lead
last_verified: 2026-09-08
source: developer.harborfinch.example
---

The API uses OAuth 2.0 client credentials for service-to-service access and scoped tokens for staff tools. Webhooks are signed with HMAC-SHA256, retried with exponential backoff and replayable for seven days. The specification is published as a versioned OpenAPI document.
