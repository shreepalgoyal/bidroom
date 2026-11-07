# Resident Services Portal — Digital Access Platform

**RFP reference:** NCC-2026-114
**Issued by:** Northwind City Council
**Submission deadline:** 20 November 2026, 17:00 GMT
**Clarification deadline:** 12 November 2026, 17:00 GMT
**Portal:** https://tenders.northwind.gov.uk/NCC-2026-114

## 1. Introduction

Northwind City Council serves 48,000 residents across a mix of urban and rural wards. The current resident services portal was launched in 2017, covers 34 services and is no longer supported by its vendor. Residents must use seven different systems to complete the most common transactions, and 41% of contact-centre calls are requests that could be completed online.

The Council wishes to appoint a supplier to design, build, host and support a replacement Resident Services Portal. The contract will run for five years from award, with an option to extend for a further two years.

### 1.1 Objectives

- The solution shall provide a single digital front door for all resident-facing services.
- The solution shall reduce the percentage of residents who need to call the contact centre by at least 20% within 12 months of go-live.
- The solution must be usable by residents with low digital confidence, including assisted digital journeys.
- The solution shall support at least 60,000 registered users and 2,000 concurrent sessions without degradation.
- The solution should provide translated content for the Council's three largest community languages.
- The solution must meet the Council's obligations under the Public Sector Bodies Accessibility Regulations 2018.

## 2. Scope of services

### 2.1 Functional requirements

- The solution shall provide a searchable service catalogue covering at least 120 council services.
- Residents must be able to complete the top 20 transactions end to end online, including reporting a repair, applying for a parking permit, paying council tax and requesting a bulky waste collection.
- The solution shall provide a case management workspace for council staff, with assignment, status, notes and full audit history.
- The solution must integrate with the Council's existing IDOX Uniform system for planning and environmental health records.
- The solution shall support SMS, email and in-app notifications, with a resident-controlled preference centre.
- The solution should provide an AI-assisted search that answers natural-language questions and cites the source page.
- The solution must allow residents to upload evidence and photographs of up to 25 MB per file.
- The solution shall provide a staff-facing dashboard of service demand, backlog and resident satisfaction.
- The solution must support role-based access for at least six staff roles, including contact centre, service manager and administrator.
- The solution should allow service managers to publish new forms and journeys without a code release.

### 2.2 Payments and identity requirements

- The solution shall integrate with GOV.UK Pay for card payments and support Apple Pay and Google Pay.
- The solution must support single sign-on using SAML 2.0 and OpenID Connect.
- The solution shall allow residents to authenticate using a one-time passcode sent by SMS or email.
- The solution must not store raw payment card data in any Council or supplier system.
- The solution should support delegated access so a family member or carer can act on behalf of a resident.

## 3. Technical requirements

### 3.1 Hosting and resilience

- The solution shall be hosted in the United Kingdom and all resident data must remain in the UK.
- The solution must achieve at least 99.9% availability measured monthly, excluding agreed maintenance windows.
- The supplier shall provide a disaster recovery plan with a recovery time objective of four hours and a recovery point objective of 30 minutes.
- The solution must be tested for disaster recovery at least annually and the result shared with the Council.
- The solution should scale automatically to handle a tenfold increase in traffic during a council tax deadline.
- The solution must provide a public status page and notify the Council of any severity-one incident within 30 minutes.

### 3.2 Integration and data

- The solution shall expose a documented REST API with OpenAPI 3.1 specifications for all core resources.
- The solution must support webhooks for case creation, status change and payment events.
- The solution shall provide a data migration plan for 180,000 existing resident records, including deduplication and validation.
- The solution must produce a monthly open-data extract in CSV and JSON, published under the Open Government Licence.
- The solution shall retain audit logs for seven years and make them available to the Council on request.
- The solution must support data subject access requests within one calendar month.
- The solution should provide a self-service analytics dashboard for the Council's performance team.

## 4. Security and compliance

- The supplier shall hold Cyber Essentials Plus certification for the duration of the contract.
- The supplier must hold ISO/IEC 27001 certification covering the services in scope.
- The solution shall undergo an independent penetration test before go-live and annually thereafter, and the supplier must share the remediation plan.
- The solution must encrypt data in transit using TLS 1.3 and at rest using AES-256.
- The solution shall enforce multi-factor authentication for all administrative accounts.
- The supplier must report any personal data breach to the Council within 72 hours of becoming aware.
- The supplier shall sign the Council's data processing agreement and provide a record of processing activities.
- The solution must comply with the UK GDPR, the Data Protection Act 2018 and the Public Sector Bodies Accessibility Regulations 2018.
- The solution should support Internet Protocol version 6 across all public endpoints.

## 5. Accessibility and inclusion

- The solution shall meet WCAG 2.2 Level AA across every resident-facing journey.
- The supplier must provide an accessibility conformance report (VPAT) for the current release.
- The solution shall be tested with disabled users, including screen reader and switch-access users, before go-live and annually.
- The solution must support keyboard-only navigation, visible focus states and a skip-to-content link.
- The solution shall provide content in plain English at a reading age of 9 or below for the top 20 journeys.
- The solution should provide translated content in Polish, Urdu and Romanian for the top 10 journeys.
- The solution must provide an assisted-digital route for residents who cannot complete a journey online.

## 6. Implementation and support

- The supplier shall mobilise the delivery team within six weeks of contract award.
- The supplier must provide a named delivery manager, technical lead and accessibility lead for the duration of the implementation.
- The solution shall go live within nine months of contract award.
- The supplier shall provide training for at least 150 Council staff, including train-the-trainer materials.
- The supplier must provide 24/7 support for severity-one incidents with a 30-minute response time.
- The supplier shall provide a service desk with a target resolution time of four hours for severity-two incidents.
- The supplier must provide a monthly service report covering availability, incidents, backlog and improvement actions.
- The supplier shall provide an exit plan and data export in an open format at the end of the contract.
- The supplier should provide a hypercare period of at least eight weeks after go-live.

## 7. Social value

- The supplier shall create at least two paid apprenticeships in Northwind for the duration of the contract.
- The supplier must deliver at least 30% of contract value through local suppliers or SMEs where subcontracting is used.
- The supplier shall report carbon emissions for the contract annually and set a net-zero target.
- The supplier should provide digital skills workshops for local community groups.
- The supplier must pay all staff delivering the contract at least the Real Living Wage.

## 8. Commercial requirements

- The supplier shall provide a fixed price for the implementation and a separate annual support price for five years.
- The supplier must provide a priced breakdown by workstream and resource role.
- The supplier shall hold public liability insurance of at least £10 million and professional indemnity insurance of at least £5 million.
- The supplier must accept the Council's payment terms of 30 days from a valid invoice.
- The supplier should offer a gainshare mechanism if transaction volumes exceed the forecast by more than 20%.
- The supplier shall provide three contactable references from comparable public sector organisations.

## 9. Evaluation and submission

- The supplier must submit the response through the Council's e-tendering portal by the deadline.
- The response must not exceed 40 pages excluding annexes.
- The supplier shall provide a completed pricing schedule in the required Excel template.
- The supplier must provide a signed declaration confirming no conflicts of interest.
- The supplier should provide a two-page executive summary.
- The supplier must answer every mandatory requirement with "Compliant", "Partially compliant" or "Not compliant" and provide supporting evidence.
- The supplier shall submit any clarification questions by 12 November 2026.

### 9.1 Evaluation criteria

| Criterion | Weight |
| --- | --- |
| Technical solution | 40% |
| Experience and references | 25% |
| Price | 20% |
| Social value | 15% |

## 10. Questions and clarifications

All clarification questions must be submitted through the portal. The Council will publish answers to all questions by 14 November 2026. No contact should be made with individual Council officers about this procurement.
