---
title: "GraphQL Interface"
description: "Internal CRUD over every domain object (shipments, trackers, fleet, routes, catalog, billing…) plus the back-office operations, over GraphQL. Generated from the same object model as the REST Interface."
---

The specification has two interfaces over **one object model**:

| Interface | For | Covers | Endpoint |
|---|---|---|---|
| **REST Interface** | Integrators: shippers, platforms, partners, devices and agents | Each module's public workflows and actions: rate, purchase, void, book, close, track, inject, generate, verify | `https://{host}/v1/…`, in the REST Interface tab |
| **GraphQL Interface** | Internal tools: implementer dashboards, operations consoles, carrier and network member administration, data teams | CRUD over **every** domain object (shipments, trackers, pickups, manifests, products, fleet, routes, catalog, invoices…), plus the back-office operations that exist only here | `POST https://{host}/graphql` |

Both interfaces return the same canonical objects with the same field names, IDs, enums and metadata namespaces. A `Shipment` from `query { shipment(id:) }` is the object `GET /v1/shipments/{id}` returns. CRUD operations available on both interfaces behave identically: same validation, same state rules, same events.

## Conventions

- **Authentication and scopes** are the same as REST (Conventions §3): `Authorization: Bearer …`, `Shipping-Version`, and `Shipping-Account` to act for a connected or member account. Each field requires the scope of its REST counterpart (`shipments:write` for `createShipment`, `catalog:write` for `createService`).
- **Idempotency.** Mutations that create or act accept the `Idempotency-Key` header, with the same rules as Conventions §8. Fields that spend money are flagged on their page.
- **Errors** use the standard GraphQL `errors[]`, and `extensions` carries the REST error object: `extensions.type`, `extensions.code` (the Conventions §9 registry), `extensions.param`, `extensions.request_id`.
- **Lists** return `{ data, has_more }` with `limit`, `startingAfter` and `endingBefore` arguments, mirroring REST cursor pagination.
- **Events.** Mutations emit the same webhook events as their REST counterparts. Subscribing over GraphQL (`subscription { events(types: […]) }`) is an optional capability (`graphql.subscriptions`).
- **Schema.** The full SDL is published at [`graphql/schema.graphql`](/graphql/schema.graphql), and implementers SHOULD serve introspection to authenticated clients.

Every field below has its own page with arguments, return fields and request, variables and response examples. Module chapters describe the behavior.

## Accounts

| Field | Kind | What it does |
|---|---|---|
| [`accounts`](/graphql-reference/accounts/accounts) | query | List accounts |
| [`createAccount`](/graphql-reference/accounts/create-account) | mutation | Create a child account |
| [`account`](/graphql-reference/accounts/account) | query | Retrieve a Account |
| [`updateAccount`](/graphql-reference/accounts/update-account) | mutation | Update a Account |
| [`accountGet`](/graphql-reference/accounts/account-get) | query | Retrieve the current account |
| [`suspendAccount`](/graphql-reference/accounts/suspend-account) | mutation | Suspend an account |
| [`reactivateAccount`](/graphql-reference/accounts/reactivate-account) | mutation | Reactivate an account |
| [`closeAccount`](/graphql-reference/accounts/close-account) | mutation | Close an account |
| [`identityProviders`](/graphql-reference/accounts/identity-providers) | query | List identity providers |
| [`createIdentityProvider`](/graphql-reference/accounts/create-identity-provider) | mutation | Register an identity provider |
| [`identityProvider`](/graphql-reference/accounts/identity-provider) | query | Retrieve a IdentityProvider |
| [`updateIdentityProvider`](/graphql-reference/accounts/update-identity-provider) | mutation | Update a IdentityProvider |
| [`deleteIdentityProvider`](/graphql-reference/accounts/delete-identity-provider) | mutation | Delete a IdentityProvider |
| [`verifyDomainIdentityProvider`](/graphql-reference/accounts/verify-domain-identity-provider) | mutation | Verify a domain |
| [`testIdentityProvider`](/graphql-reference/accounts/test-identity-provider) | mutation | Test sign-in |
| [`memberships`](/graphql-reference/accounts/memberships) | query | List memberships |
| [`membership`](/graphql-reference/accounts/membership) | query | Retrieve a Membership |
| [`updateMembership`](/graphql-reference/accounts/update-membership) | mutation | Update a Membership |
| [`deleteMembership`](/graphql-reference/accounts/delete-membership) | mutation | Delete a Membership |
| [`invitations`](/graphql-reference/accounts/invitations) | query | List invitations |
| [`createInvitation`](/graphql-reference/accounts/create-invitation) | mutation | Invite a member |
| [`invitation`](/graphql-reference/accounts/invitation) | query | Retrieve a Invitation |
| [`revokeInvitation`](/graphql-reference/accounts/revoke-invitation) | mutation | Revoke an invitation |
| [`roles`](/graphql-reference/accounts/roles) | query | List roles |
| [`createRole`](/graphql-reference/accounts/create-role) | mutation | Create a custom role |
| [`role`](/graphql-reference/accounts/role) | query | Retrieve a Role |
| [`updateRole`](/graphql-reference/accounts/update-role) | mutation | Update a Role |
| [`deleteRole`](/graphql-reference/accounts/delete-role) | mutation | Delete a Role |
| [`apiKeys`](/graphql-reference/accounts/api-keys) | query | List api keys |
| [`createApiKey`](/graphql-reference/accounts/create-api-key) | mutation | Create an API key |
| [`apiKey`](/graphql-reference/accounts/api-key) | query | Retrieve a ApiKey |
| [`updateApiKey`](/graphql-reference/accounts/update-api-key) | mutation | Update a ApiKey |
| [`deleteApiKey`](/graphql-reference/accounts/delete-api-key) | mutation | Delete a ApiKey |
| [`rollApiKey`](/graphql-reference/accounts/roll-api-key) | mutation | Roll an API key |

## Apps

| Field | Kind | What it does |
|---|---|---|
| [`apps`](/graphql-reference/apps/apps) | query | List apps |
| [`createApp`](/graphql-reference/apps/create-app) | mutation | Register a carrier OAuth app |
| [`app`](/graphql-reference/apps/app) | query | Retrieve a App |
| [`updateApp`](/graphql-reference/apps/update-app) | mutation | Update a App |
| [`deleteApp`](/graphql-reference/apps/delete-app) | mutation | Delete a App |
| [`rotateSecretApp`](/graphql-reference/apps/rotate-secret-app) | mutation | Rotate a dynamic app's client secret |

## Batches

| Field | Kind | What it does |
|---|---|---|
| [`createBatche`](/graphql-reference/batches/create-batche) | mutation | Create a batch |
| [`batche`](/graphql-reference/batches/batche) | query | Retrieve a batch |

## Billing

| Field | Kind | What it does |
|---|---|---|
| [`invoices`](/graphql-reference/billing/invoices) | query | List invoices |
| [`invoice`](/graphql-reference/billing/invoice) | query | Retrieve a Invoice |
| [`usageRecords`](/graphql-reference/billing/usage-records) | query | List usage records |
| [`createUsageRecord`](/graphql-reference/billing/create-usage-record) | mutation | Report usage |
| [`usageRecord`](/graphql-reference/billing/usage-record) | query | Retrieve a UsageRecord |
| [`usageSummaries`](/graphql-reference/billing/usage-summaries) | query | Usage summary per meter |
| [`balance`](/graphql-reference/billing/balance) | query | Retrieve the prepaid balance |
| [`balanceTransactions`](/graphql-reference/billing/balance-transactions) | query | List balance transactions |
| [`paymentMethods`](/graphql-reference/billing/payment-methods) | query | List payment methods |
| [`paymentMethod`](/graphql-reference/billing/payment-method) | query | Retrieve a PaymentMethod |
| [`deletePaymentMethod`](/graphql-reference/billing/delete-payment-method) | mutation | Delete a PaymentMethod |
| [`payments`](/graphql-reference/billing/payments) | query | List payments |
| [`payment`](/graphql-reference/billing/payment) | query | Retrieve a Payment |
| [`createInvoice`](/graphql-reference/billing/create-invoice) | mutation | Create a draft invoice |
| [`updateInvoice`](/graphql-reference/billing/update-invoice) | mutation | Update a Invoice |
| [`finalizeInvoice`](/graphql-reference/billing/finalize-invoice) | mutation | Invoice: finalize |
| [`sendInvoice`](/graphql-reference/billing/send-invoice) | mutation | Invoice: send |
| [`voidInvoice`](/graphql-reference/billing/void-invoice) | mutation | Invoice: void |
| [`markUncollectibleInvoice`](/graphql-reference/billing/mark-uncollectible-invoice) | mutation | Invoice: mark_uncollectible |
| [`importInvoice`](/graphql-reference/billing/import-invoice) | mutation | Import invoices from a file |
| [`reconciliations`](/graphql-reference/billing/reconciliations) | query | List reconciliations |
| [`createReconciliation`](/graphql-reference/billing/create-reconciliation) | mutation | Reconcile an invoice |
| [`reconciliation`](/graphql-reference/billing/reconciliation) | query | Retrieve a Reconciliation |
| [`resolveReconciliation`](/graphql-reference/billing/resolve-reconciliation) | mutation | Resolve a reconciliation line |
| [`meters`](/graphql-reference/billing/meters) | query | List meters |
| [`createMeter`](/graphql-reference/billing/create-meter) | mutation | Create a meter |
| [`meter`](/graphql-reference/billing/meter) | query | Retrieve a Meter |
| [`updateMeter`](/graphql-reference/billing/update-meter) | mutation | Update a Meter |
| [`pricePlans`](/graphql-reference/billing/price-plans) | query | List price plans |
| [`createPricePlan`](/graphql-reference/billing/create-price-plan) | mutation | Create a price plan |
| [`pricePlan`](/graphql-reference/billing/price-plan) | query | Retrieve a PricePlan |
| [`updatePricePlan`](/graphql-reference/billing/update-price-plan) | mutation | Update a PricePlan |
| [`billingProfile`](/graphql-reference/billing/billing-profile) | query | Retrieve the billing profile |
| [`updateBillingProfile`](/graphql-reference/billing/update-billing-profile) | mutation | Update the billing profile |
| [`refundPayment`](/graphql-reference/billing/refund-payment) | mutation | Refund a payment |
| [`reconcileStatementPayment`](/graphql-reference/billing/reconcile-statement-payment) | mutation | Reconcile an ISO 20022 camt.053 statement |
| [`payouts`](/graphql-reference/billing/payouts) | query | List payouts |
| [`payout`](/graphql-reference/billing/payout) | query | Retrieve a Payout |

## Carriers

| Field | Kind | What it does |
|---|---|---|
| [`carriers`](/graphql-reference/carriers/carriers) | query | List carriers |
| [`carrier`](/graphql-reference/carriers/carrier) | query | Retrieve a carrier |

## Catalog

| Field | Kind | What it does |
|---|---|---|
| [`createServiceAvailability`](/graphql-reference/catalog/create-service-availability) | mutation | Check serviceability |
| [`services`](/graphql-reference/catalog/services) | query | List services |
| [`createService`](/graphql-reference/catalog/create-service) | mutation | Create a service |
| [`service`](/graphql-reference/catalog/service) | query | Retrieve a CatalogService |
| [`updateService`](/graphql-reference/catalog/update-service) | mutation | Update a CatalogService |
| [`deleteService`](/graphql-reference/catalog/delete-service) | mutation | Delete a draft service |
| [`publishService`](/graphql-reference/catalog/publish-service) | mutation | Publish a service |
| [`serviceVersions`](/graphql-reference/catalog/service-versions) | query | List service versions |
| [`options`](/graphql-reference/catalog/options) | query | List options |
| [`createOption`](/graphql-reference/catalog/create-option) | mutation | Create a option |
| [`option`](/graphql-reference/catalog/option) | query | Retrieve a CatalogOption |
| [`updateOption`](/graphql-reference/catalog/update-option) | mutation | Update a CatalogOption |
| [`deleteOption`](/graphql-reference/catalog/delete-option) | mutation | Delete a draft option |
| [`publishOption`](/graphql-reference/catalog/publish-option) | mutation | Publish a option |
| [`optionVersions`](/graphql-reference/catalog/option-versions) | query | List option versions |
| [`packagings`](/graphql-reference/catalog/packagings) | query | List packagings |
| [`createPackaging`](/graphql-reference/catalog/create-packaging) | mutation | Create a packaging |
| [`packaging`](/graphql-reference/catalog/packaging) | query | Retrieve a Packaging |
| [`updatePackaging`](/graphql-reference/catalog/update-packaging) | mutation | Update a Packaging |
| [`deletePackaging`](/graphql-reference/catalog/delete-packaging) | mutation | Delete a draft packaging |
| [`publishPackaging`](/graphql-reference/catalog/publish-packaging) | mutation | Publish a packaging |
| [`packagingVersions`](/graphql-reference/catalog/packaging-versions) | query | List packaging versions |
| [`zones`](/graphql-reference/catalog/zones) | query | List zones |
| [`createZone`](/graphql-reference/catalog/create-zone) | mutation | Create a zone |
| [`zone`](/graphql-reference/catalog/zone) | query | Retrieve a Zone |
| [`updateZone`](/graphql-reference/catalog/update-zone) | mutation | Update a Zone |
| [`deleteZone`](/graphql-reference/catalog/delete-zone) | mutation | Delete a draft zone |
| [`publishZone`](/graphql-reference/catalog/publish-zone) | mutation | Publish a zone |
| [`zoneVersions`](/graphql-reference/catalog/zone-versions) | query | List zone versions |
| [`matchZone`](/graphql-reference/catalog/match-zone) | mutation | Match an address to zones |

## Connections

| Field | Kind | What it does |
|---|---|---|
| [`connections`](/graphql-reference/connections/connections) | query | List connections |
| [`createConnection`](/graphql-reference/connections/create-connection) | mutation | Create a credentials-based connection |
| [`connection`](/graphql-reference/connections/connection) | query | Retrieve a Connection |
| [`updateConnection`](/graphql-reference/connections/update-connection) | mutation | Update a Connection |
| [`deleteConnection`](/graphql-reference/connections/delete-connection) | mutation | Delete a Connection |
| [`createConnectSession`](/graphql-reference/connections/create-connect-session) | mutation | Start an OAuth/OIDC connect flow |
| [`connectSession`](/graphql-reference/connections/connect-session) | query | Retrieve a connect session |

## Consolidation

| Field | Kind | What it does |
|---|---|---|
| [`consolidations`](/graphql-reference/consolidation/consolidations) | query | List consolidations |
| [`createConsolidation`](/graphql-reference/consolidation/create-consolidation) | mutation | Create a consolidation |
| [`consolidation`](/graphql-reference/consolidation/consolidation) | query | Retrieve a Consolidation |
| [`updateConsolidation`](/graphql-reference/consolidation/update-consolidation) | mutation | Update a Consolidation |
| [`addConsolidation`](/graphql-reference/consolidation/add-consolidation) | mutation | Consolidation: add |
| [`removeConsolidation`](/graphql-reference/consolidation/remove-consolidation) | mutation | Consolidation: remove |
| [`closeConsolidation`](/graphql-reference/consolidation/close-consolidation) | mutation | Consolidation: close |
| [`sealConsolidation`](/graphql-reference/consolidation/seal-consolidation) | mutation | Consolidation: seal |
| [`breakSealConsolidation`](/graphql-reference/consolidation/break-seal-consolidation) | mutation | Consolidation: break_seal |
| [`loadConsolidation`](/graphql-reference/consolidation/load-consolidation) | mutation | Consolidation: load |
| [`unloadConsolidation`](/graphql-reference/consolidation/unload-consolidation) | mutation | Consolidation: unload |
| [`deconsolidateConsolidation`](/graphql-reference/consolidation/deconsolidate-consolidation) | mutation | Consolidation: deconsolidate |
| [`labelConsolidation`](/graphql-reference/consolidation/label-consolidation) | mutation | Generate a consolidation label |
| [`consolidationContents`](/graphql-reference/consolidation/consolidation-contents) | query | List contents |
| [`conveyances`](/graphql-reference/consolidation/conveyances) | query | List conveyances |
| [`createConveyance`](/graphql-reference/consolidation/create-conveyance) | mutation | Create a conveyance |
| [`conveyance`](/graphql-reference/consolidation/conveyance) | query | Retrieve a Conveyance |
| [`updateConveyance`](/graphql-reference/consolidation/update-conveyance) | mutation | Update a Conveyance |
| [`closeConveyance`](/graphql-reference/consolidation/close-conveyance) | mutation | Conveyance: close |
| [`departConveyance`](/graphql-reference/consolidation/depart-conveyance) | mutation | Conveyance: depart |
| [`arriveConveyance`](/graphql-reference/consolidation/arrive-conveyance) | mutation | Conveyance: arrive |
| [`cancelConveyance`](/graphql-reference/consolidation/cancel-conveyance) | mutation | Conveyance: cancel |
| [`conveyanceManifest`](/graphql-reference/consolidation/conveyance-manifest) | query | Conveyance manifest |

## Data Network

| Field | Kind | What it does |
|---|---|---|
| [`participants`](/graphql-reference/data-network/participants) | query | List participants |
| [`createParticipant`](/graphql-reference/data-network/create-participant) | mutation | Register a participant (DID) |
| [`participant`](/graphql-reference/data-network/participant) | query | Retrieve a Participant |
| [`records`](/graphql-reference/data-network/records) | query | List records |
| [`createRecord`](/graphql-reference/data-network/create-record) | mutation | Write a record |
| [`anchor`](/graphql-reference/data-network/anchor) | query | Retrieve an anchor |
| [`accessGrants`](/graphql-reference/data-network/access-grants) | query | List access grants |
| [`createAccessGrant`](/graphql-reference/data-network/create-access-grant) | mutation | Grant access |
| [`accessGrant`](/graphql-reference/data-network/access-grant) | query | Retrieve a AccessGrant |
| [`attestations`](/graphql-reference/data-network/attestations) | query | List attestations |
| [`createAttestation`](/graphql-reference/data-network/create-attestation) | mutation | Create an attestation |
| [`attestation`](/graphql-reference/data-network/attestation) | query | Retrieve a Attestation |
| [`createDataset`](/graphql-reference/data-network/create-dataset) | mutation | Create a dataset extract |
| [`timeline`](/graphql-reference/data-network/timeline) | query | End-to-end timeline |
| [`createIdentifierLink`](/graphql-reference/data-network/create-identifier-link) | mutation | Link identifiers |
| [`milestoneDefinition`](/graphql-reference/data-network/milestone-definition) | query | Milestone definition set |
| [`accessPolicies`](/graphql-reference/data-network/access-policies) | query | List access policies |
| [`createAccessPolicy`](/graphql-reference/data-network/create-access-policy) | mutation | Create an access policy |
| [`accessPolicy`](/graphql-reference/data-network/access-policy) | query | Retrieve a AccessPolicy |
| [`updateAccessPolicy`](/graphql-reference/data-network/update-access-policy) | mutation | Update a AccessPolicy |

## Document Uploads

| Field | Kind | What it does |
|---|---|---|
| [`documentUploads`](/graphql-reference/document-uploads/document-uploads) | query | List document uploads |
| [`createDocumentUpload`](/graphql-reference/document-uploads/create-document-upload) | mutation | Submit customs documents to a carrier |
| [`documentUpload`](/graphql-reference/document-uploads/document-upload) | query | Retrieve a DocumentUpload |
| [`updateDocumentUpload`](/graphql-reference/document-uploads/update-document-upload) | mutation | Update a DocumentUpload |

## Events

| Field | Kind | What it does |
|---|---|---|
| [`events`](/graphql-reference/events/events) | query | List events |
| [`event`](/graphql-reference/events/event) | query | Retrieve an event |

## Files

| Field | Kind | What it does |
|---|---|---|
| [`files`](/graphql-reference/files/files) | query | List files |
| [`createFile`](/graphql-reference/files/create-file) | mutation | Upload a file |
| [`file`](/graphql-reference/files/file) | query | Retrieve a File |
| [`deleteFile`](/graphql-reference/files/delete-file) | mutation | Delete a File |

## Fleet

| Field | Kind | What it does |
|---|---|---|
| [`routeRunPositions`](/graphql-reference/fleet/route-run-positions) | query | List positions |
| [`createRouteRunPosition`](/graphql-reference/fleet/create-route-run-position) | mutation | Report positions |
| [`vehicles`](/graphql-reference/fleet/vehicles) | query | List vehicles |
| [`createVehicle`](/graphql-reference/fleet/create-vehicle) | mutation | Create a vehicle |
| [`vehicle`](/graphql-reference/fleet/vehicle) | query | Retrieve a Vehicle |
| [`updateVehicle`](/graphql-reference/fleet/update-vehicle) | mutation | Update a Vehicle |
| [`deleteVehicle`](/graphql-reference/fleet/delete-vehicle) | mutation | Delete a Vehicle |
| [`vehiclePosition`](/graphql-reference/fleet/vehicle-position) | query | Latest vehicle position |
| [`drivers`](/graphql-reference/fleet/drivers) | query | List drivers |
| [`createDriver`](/graphql-reference/fleet/create-driver) | mutation | Create a driver |
| [`driver`](/graphql-reference/fleet/driver) | query | Retrieve a Driver |
| [`updateDriver`](/graphql-reference/fleet/update-driver) | mutation | Update a Driver |
| [`deleteDriver`](/graphql-reference/fleet/delete-driver) | mutation | Delete a Driver |
| [`optimizations`](/graphql-reference/fleet/optimizations) | query | List optimizations |
| [`createOptimization`](/graphql-reference/fleet/create-optimization) | mutation | Optimize runs |
| [`optimization`](/graphql-reference/fleet/optimization) | query | Retrieve a Optimization |
| [`commitOptimization`](/graphql-reference/fleet/commit-optimization) | mutation | Commit proposed runs |

## Inbound

| Field | Kind | What it does |
|---|---|---|
| [`inboundEvents`](/graphql-reference/inbound/inbound-events) | query | List inbound events |
| [`createInboundEvent`](/graphql-reference/inbound/create-inbound-event) | mutation | Inject canonical events |
| [`inboundEvent`](/graphql-reference/inbound/inbound-event) | query | Retrieve a InboundEvent |

## Injection

| Field | Kind | What it does |
|---|---|---|
| [`asns`](/graphql-reference/injection/asns) | query | List asns |
| [`createAsn`](/graphql-reference/injection/create-asn) | mutation | Create an advance shipping notice |
| [`asn`](/graphql-reference/injection/asn) | query | Retrieve a Asn |
| [`updateAsn`](/graphql-reference/injection/update-asn) | mutation | Update a Asn |

## Integrations

| Field | Kind | What it does |
|---|---|---|
| [`integrations`](/graphql-reference/integrations/integrations) | query | List integrations |
| [`integration`](/graphql-reference/integrations/integration) | query | Retrieve an integration |
| [`createAddressValidation`](/graphql-reference/integrations/create-address-validation) | mutation | Validate an address |
| [`addressValidation`](/graphql-reference/integrations/address-validation) | query | Retrieve an address validation |
| [`createInsuranceQuote`](/graphql-reference/integrations/create-insurance-quote) | mutation | Quote insurance |
| [`coverages`](/graphql-reference/integrations/coverages) | query | List coverages |
| [`createCoverage`](/graphql-reference/integrations/create-coverage) | mutation | Buy coverage |
| [`coverage`](/graphql-reference/integrations/coverage) | query | Retrieve a Coverage |
| [`claims`](/graphql-reference/integrations/claims) | query | List claims |
| [`createClaim`](/graphql-reference/integrations/create-claim) | mutation | Submit a claim |
| [`claim`](/graphql-reference/integrations/claim) | query | Retrieve a Claim |
| [`updateClaim`](/graphql-reference/integrations/update-claim) | mutation | Update a Claim |
| [`createIntegration`](/graphql-reference/integrations/create-integration) | mutation | Onboard a federated provider |

## Inventory

| Field | Kind | What it does |
|---|---|---|
| [`fulfillmentOrders`](/graphql-reference/inventory/fulfillment-orders) | query | List fulfillment orders |
| [`createFulfillmentOrder`](/graphql-reference/inventory/create-fulfillment-order) | mutation | Create a fulfillment order |
| [`searchFulfillmentOrders`](/graphql-reference/inventory/search-fulfillment-orders) | query | Search fulfillment orders |
| [`fulfillmentOrder`](/graphql-reference/inventory/fulfillment-order) | query | Retrieve a FulfillmentOrder |
| [`updateFulfillmentOrder`](/graphql-reference/inventory/update-fulfillment-order) | mutation | Update a FulfillmentOrder |
| [`storageLocations`](/graphql-reference/inventory/storage-locations) | query | List storage locations |
| [`createStorageLocation`](/graphql-reference/inventory/create-storage-location) | mutation | Create a storage location |
| [`storageLocation`](/graphql-reference/inventory/storage-location) | query | Retrieve a StorageLocation |
| [`updateStorageLocation`](/graphql-reference/inventory/update-storage-location) | mutation | Update a StorageLocation |
| [`deleteStorageLocation`](/graphql-reference/inventory/delete-storage-location) | mutation | Delete a StorageLocation |
| [`importStorageLocation`](/graphql-reference/inventory/import-storage-location) | mutation | Import a facility layout |
| [`thresholdsInventory`](/graphql-reference/inventory/thresholds-inventory) | mutation | Set low-stock thresholds |
| [`stock`](/graphql-reference/inventory/stock) | query | List stock |
| [`stockGet`](/graphql-reference/inventory/stock-get) | query | Retrieve a Stock |
| [`stockMovements`](/graphql-reference/inventory/stock-movements) | query | List stock movements |
| [`createStockMovement`](/graphql-reference/inventory/create-stock-movement) | mutation | Record a stock movement |
| [`stockMovement`](/graphql-reference/inventory/stock-movement) | query | Retrieve a StockMovement |
| [`allocateFulfillmentOrder`](/graphql-reference/inventory/allocate-fulfillment-order) | mutation | Fulfillment order: allocate |
| [`releaseToPickFulfillmentOrder`](/graphql-reference/inventory/release-to-pick-fulfillment-order) | mutation | Fulfillment order: release_to_pick |
| [`packFulfillmentOrder`](/graphql-reference/inventory/pack-fulfillment-order) | mutation | Fulfillment order: pack |
| [`shipFulfillmentOrder`](/graphql-reference/inventory/ship-fulfillment-order) | mutation | Ship a fulfillment order |
| [`waves`](/graphql-reference/inventory/waves) | query | List waves |
| [`createWave`](/graphql-reference/inventory/create-wave) | mutation | Release a wave |
| [`wave`](/graphql-reference/inventory/wave) | query | Retrieve a Wave |
| [`inventoryCounts`](/graphql-reference/inventory/inventory-counts) | query | List inventory counts |
| [`createInventoryCount`](/graphql-reference/inventory/create-inventory-count) | mutation | Start a count |
| [`inventoryCount`](/graphql-reference/inventory/inventory-count) | query | Retrieve a InventoryCount |
| [`linesInventoryCount`](/graphql-reference/inventory/lines-inventory-count) | mutation | Add count lines |
| [`completeInventoryCount`](/graphql-reference/inventory/complete-inventory-count) | mutation | Complete a count |

## IoT

| Field | Kind | What it does |
|---|---|---|
| [`deviceEvents`](/graphql-reference/iot/device-events) | query | List device events |
| [`createDeviceEvent`](/graphql-reference/iot/create-device-event) | mutation | Ingest device events |
| [`devices`](/graphql-reference/iot/devices) | query | List devices |
| [`createDevice`](/graphql-reference/iot/create-device) | mutation | Register a device |
| [`device`](/graphql-reference/iot/device) | query | Retrieve a Device |
| [`updateDevice`](/graphql-reference/iot/update-device) | mutation | Update a Device |
| [`deleteDevice`](/graphql-reference/iot/delete-device) | mutation | Delete a Device |
| [`certificateDevice`](/graphql-reference/iot/certificate-device) | mutation | Issue a device certificate |
| [`tokenDevice`](/graphql-reference/iot/token-device) | mutation | Issue a device token |
| [`attachDevice`](/graphql-reference/iot/attach-device) | mutation | Attach a device |
| [`detachDevice`](/graphql-reference/iot/detach-device) | mutation | Detach a device |
| [`deactivateDevice`](/graphql-reference/iot/deactivate-device) | mutation | Deactivate a device |

## Jobs

| Field | Kind | What it does |
|---|---|---|
| [`jobs`](/graphql-reference/jobs/jobs) | query | List jobs |
| [`createJob`](/graphql-reference/jobs/create-job) | mutation | Start a job |
| [`job`](/graphql-reference/jobs/job) | query | Retrieve a Job |
| [`jobSchedules`](/graphql-reference/jobs/job-schedules) | query | List job schedules |
| [`createJobSchedule`](/graphql-reference/jobs/create-job-schedule) | mutation | Create a job schedule |
| [`jobSchedule`](/graphql-reference/jobs/job-schedule) | query | Retrieve a JobSchedule |
| [`updateJobSchedule`](/graphql-reference/jobs/update-job-schedule) | mutation | Update a JobSchedule |
| [`deleteJobSchedule`](/graphql-reference/jobs/delete-job-schedule) | mutation | Delete a JobSchedule |
| [`pauseJobSchedule`](/graphql-reference/jobs/pause-job-schedule) | mutation | Job schedule: pause |
| [`resumeJobSchedule`](/graphql-reference/jobs/resume-job-schedule) | mutation | Job schedule: resume |
| [`runNowJobSchedule`](/graphql-reference/jobs/run-now-job-schedule) | mutation | Job schedule: run_now |

## Manifests

| Field | Kind | What it does |
|---|---|---|
| [`manifests`](/graphql-reference/manifests/manifests) | query | List manifests |
| [`createManifest`](/graphql-reference/manifests/create-manifest) | mutation | Create (close out) one or more manifests |
| [`manifest`](/graphql-reference/manifests/manifest) | query | Retrieve a Manifest |
| [`updateManifest`](/graphql-reference/manifests/update-manifest) | mutation | Update a Manifest |

## Network

| Field | Kind | What it does |
|---|---|---|
| [`networkMembers`](/graphql-reference/network/network-members) | mutation | List a carrier member |
| [`pauseMember`](/graphql-reference/network/pause-member) | mutation | Pause a carrier member |
| [`delistMember`](/graphql-reference/network/delist-member) | mutation | Delist a carrier member |
| [`interlineAgreements`](/graphql-reference/network/interline-agreements) | query | List interline agreements |
| [`createInterlineAgreement`](/graphql-reference/network/create-interline-agreement) | mutation | Propose an interline agreement |
| [`interlineAgreement`](/graphql-reference/network/interline-agreement) | query | Retrieve a InterlineAgreement |
| [`updateInterlineAgreement`](/graphql-reference/network/update-interline-agreement) | mutation | Update a InterlineAgreement |
| [`signInterlineAgreement`](/graphql-reference/network/sign-interline-agreement) | mutation | Sign an interline agreement |
| [`suspendInterlineAgreement`](/graphql-reference/network/suspend-interline-agreement) | mutation | Suspend an interline agreement |
| [`terminateInterlineAgreement`](/graphql-reference/network/terminate-interline-agreement) | mutation | Terminate an interline agreement |
| [`ledgerEntries`](/graphql-reference/network/ledger-entries) | query | List ledger entries |
| [`ledgerEntry`](/graphql-reference/network/ledger-entry) | query | Retrieve a LedgerEntry |
| [`settlements`](/graphql-reference/network/settlements) | query | List settlements |
| [`settlement`](/graphql-reference/network/settlement) | query | Retrieve a Settlement |
| [`closeSettlement`](/graphql-reference/network/close-settlement) | mutation | Close a settlement |
| [`disputeSettlement`](/graphql-reference/network/dispute-settlement) | mutation | Dispute settlement entries |
| [`serviceLevels`](/graphql-reference/network/service-levels) | query | List service levels |
| [`createServiceLevel`](/graphql-reference/network/create-service-level) | mutation | Define a service level |
| [`serviceLevel`](/graphql-reference/network/service-level) | query | Retrieve a NetworkServiceLevel |
| [`updateServiceLevel`](/graphql-reference/network/update-service-level) | mutation | Update a NetworkServiceLevel |
| [`deleteServiceLevel`](/graphql-reference/network/delete-service-level) | mutation | Delete a NetworkServiceLevel |

## Pickup Schedules

| Field | Kind | What it does |
|---|---|---|
| [`pickupSchedules`](/graphql-reference/pickup-schedules/pickup-schedules) | query | List pickup schedules |
| [`createPickupSchedule`](/graphql-reference/pickup-schedules/create-pickup-schedule) | mutation | Create a pickup schedule |
| [`pickupSchedule`](/graphql-reference/pickup-schedules/pickup-schedule) | query | Retrieve a PickupSchedule |
| [`updatePickupSchedule`](/graphql-reference/pickup-schedules/update-pickup-schedule) | mutation | Update a PickupSchedule |

## Pickups

| Field | Kind | What it does |
|---|---|---|
| [`pickups`](/graphql-reference/pickups/pickups) | query | List pickups |
| [`createPickup`](/graphql-reference/pickups/create-pickup) | mutation | Book a pickup |
| [`searchPickups`](/graphql-reference/pickups/search-pickups) | query | Search pickups |
| [`pickup`](/graphql-reference/pickups/pickup) | query | Retrieve a Pickup |
| [`updatePickup`](/graphql-reference/pickups/update-pickup) | mutation | Update a Pickup |

## Pricing

| Field | Kind | What it does |
|---|---|---|
| [`rateSheets`](/graphql-reference/pricing/rate-sheets) | query | List rate sheets |
| [`createRateSheet`](/graphql-reference/pricing/create-rate-sheet) | mutation | Create a rate sheet |
| [`rateSheet`](/graphql-reference/pricing/rate-sheet) | query | Retrieve a RateSheet |
| [`updateRateSheet`](/graphql-reference/pricing/update-rate-sheet) | mutation | Update a RateSheet |
| [`deleteRateSheet`](/graphql-reference/pricing/delete-rate-sheet) | mutation | Delete a draft rate sheet |
| [`publishRateSheet`](/graphql-reference/pricing/publish-rate-sheet) | mutation | Publish a rate sheet |
| [`simulateRateSheet`](/graphql-reference/pricing/simulate-rate-sheet) | mutation | Simulate prices |
| [`rateSheetVersions`](/graphql-reference/pricing/rate-sheet-versions) | query | List rate sheet versions |
| [`importRateSheet`](/graphql-reference/pricing/import-rate-sheet) | mutation | Import a rate sheet |
| [`rateSheetExport`](/graphql-reference/pricing/rate-sheet-export) | query | Export a rate sheet |
| [`surcharges`](/graphql-reference/pricing/surcharges) | query | List surcharges |
| [`createSurcharge`](/graphql-reference/pricing/create-surcharge) | mutation | Create a surcharge |
| [`surcharge`](/graphql-reference/pricing/surcharge) | query | Retrieve a Surcharge |
| [`updateSurcharge`](/graphql-reference/pricing/update-surcharge) | mutation | Update a Surcharge |
| [`deleteSurcharge`](/graphql-reference/pricing/delete-surcharge) | mutation | Delete a Surcharge |
| [`scheduleSurcharge`](/graphql-reference/pricing/schedule-surcharge) | mutation | Add a schedule entry |
| [`pricingRules`](/graphql-reference/pricing/pricing-rules) | query | List pricing rules |
| [`createPricingRule`](/graphql-reference/pricing/create-pricing-rule) | mutation | Create a pricing rule |
| [`pricingRule`](/graphql-reference/pricing/pricing-rule) | query | Retrieve a PricingRule |
| [`updatePricingRule`](/graphql-reference/pricing/update-pricing-rule) | mutation | Update a PricingRule |
| [`deletePricingRule`](/graphql-reference/pricing/delete-pricing-rule) | mutation | Delete a PricingRule |

## Products

| Field | Kind | What it does |
|---|---|---|
| [`products`](/graphql-reference/products/products) | query | List products |
| [`createProduct`](/graphql-reference/products/create-product) | mutation | Create a product |
| [`searchProducts`](/graphql-reference/products/search-products) | query | Search products |
| [`product`](/graphql-reference/products/product) | query | Retrieve a Product |
| [`updateProduct`](/graphql-reference/products/update-product) | mutation | Update a Product |
| [`deleteProduct`](/graphql-reference/products/delete-product) | mutation | Delete an unreferenced product |

## Rates

| Field | Kind | What it does |
|---|---|---|
| [`createRate`](/graphql-reference/rates/create-rate) | mutation | Get live rates |
| [`rateQuote`](/graphql-reference/rates/rate-quote) | query | Retrieve a rate quote |

## Routes

| Field | Kind | What it does |
|---|---|---|
| [`facilities`](/graphql-reference/routes/facilities) | query | List facilities |
| [`createFacility`](/graphql-reference/routes/create-facility) | mutation | Create a facility |
| [`facility`](/graphql-reference/routes/facility) | query | Retrieve a Facility |
| [`updateFacility`](/graphql-reference/routes/update-facility) | mutation | Update a Facility |
| [`deleteFacility`](/graphql-reference/routes/delete-facility) | mutation | Delete a Facility |
| [`routes`](/graphql-reference/routes/routes) | query | List routes |
| [`createRoute`](/graphql-reference/routes/create-route) | mutation | Create a route |
| [`route`](/graphql-reference/routes/route) | query | Retrieve a Route |
| [`updateRoute`](/graphql-reference/routes/update-route) | mutation | Update a Route |
| [`deleteRoute`](/graphql-reference/routes/delete-route) | mutation | Delete a Route |
| [`activateRoute`](/graphql-reference/routes/activate-route) | mutation | Activate a route |
| [`deactivateRoute`](/graphql-reference/routes/deactivate-route) | mutation | Deactivate a route |
| [`createRouteStop`](/graphql-reference/routes/create-route-stop) | mutation | Insert a stop |
| [`updateRouteStop`](/graphql-reference/routes/update-route-stop) | mutation | Update a stop |
| [`deleteRouteStop`](/graphql-reference/routes/delete-route-stop) | mutation | Remove a stop |
| [`reorderRouteStop`](/graphql-reference/routes/reorder-route-stop) | mutation | Reorder stops |
| [`routeLegs`](/graphql-reference/routes/route-legs) | query | List legs |
| [`updateRouteLeg`](/graphql-reference/routes/update-route-leg) | mutation | Update a leg |
| [`routeRuns`](/graphql-reference/routes/route-runs) | query | List route runs |
| [`createRouteRun`](/graphql-reference/routes/create-route-run) | mutation | Create a route run |
| [`routeRun`](/graphql-reference/routes/route-run) | query | Retrieve a RouteRun |
| [`updateRouteRun`](/graphql-reference/routes/update-route-run) | mutation | Update a RouteRun |
| [`dispatchRouteRun`](/graphql-reference/routes/dispatch-route-run) | mutation | Dispatch a route run |
| [`startRouteRun`](/graphql-reference/routes/start-route-run) | mutation | Start a route run |
| [`completeRouteRun`](/graphql-reference/routes/complete-route-run) | mutation | Complete a route run |
| [`cancelRouteRun`](/graphql-reference/routes/cancel-route-run) | mutation | Cancel a route run |
| [`assignRouteRun`](/graphql-reference/routes/assign-route-run) | mutation | Assign a route run |
| [`unassignRouteRun`](/graphql-reference/routes/unassign-route-run) | mutation | Unassign a route run |
| [`optimizeRouteRun`](/graphql-reference/routes/optimize-route-run) | mutation | Optimize a route run |
| [`arriveRouteRunStop`](/graphql-reference/routes/arrive-route-run-stop) | mutation | Stop: arrive |
| [`completeRouteRunStop`](/graphql-reference/routes/complete-route-run-stop) | mutation | Stop: complete |
| [`failRouteRunStop`](/graphql-reference/routes/fail-route-run-stop) | mutation | Stop: fail |
| [`skipRouteRunStop`](/graphql-reference/routes/skip-route-run-stop) | mutation | Stop: skip |
| [`departRouteRunLeg`](/graphql-reference/routes/depart-route-run-leg) | mutation | Leg: depart |
| [`arriveRouteRunLeg`](/graphql-reference/routes/arrive-route-run-leg) | mutation | Leg: arrive |
| [`replanShipmentJourney`](/graphql-reference/routes/replan-shipment-journey) | mutation | Replan a journey |

## Shipments

| Field | Kind | What it does |
|---|---|---|
| [`shipments`](/graphql-reference/shipments/shipments) | query | List shipments |
| [`createShipment`](/graphql-reference/shipments/create-shipment) | mutation | Create a shipment (draft, or purchase with `purchase: true`) |
| [`searchShipments`](/graphql-reference/shipments/search-shipments) | query | Search shipments |
| [`shipment`](/graphql-reference/shipments/shipment) | query | Retrieve a Shipment |
| [`updateShipment`](/graphql-reference/shipments/update-shipment) | mutation | Update a Shipment |
| [`deleteShipment`](/graphql-reference/shipments/delete-shipment) | mutation | Delete a draft shipment |

## Templates

| Field | Kind | What it does |
|---|---|---|
| [`documents`](/graphql-reference/templates/documents) | query | List documents |
| [`document`](/graphql-reference/templates/document) | query | Retrieve a Document |
| [`deleteDocument`](/graphql-reference/templates/delete-document) | mutation | Delete a standalone document |
| [`documentJobs`](/graphql-reference/templates/document-jobs) | query | List document jobs |
| [`createDocumentJob`](/graphql-reference/templates/create-document-job) | mutation | Create a document job |
| [`documentJob`](/graphql-reference/templates/document-job) | query | Retrieve a DocumentJob |
| [`labelSpecs`](/graphql-reference/templates/label-specs) | query | List label specs |
| [`labelSpec`](/graphql-reference/templates/label-spec) | query | Retrieve a LabelSpec |
| [`documentIngestions`](/graphql-reference/templates/document-ingestions) | query | List document ingestions |
| [`documentIngestion`](/graphql-reference/templates/document-ingestion) | query | Retrieve a DocumentIngestion |
| [`documentTemplates`](/graphql-reference/templates/document-templates) | query | List document templates |
| [`createDocumentTemplate`](/graphql-reference/templates/create-document-template) | mutation | Create a document template |
| [`documentTemplate`](/graphql-reference/templates/document-template) | query | Retrieve a DocumentTemplate |
| [`updateDocumentTemplate`](/graphql-reference/templates/update-document-template) | mutation | Update a DocumentTemplate |
| [`deleteDocumentTemplate`](/graphql-reference/templates/delete-document-template) | mutation | Delete a draft template |
| [`publishDocumentTemplate`](/graphql-reference/templates/publish-document-template) | mutation | Publish a template |
| [`previewDocumentTemplate`](/graphql-reference/templates/preview-document-template) | mutation | Preview a template |
| [`validateDocumentTemplate`](/graphql-reference/templates/validate-document-template) | mutation | Validate a template |
| [`documentTemplateVersions`](/graphql-reference/templates/document-template-versions) | query | List template versions |
| [`createLabelSpec`](/graphql-reference/templates/create-label-spec) | mutation | Create a label spec |
| [`updateLabelSpec`](/graphql-reference/templates/update-label-spec) | mutation | Update a LabelSpec |
| [`publishLabelSpec`](/graphql-reference/templates/publish-label-spec) | mutation | Publish a label spec |

## Tracking

| Field | Kind | What it does |
|---|---|---|
| [`trackers`](/graphql-reference/tracking/trackers) | query | List trackers |
| [`createTracker`](/graphql-reference/tracking/create-tracker) | mutation | Create a tracker |
| [`searchTrackers`](/graphql-reference/tracking/search-trackers) | query | Search trackers |
| [`tracker`](/graphql-reference/tracking/tracker) | query | Retrieve a Tracker |
| [`updateTracker`](/graphql-reference/tracking/update-tracker) | mutation | Update a Tracker |
| [`deleteTracker`](/graphql-reference/tracking/delete-tracker) | mutation | Discard a tracker |

## Trade

| Field | Kind | What it does |
|---|---|---|
| [`classifications`](/graphql-reference/trade/classifications) | query | List classifications |
| [`createClassification`](/graphql-reference/trade/create-classification) | mutation | Classify items |
| [`classification`](/graphql-reference/trade/classification) | query | Retrieve a Classification |
| [`complianceScreenings`](/graphql-reference/trade/compliance-screenings) | query | List compliance screenings |
| [`createComplianceScreening`](/graphql-reference/trade/create-compliance-screening) | mutation | Screen parties and goods |
| [`complianceScreening`](/graphql-reference/trade/compliance-screening) | query | Retrieve a ComplianceScreening |
| [`landedCosts`](/graphql-reference/trade/landed-costs) | query | List landed costs |
| [`createLandedCost`](/graphql-reference/trade/create-landed-cost) | mutation | Quote landed cost |
| [`landedCost`](/graphql-reference/trade/landed-cost) | query | Retrieve a LandedCost |
| [`tariff`](/graphql-reference/trade/tariff) | query | Look up a tariff line |
| [`dutyCollections`](/graphql-reference/trade/duty-collections) | query | List duty collections |
| [`dutyCollection`](/graphql-reference/trade/duty-collection) | query | Retrieve a DutyCollection |

## Webhooks

| Field | Kind | What it does |
|---|---|---|
| [`webhookEndpoints`](/graphql-reference/webhooks/webhook-endpoints) | query | List webhook endpoints |
| [`createWebhookEndpoint`](/graphql-reference/webhooks/create-webhook-endpoint) | mutation | Create a webhook endpoint |
| [`webhookEndpoint`](/graphql-reference/webhooks/webhook-endpoint) | query | Retrieve a WebhookEndpoint |
| [`updateWebhookEndpoint`](/graphql-reference/webhooks/update-webhook-endpoint) | mutation | Update a WebhookEndpoint |
| [`deleteWebhookEndpoint`](/graphql-reference/webhooks/delete-webhook-endpoint) | mutation | Delete a WebhookEndpoint |
