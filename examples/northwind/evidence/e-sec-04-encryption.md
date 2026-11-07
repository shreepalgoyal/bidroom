---
id: E-SEC-04
title: Encryption in transit and at rest
claim: All resident data is encrypted in transit with TLS 1.3 and at rest with AES-256, with keys managed in AWS KMS.
tags: [security, encryption, tls, aes-256, kms]
categories: [security]
approved: true
owner: Security lead
last_verified: 2026-09-01
source: trust.harborfinch.example/encryption
---

TLS 1.2 is disabled on public endpoints. Internal service-to-service traffic uses mutual TLS. Database, object storage and backup volumes are encrypted with customer-managed KMS keys, rotated annually. Key access is logged and restricted to the platform break-glass role.
