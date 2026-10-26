---
title: "Platform Constructs"
description: "The reusable, domain-neutral building blocks under the Open Logistics Specs: conventions, identity, integrations, events, jobs, documents, billing and shared objects."
---

The Open Logistics Specs are built from two layers:

- **Platform Constructs** (this tab) are concepts that any multi-tenant API platform needs, whatever its domain: how requests, IDs, errors and versions work; who the tenants and users are; how providers are integrated; how events, jobs, documents and money flow. Nothing here is specific to shipping.
- **Specification** (the first tab) defines the logistics domain on top of them: shipments, rates, tracking, customs, networks, fleets, inventory and the parties involved.

Keeping the layers apart keeps the logistics chapters focused, and makes the constructs reusable by any domain that adopts the same conventions.

| Construct | What it provides | Chapter |
|---|---|---|
| Conventions | Transport, versioning, authentication (API keys, OAuth 2.1, OIDC), IDs, common fields, money and units, idempotency, errors, pagination, expansion, rate limits, test mode, security, the two interfaces | [00](/spec/00-conventions) |
| Shared objects | Money, measurements, contact and address, recurrence, area, messages, metadata, files and documents | [Shared objects](/platform/shared-objects) |
| Object management | Uniform list, search, retrieve, update, delete, batches, exports and retention | [10](/spec/10-object-management) |
| Conformance and discovery | Modules, capabilities, `/.well-known` configuration, the conformance suite, agent and MCP integration | [11](/spec/11-conformance) |
| Accounts and identity | Tenants, platforms and children, memberships, roles, API keys, SSO through any OIDC provider, token exchange | [19](/spec/19-accounts) |
| Integrations and interfaces | A generic OAuth app and connection wrapper with typed provider interfaces, federated onboarding | [26](/spec/26-integrations) |
| Webhooks and events | Signed at-least-once events, the event catalog, redelivery, inbound injection | [08](/spec/08-webhooks) |
| Background jobs | One envelope for all asynchronous work, progress, cancel, retry, logs, recurring job schedules | [27](/spec/27-jobs) |
| Documents | Portable templates, generation (on demand, triggered, batch), ingestion of PDFs, scans and EDI | [25](/spec/25-documents-generation) |
| Billing and payments | Invoices with import, export and reconciliation, usage metering, price plans, balances, a provider-neutral payments interface | [28](/spec/28-billing) |
| Interfaces | The REST Interface for integrators, and the GraphQL Interface for internal CRUD and back-office operations | [Conventions §16](/spec/00-conventions), [GraphQL Interface](/spec/graphql) |

Some constructs have logistics extensions, which stay in the logistics chapters. Examples: carrier label specs and certification (chapter 25 §6), carrier invoice audit (chapter 28 §2), and the `lsp` integration interface (chapter 26 §3).
