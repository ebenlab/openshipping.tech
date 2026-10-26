# Open Logistics Specification

**Status:** Draft 0.1 · 2026-10-06
**Editor:** Daniel Kobina (Eben Labs)
**Home:** shippinginternals.dev (forthcoming)

This is an open specification for a universal, multi-carrier shipping API. It defines one resource model and one wire format for live rates, labels, pickups, manifests, customs documents, tracking, webhooks, and carrier connections. Any party can implement it, in one or more **modes** (chapter 12) that share one object model:

- **Universal**: aggregators (Karrio-style) implement it in front of many carriers.
- **Carrier**: carriers (DHL- or UPS-style) implement it as their own public API, with trade, catalog, pricing and routes.
- **3PL**: logistics providers implement it over their own routes plus subcontracted carriers.
- **Network**: carrier and LSP networks host carrier accounts next to merchant accounts, and compose journeys across members.
- **Fleet**: operators implement it over their own vehicles: vans, aircraft, drones, vessels.
- **Data Network**: data nodes keep a shared, signed, access-controlled record of every party's objects.

Platforms (marketplaces, WMS, OMS) consume it once and reach every implementer, whatever its mode.

The API design follows Stripe's API conventions on purpose: prefixed IDs, form-free JSON, `Idempotency-Key`, cursor pagination, `expand[]`, metadata, dated versions, test and live keys, signed webhook events. These are the conventions engineers already trust, so we reuse them rather than invent our own.

The spec has two audiences, in the same way `auth.md` does:

| Audience | Start here |
|---|---|
| **Agents** (LLM agents, MCP clients, autonomous integrators) | [`shipping.md`](shipping.md): the discovery file an implementer hosts at `https://{domain}/shipping.md` |
| **Developers** (people implementing or consuming the API) | The chapters below, then [`openapi.yaml`](openapi.yaml) |

## Two layers and two interfaces

- **Specification**: the logistics domain (shipments, rates, tracking, customs, networks, fleets, inventory and the parties involved).
- **Platform Constructs** ([platform/index.md](platform/index.md)): domain-neutral building blocks (conventions, shared objects, identity, integrations, events, jobs, documents, billing), reusable by any domain.
- **REST Interface** (`/v1`): public workflows for integrators.
- **GraphQL Interface** (GraphQL, `/graphql`): internal CRUD over every domain object, plus back-office operations.

## Chapters

| # | Chapter | Covers |
|---|---|---|
| — | [Architecture](spec/architecture.md) | System context, implementer reference architecture, object model, end-to-end lifecycle |
| 00 | [Conventions](spec/00-conventions.md) | Auth, versioning, IDs, errors, idempotency, pagination, expansion, metadata namespaces (user, carrier, system), test mode, units, money |
| 01 | [Core objects](spec/01-core-objects.md) | Contact, Address, Parcel, Item, Order, Customs Declaration, Carrier Configs, Service, Charge, Document, Recurrence, Area |
| 02 | [Live Rates](spec/02-rates.md) | `POST /v1/rates`, rate quotes, partial failure, expiry |
| 03 | [Shipments & Labels](spec/03-shipments.md) | Buy a label, void a label, returns, multi-piece |
| 04 | [Pickups](spec/04-pickups.md) | Availability, book, reschedule, cancel, recurring pickup schedules |
| 05 | [Manifests & End of Day](spec/05-manifests.md) | Previews, explicit and close-all manifests, close groups, async submission, scheduled auto-close, reprints |
| 06 | [Customs Documents](spec/06-documents.md) | Files, paperless trade uploads, pre-shipment and post-shipment |
| 07 | [Tracking](spec/07-tracking.md) | Trackers, canonical statuses, events, discard |
| 08 | [Webhooks & Events](spec/08-webhooks.md) | Endpoints CRUD, event catalog, signatures, delivery, inbound injection |
| 09 | [Carriers, Connections & Apps](spec/09-connections.md) | Carrier catalog, dynamic config schemas, OAuth/OIDC carrier apps, connect sessions |
| 10 | [Object Management](spec/10-object-management.md) | List, search, retrieve, update, delete semantics across every object |
| 11 | [Conformance](spec/11-conformance.md) | Modules, capability registry, `/.well-known/shipping-configuration` |
| 12 | [Modes](spec/12-modes.md) | Universal, Carrier, 3PL and Fleet profiles over shared modules |
| 13 | [Trade Engine](spec/13-trade.md) | Classification, compliance screening, landed cost, tariffs, duty collections |
| 14 | [Service Catalog](spec/14-catalog.md) | Services, options, packagings, zones, and serviceability |
| 15 | [Rate Sheets & Pricing](spec/15-pricing.md) | Rate sheets, surcharges, fuel schedules, pricing rules, simulate, import and export |
| 16 | [Routes](spec/16-routes.md) | Facilities, routes, stops and legs, route runs, journeys |
| 17 | [Fleet](spec/17-fleet.md) | Vehicles, drivers, optimization, positions and ETAs |
| 18 | [Shipment Injection](spec/18-injection.md) | Shipments injected by upstream carriers and e-commerce platforms, ASNs, receiving, tracking feedback |
| 19 | [Merchants & Identity](spec/19-accounts.md) | Accounts, memberships, roles, API keys, OIDC/SSO identity providers, token exchange |
| 20 | [Products](spec/20-products.md) | Product and commodity master: CRUD, variants, per-country HS codes, upsert sync |
| 21 | [Carrier & LSP Networks](spec/21-network.md) | Carrier member accounts, composed rates across members, interline agreements, settlement |
| 22 | [IoT & Devices](spec/22-iot.md) | Devices, scan, sensor, position and geofence ingestion, condition monitoring |
| 23 | [Logistics Data Network](spec/23-data-network.md) | Participants (DIDs), signed and anchored records, field-level access, end-to-end timelines from distributed scans with consolidated milestones, attestations, erasure |
| 24 | [Consolidation & Transport Units](spec/24-consolidation.md) | Bags, gaylords, pallets, ULDs, containers, trailers, and conveyances (flights, voyages, trips) with aggregation |
| 25 | [Documents: Templates, Generation & Ingestion](spec/25-documents-generation.md) | Liquid and ZPL templates, carrier label specs and certification, on-demand, triggered and batch generation, ingestion of PDFs, scans and EDI into structured objects |
| 26 | [Integrations & Interfaces](spec/26-integrations.md) | Generic OAuth apps and connections, interfaces `lsp` (carriers, 3PL injection), `address_validation`, `insurance` |
| 27 | [Background Jobs](spec/27-jobs.md) | One job envelope for every async operation, cancel, retry, logs, stream, recurring job schedules |
| 28 | [Billing & Payments](spec/28-billing.md) | Carrier and LSP invoices (EDI 210, INVOIC, UBL, CSV), reconciliation, usage meters and price plans, prepaid balances, payments interface |
| 29 | [Inventory & Fulfillment](spec/29-inventory.md) | Storage locations, lot and serial-aware stock, movement ledger, levels, fulfillment orders, waves, counts, channel sync |
| A | [Appendix: Design rationale](spec/A-rationale.md) | Why each decision was made, and what we borrowed from Karrio, Amazon Shipping, cross-border carrier practice and Stripe |
| B | [Appendix: Standards mapping](spec/B-standards.md) | GS1 (SSCC, GTIN, EPCIS 2.0), IATA ONE Record, DCSA, UPU, ISO 6346, UN/LOCODE, WCO, W3C DID and VC |
| C | [Appendix: Glossary](spec/C-glossary.md) | Every term with its definition, the names used across the industry, and where the spec defines it, plus an alias index. Generated by `tools/build_glossary.py`. |

## REST endpoint index

Generated from `openapi.yaml`. Back-office operations are on the GraphQL surface. See [spec/graphql.md](spec/graphql.md) and [graphql/schema.graphql](graphql/schema.graphql).

```
Rates
  POST   /v1/rates                                            Get live rates
  GET    /v1/rate_quotes/{id}                                 Retrieve a rate quote

Shipments
  GET    /v1/shipments                                        List shipments
  POST   /v1/shipments                                        Create a shipment (draft, or purchase with `purchase: true`)
  GET    /v1/shipments/search                                 Search shipments
  GET    /v1/shipments/{id}                                   Retrieve a Shipment
  POST   /v1/shipments/{id}                                   Update a Shipment
  DELETE /v1/shipments/{id}                                   Delete a draft shipment
  POST   /v1/shipments/{id}/purchase                          Purchase a label
  POST   /v1/shipments/{id}/void                              Void a label
  POST   /v1/shipments/{id}/rates                             Re-rate a draft shipment
  POST   /v1/shipments/{id}/return                            Create a return shipment
  POST   /v1/shipments/{id}/label                             Re-render the label

Pickups
  POST   /v1/pickups/availability                             Check pickup availability
  GET    /v1/pickups                                          List pickups
  POST   /v1/pickups                                          Book a pickup
  GET    /v1/pickups/search                                   Search pickups
  GET    /v1/pickups/{id}                                     Retrieve a Pickup
  POST   /v1/pickups/{id}                                     Update a Pickup
  POST   /v1/pickups/{id}/cancel                              Cancel a pickup

Manifests
  GET    /v1/manifests                                        List manifests
  POST   /v1/manifests                                        Create (close out) one or more manifests
  GET    /v1/manifests/{id}                                   Retrieve a Manifest
  POST   /v1/manifests/{id}                                   Update a Manifest
  POST   /v1/manifests/preview                                Preview the day's close-out
  POST   /v1/manifests/{id}/reprint                           Re-fetch manifest documents

Files
  GET    /v1/files                                            List files
  POST   /v1/files                                            Upload a file
  GET    /v1/files/{id}                                       Retrieve a File
  DELETE /v1/files/{id}                                       Delete a File
  GET    /v1/files/{id}/contents                              Download file contents

Document Uploads
  GET    /v1/document_uploads                                 List document uploads
  POST   /v1/document_uploads                                 Submit customs documents to a carrier
  GET    /v1/document_uploads/{id}                            Retrieve a DocumentUpload
  POST   /v1/document_uploads/{id}                            Update a DocumentUpload

Tracking
  GET    /v1/trackers                                         List trackers
  POST   /v1/trackers                                         Create a tracker
  GET    /v1/trackers/search                                  Search trackers
  GET    /v1/trackers/{id}                                    Retrieve a Tracker
  POST   /v1/trackers/{id}                                    Update a Tracker
  DELETE /v1/trackers/{id}                                    Discard a tracker
  POST   /v1/trackers/{id}/refresh                            Force a carrier poll
  GET    /v1/trackers/{id}/events                             List tracking events

Webhooks
  GET    /v1/webhook_endpoints                                List webhook endpoints
  POST   /v1/webhook_endpoints                                Create a webhook endpoint
  GET    /v1/webhook_endpoints/{id}                           Retrieve a WebhookEndpoint
  POST   /v1/webhook_endpoints/{id}                           Update a WebhookEndpoint
  DELETE /v1/webhook_endpoints/{id}                           Delete a WebhookEndpoint
  POST   /v1/webhook_endpoints/{id}/rotate_secret             Rotate the signing secret
  POST   /v1/webhook_endpoints/{id}/test                      Send a test event

Events
  GET    /v1/events                                           List events
  GET    /v1/events/{id}                                      Retrieve an event
  GET    /v1/events/{id}/deliveries                           List delivery attempts
  POST   /v1/events/{id}/redeliver                            Redeliver an event

Inbound
  POST   /v1/inbound/{connection_id}                          Carrier push receiver (carrier-native payload)
  GET    /v1/inbound_events                                   List inbound events
  POST   /v1/inbound_events                                   Inject canonical events
  GET    /v1/inbound_events/{id}                              Retrieve a InboundEvent

Test Helpers
  POST   /v1/test_helpers/trackers/{id}/advance               Advance a test tracker
  POST   /v1/test_helpers/shipments/{id}/charge_adjustment    Simulate a carrier charge adjustment

Carriers
  GET    /v1/carriers                                         List carriers
  GET    /v1/carriers/{id}                                    Retrieve a carrier

Connections
  GET    /v1/connections                                      List connections
  POST   /v1/connections                                      Create a credentials-based connection
  GET    /v1/connections/{id}                                 Retrieve a Connection
  POST   /v1/connections/{id}                                 Update a Connection
  DELETE /v1/connections/{id}                                 Delete a Connection
  POST   /v1/connections/{id}/verify                          Verify connection credentials
  POST   /v1/connect_sessions                                 Start an OAuth/OIDC connect flow
  GET    /v1/connect_sessions/{id}                            Retrieve a connect session
  GET    /v1/oauth/callback                                   Carrier OAuth redirect target

Batches
  POST   /v1/batches                                          Create a batch
  GET    /v1/batches/{id}                                     Retrieve a batch

Pickup Schedules
  GET    /v1/pickup_schedules                                 List pickup schedules
  POST   /v1/pickup_schedules                                 Create a pickup schedule
  GET    /v1/pickup_schedules/{id}                            Retrieve a PickupSchedule
  POST   /v1/pickup_schedules/{id}                            Update a PickupSchedule
  POST   /v1/pickup_schedules/{id}/pause                      Pause a pickup schedule
  POST   /v1/pickup_schedules/{id}/resume                     Resume a pickup schedule
  POST   /v1/pickup_schedules/{id}/cancel                     Cancel a pickup schedule
  POST   /v1/pickup_schedules/{id}/skip                       Skip a pickup schedule
  POST   /v1/pickup_schedules/{id}/add                        Add a pickup schedule
  GET    /v1/pickup_schedules/{id}/occurrences                List occurrences

Trade
  GET    /v1/classifications                                  List classifications
  POST   /v1/classifications                                  Classify items
  GET    /v1/classifications/{id}                             Retrieve a Classification
  POST   /v1/classifications/{id}/apply                       Apply classification to a draft shipment
  POST   /v1/classifications/{id}/feedback                    Submit classification feedback
  GET    /v1/compliance_screenings                            List compliance screenings
  POST   /v1/compliance_screenings                            Screen parties and goods
  GET    /v1/compliance_screenings/{id}                       Retrieve a ComplianceScreening
  GET    /v1/landed_costs                                     List landed costs
  POST   /v1/landed_costs                                     Quote landed cost
  GET    /v1/landed_costs/{id}                                Retrieve a LandedCost
  GET    /v1/tariffs/{country}/{hs_code}                      Look up a tariff line
  GET    /v1/duty_collections                                 List duty collections
  GET    /v1/duty_collections/{id}                            Retrieve a DutyCollection
  POST   /v1/duty_collections/{id}/pay                        Pay a duty collection
  POST   /v1/duty_collections/export                          Export duty collections

Catalog
  POST   /v1/service_availability                             Check serviceability

Routes
  POST   /v1/journeys/plan                                    Plan a journey
  GET    /v1/shipments/{id}/journey                           Retrieve a shipment's journey

Injection
  POST   /v1/shipments/{id}/cancel_injection                  Cancel an injected shipment
  GET    /v1/asns                                             List asns
  POST   /v1/asns                                             Create an advance shipping notice
  GET    /v1/asns/{id}                                        Retrieve a Asn
  POST   /v1/asns/{id}                                        Update a Asn
  POST   /v1/asns/{id}/dispatch                               ASN: dispatch
  POST   /v1/asns/{id}/arrive                                 ASN: arrive
  POST   /v1/asns/{id}/cancel                                 ASN: cancel
  POST   /v1/asns/{id}/close                                  ASN: close
  POST   /v1/asns/{id}/receive                                ASN: receive

Accounts
  GET    /v1/accounts                                         List accounts
  POST   /v1/accounts                                         Create a child account
  GET    /v1/accounts/{id}                                    Retrieve a Account
  POST   /v1/accounts/{id}                                    Update a Account
  GET    /v1/account                                          Retrieve the current account

Products
  GET    /v1/products                                         List products
  POST   /v1/products                                         Create a product
  GET    /v1/products/search                                  Search products
  GET    /v1/products/{id}                                    Retrieve a Product
  POST   /v1/products/{id}                                    Update a Product
  DELETE /v1/products/{id}                                    Delete an unreferenced product
  POST   /v1/products/upsert                                  Upsert a product
  POST   /v1/products/import                                  Import products from a file
  POST   /v1/products/{id}/archive                            Archive a product
  POST   /v1/products/{id}/unarchive                          Unarchive a product

IoT
  GET    /v1/device_events                                    List device events
  POST   /v1/device_events                                    Ingest device events
  GET    /v1/shipments/{id}/conditions                        Condition readings and excursions

Data Network
  GET    /v1/participants                                     List participants
  POST   /v1/participants                                     Register a participant (DID)
  GET    /v1/participants/{id}                                Retrieve a Participant
  POST   /v1/participants/{id}/credentials                    Attach a verifiable credential
  POST   /v1/participants/{id}/rotate_keys                    Rotate participant keys
  GET    /v1/records                                          List records
  POST   /v1/records                                          Write a record
  POST   /v1/records/query                                    Query records
  POST   /v1/records/verify                                   Verify a record
  GET    /v1/records/feed                                     Change feed
  POST   /v1/records/erase                                    Crypto-shred personal data
  GET    /v1/anchors/{id}                                     Retrieve an anchor
  GET    /v1/access_grants                                    List access grants
  POST   /v1/access_grants                                    Grant access
  GET    /v1/access_grants/{id}                               Retrieve a AccessGrant
  POST   /v1/access_grants/{id}/revoke                        Revoke a grant
  GET    /v1/attestations                                     List attestations
  POST   /v1/attestations                                     Create an attestation
  GET    /v1/attestations/{id}                                Retrieve a Attestation
  POST   /v1/datasets                                         Create a dataset extract
  GET    /v1/timelines/{shipment_id}                          End-to-end timeline
  GET    /v1/timelines/{shipment_id}/events                   Merged events with provenance
  POST   /v1/timelines/resolve                                Resolve an identifier to shipments
  POST   /v1/identifier_links                                 Link identifiers
  GET    /v1/milestone_definitions                            Milestone definition set

Consolidation
  GET    /v1/shipments/{id}/custody                           Custody chain

Templates
  POST   /v1/documents/generate                               Generate a document
  GET    /v1/documents                                        List documents
  GET    /v1/documents/{id}                                   Retrieve a Document
  DELETE /v1/documents/{id}                                   Delete a standalone document
  GET    /v1/document_jobs                                    List document jobs
  POST   /v1/document_jobs                                    Create a document job
  GET    /v1/document_jobs/{id}                               Retrieve a DocumentJob
  GET    /v1/label_specs                                      List label specs
  GET    /v1/label_specs/{id}                                 Retrieve a LabelSpec
  POST   /v1/label_specs/{id}/certify                         Certify labels against the spec
  POST   /v1/label_specs/{id}/tracking_ranges                 Allocate tracking numbers
  POST   /v1/documents/ingest                                 Ingest a document
  GET    /v1/document_ingestions                              List document ingestions
  GET    /v1/document_ingestions/{id}                         Retrieve a DocumentIngestion
  POST   /v1/document_ingestions/{id}/apply                   Apply extracted data
  POST   /v1/document_ingestions/{id}/reject                  Reject an ingestion

Integrations
  GET    /v1/integrations                                     List integrations
  GET    /v1/integrations/{id}                                Retrieve an integration
  POST   /v1/address_validations                              Validate an address
  GET    /v1/address_validations/{id}                         Retrieve an address validation
  POST   /v1/insurance_quotes                                 Quote insurance
  GET    /v1/coverages                                        List coverages
  POST   /v1/coverages                                        Buy coverage
  GET    /v1/coverages/{id}                                   Retrieve a Coverage
  POST   /v1/coverages/{id}/cancel                            Cancel coverage
  GET    /v1/claims                                           List claims
  POST   /v1/claims                                           Submit a claim
  GET    /v1/claims/{id}                                      Retrieve a Claim
  POST   /v1/claims/{id}                                      Update a Claim
  POST   /v1/claims/{id}/withdraw                             Withdraw a claim

Jobs
  GET    /v1/jobs                                             List jobs
  POST   /v1/jobs                                             Start a job
  GET    /v1/jobs/{id}                                        Retrieve a Job
  POST   /v1/jobs/{id}/cancel                                 Cancel a job
  POST   /v1/jobs/{id}/retry                                  Retry a job
  GET    /v1/jobs/{id}/logs                                   Job logs
  GET    /v1/jobs/{id}/stream                                 Stream job progress (SSE)

Billing
  GET    /v1/invoices                                         List invoices
  GET    /v1/invoices/{id}                                    Retrieve a Invoice
  POST   /v1/invoices/{id}/dispute                            Invoice: dispute
  POST   /v1/invoices/{id}/pay                                Pay an invoice
  GET    /v1/invoices/{id}/export                             Export an invoice
  GET    /v1/invoices/upcoming                                Preview the upcoming usage invoice
  GET    /v1/usage_records                                    List usage records
  POST   /v1/usage_records                                    Report usage
  GET    /v1/usage_records/{id}                               Retrieve a UsageRecord
  POST   /v1/usage_records/import                             Import usage records
  GET    /v1/usage_summaries                                  Usage summary per meter
  GET    /v1/balance                                          Retrieve the prepaid balance
  POST   /v1/balance/top_up                                   Top up the balance
  GET    /v1/balance_transactions                             List balance transactions
  POST   /v1/payment_methods/setup                            Start hosted payment method setup
  GET    /v1/payment_methods                                  List payment methods
  GET    /v1/payment_methods/{id}                             Retrieve a PaymentMethod
  DELETE /v1/payment_methods/{id}                             Delete a PaymentMethod
  GET    /v1/payments                                         List payments
  GET    /v1/payments/{id}                                    Retrieve a Payment

Inventory
  GET    /v1/inventory/levels                                 Stock levels
  GET    /v1/fulfillment_orders                               List fulfillment orders
  POST   /v1/fulfillment_orders                               Create a fulfillment order
  GET    /v1/fulfillment_orders/search                        Search fulfillment orders
  GET    /v1/fulfillment_orders/{id}                          Retrieve a FulfillmentOrder
  POST   /v1/fulfillment_orders/{id}                          Update a FulfillmentOrder
  POST   /v1/fulfillment_orders/{id}/cancel                   Fulfillment order: cancel

Discovery
  GET    /.well-known/shipping-configuration                  Shipping configuration document
```

## Repository layout and docs site

| Path | Purpose |
|---|---|
| `shipping.md` | Agent discovery file template |
| `spec/*.md` | Normative chapters |
| `openapi.yaml` | OpenAPI 3.1 reference for the REST surface, generated by `python3 tools/build_openapi.py openapi.yaml` |
| `graphql/schema.graphql`, `spec/graphql.md` | The GraphQL back-office surface (SDL and reference page), generated by the same command. `tools/graphql_surface.py` holds the REST/GraphQL classification. |
| `graphql-reference/` | One generated page per GraphQL field (arguments, input fields, return fields, request, variables and response examples) |
| `map.mdx` | The Industry Map tab, embedding `site/explorer.html` |
| `tools/check_mermaid.py` | Renders every Mermaid diagram in the given files and reports failures |
| `docs.json`, `index.md`, `logo/` | Mintlify site config. Preview with `npx mint dev`. |
| `site/industry-map.html` | Interactive industry map (artifact source). `python3 tools/build_site.py` writes the standalone `site/explorer.html`, served by the docs site at `/site/explorer.html`. |

The source is plain Markdown plus OpenAPI, so it stays portable if we move off Mintlify.

## Normative language

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be interpreted as described in RFC 2119 and RFC 8174 when, and only when, they appear in all capitals.

## License

Specification text: CC BY 4.0. Schemas and examples: Apache-2.0. A shipping standard that costs money to read does not get adopted.

## Building and deploying

The docs site is a Mintlify project exported to static files and hosted on Cloudflare Pages.

- Local preview: `python3 tools/build_site.py && npx mint dev`
- Static build: `bash build.sh` writes `_site/` (Mintlify export plus `_headers`)
- Cloudflare Pages: build command `bash build.sh`, output directory `_site`. `functions/_middleware.js` serves the RSC payloads that make in-page navigation work.
