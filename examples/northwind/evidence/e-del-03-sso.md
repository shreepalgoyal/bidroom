---
id: E-DEL-03
title: SSO with SAML 2.0 and OpenID Connect
claim: The platform supports single sign-on with SAML 2.0 and OpenID Connect, and residents can authenticate with a one-time passcode by SMS or email, including just-in-time provisioning and group-to-role mapping.
tags: [integration, sso, saml, oidc, identity, authentication, one-time passcode, otp, sms]
categories: [integration]
approved: true
owner: Engineering lead
last_verified: 2026-08-30
source: harborfinch.example/platform/identity
---

We have connected to Entra ID, Okta and Google Workspace in live deployments. Residents can authenticate with a one-time passcode by SMS or email when the Council does not operate a resident identity provider. Session lifetime and step-up authentication are configurable per role.
