---
id: E-DEL-02
title: GOV.UK Pay integration
claim: We integrate with GOV.UK Pay for card payments, support Apple Pay and Google Pay, and never store raw card data in our systems.
tags: [integration, payments, gov.uk pay, apple pay, google pay, pci]
categories: [integration]
approved: true
owner: Engineering lead
last_verified: 2026-08-30
source: harborfinch.example/platform/payments
---

The browser is redirected to GOV.UK Pay's hosted payment page, so card data never touches our infrastructure. Payment events arrive by signed webhook and reconcile to the case record. Refunds and partial refunds are supported from the staff workspace.
