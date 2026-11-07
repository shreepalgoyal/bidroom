---
id: E-SEC-05
title: Multi-factor authentication for administrators
claim: Every administrative account requires phishing-resistant multi-factor authentication, and standing access is removed after four hours.
tags: [security, mfa, multi-factor, administrative, access control]
categories: [security]
approved: true
owner: Security lead
last_verified: 2026-09-01
source: trust.harborfinch.example/access-control
---

Administrators enrol a FIDO2 security key or platform passkey. SMS fallback is not permitted for administrative roles. Access is granted through just-in-time elevation with a ticket reference, and all sessions are recorded in the audit log.
