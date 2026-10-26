"""Generate spec/C-glossary.md: every term, name and concept in the spec, its definition,
the alternative names used across the industry, and where the spec defines it.

Edit the GLOSSARY data below, then run: python3 tools/build_glossary.py
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (term, spec name, definition, [industry aliases], chapter reference)
GLOSSARY = {
"Parties and accounts": [
 ("Shipper", "`ship_from`, the account owner", "The party sending goods. On the label it is the sender, and commercially it is usually the merchant.", ["merchant", "consignor", "sender", "seller", "shipping customer"], "01 §1"),
 ("Consignee", "`ship_to`", "The party receiving goods at the destination.", ["recipient", "receiver", "ship-to", "addressee", "end customer"], "01 §1"),
 ("Return-to", "`return_to`", "Where undeliverable or returned goods go. It defaults to the shipper.", ["return address", "RTO address"], "01 §1"),
 ("Bill-to", "`bill_to` + `billing`", "The party a carrier invoices for transport, and which account pays (sender, recipient, third party).", ["payor", "payer", "bill shipping to", "third-party billing", "freight collect", "receiver pays"], "01 §1.1"),
 ("Importer of record", "`customs_declaration.importer_of_record`", "The party legally responsible for an import: duties, taxes and compliance.", ["IOR", "consignee of record", "declarant (import)"], "01 §5"),
 ("Exporter of record", "`customs_declaration.exporter_of_record`", "The party legally responsible for an export.", ["EOR", "USPPI (US)", "declarant (export)"], "01 §5"),
 ("Import broker", "`customs_declaration.import_broker`", "A licensed customs broker that files the import entry and pays duties on the importer's behalf.", ["customs broker", "customs agent", "clearing agent", "customs house broker"], "01 §5, 13"),
 ("Export broker", "`customs_declaration.export_broker`", "A forwarder or filing agent that submits the export declaration.", ["filing agent", "export agent", "AES filer"], "01 §5"),
 ("IOR / EOR provider", "party acting as importer or exporter of record", "A service that acts as importer or exporter of record for sellers with no local entity.", ["non-resident importer service", "IOR service", "EOR service"], "Architecture §5"),
 ("EU responsible person", "`customs_declaration.eu_responsible_person`", "The EU economic operator required under the General Product Safety Regulation for consumer goods.", ["GPSR contact", "EU representative", "economic operator"], "01 §5"),
 ("Carrier", "`carrier` / `integration` with interface `lsp`", "A company that moves goods for others under its own services.", ["courier", "logistics service provider (LSP)", "operator", "transport provider", "postal operator", "express integrator"], "09, 26"),
 ("Logistics service provider", "carrier account, network member", "Any provider of logistics services: carrying, forwarding, warehousing or last-mile delivery.", ["LSP", "logistics provider", "transport service provider"], "21"),
 ("Third-party logistics provider", "mode `3pl`", "Stores, fulfils and ships goods for merchants, often subcontracting transport.", ["3PL", "fulfillment provider", "contract logistics", "fulfillment center operator"], "12, 18, 29"),
 ("Freight forwarder", "carrier kind `freight_forwarder`", "Arranges multi-modal transport and customs, typically buying line-haul from airlines, ocean and road carriers.", ["forwarder", "NVOCC (ocean)", "consolidator", "freight agent"], "21"),
 ("Consolidator", "carrier kind `consolidator`", "Groups many shipments into larger units (gaylords, ULDs, containers) to buy line-haul at volume.", ["groupage operator", "aggregator (freight)", "co-loader"], "24"),
 ("Carrier network", "mode `network`", "A venue where many carriers publish services and tariffs, and shippers buy composed journeys across them.", ["carrier alliance", "logistics marketplace", "postal union", "consortium", "partner network"], "21"),
 ("Network member", "account `type: carrier`", "A carrier or LSP account inside a network that owns its catalog, pricing and routes.", ["member carrier", "partner carrier", "affiliate"], "21 §1"),
 ("Fleet operator", "mode `fleet`", "Runs its own vehicles: vans, trucks, aircraft, drones or vessels.", ["courier fleet", "delivery operator", "DSP (delivery service partner)", "haulier"], "17"),
 ("Platform", "account `type: platform`", "Software that acts for many merchants: e-commerce platforms, OMSs, marketplaces, shipping platforms.", ["e-commerce platform", "OMS", "marketplace", "multi-carrier platform", "shipping software"], "19"),
 ("Account", "`account` (`acct_`)", "A tenant: the business that owns data in the API.", ["organization", "tenant", "workspace", "customer account", "merchant account"], "19 §1"),
 ("Connection", "`connection` (`conn_`)", "A usable account at a provider, authenticated by credentials or OAuth.", ["carrier account", "carrier credentials", "shipper account", "account number linkage", "carrier integration"], "09 §3"),
 ("Integration", "`integration`", "A catalog entry for any external provider, with the interfaces it implements.", ["connector", "plugin", "provider", "adapter"], "26 §1"),
 ("App", "`app` (`app_`)", "An OAuth or OIDC client registration with a provider.", ["OAuth client", "developer app", "API client", "client credentials"], "09 §4"),
 ("Participant", "`participant` (`ptc_`)", "A party identified by a DID in the data network.", ["network participant", "node participant", "DID holder"], "23 §2"),
 ("Identity provider", "`identity_provider` (`idp_`)", "A customer's OpenID Connect or SAML provider, trusted for sign-in.", ["IdP", "SSO provider", "directory"], "19 §2"),
],
"Goods and physical units": [
 ("Shipment", "`shipment` (`shp_`)", "Moving handling units from one party to another with one carrier service. Buying it produces the label.", ["consignment", "parcel shipment", "booking", "waybill", "freight shipment", "item (postal)"], "03"),
 ("Handling unit", "`handling_units[]` (`hu_`)", "Anything that gets its own label: a parcel, envelope, pallet, crate, ULD or container.", ["parcel", "package", "piece", "carton", "colis", "logistic unit", "pallet", "box"], "01 §2"),
 ("Item", "`handling_units[].items[]`", "One line of goods inside a handling unit, with its customs and dangerous-goods data.", ["commodity", "line item", "article", "goods", "content line", "customs line"], "01 §3"),
 ("Product", "`product` (`prod_`)", "A reusable commodity master record that items reference.", ["SKU", "article master", "item master", "catalog item", "variant"], "20"),
 ("Order", "`order`", "The commercial sale behind a shipment: totals, buyer-paid shipping, invoice.", ["sales order", "customer order", "purchase order (buyer view)"], "01 §4"),
 ("Consolidation", "`consolidation` (`csl_`)", "A transport unit containing handling units or other consolidations.", ["bag", "sack", "receptacle", "gaylord", "cage", "tote", "master pack", "container", "ULD", "trailer load"], "24"),
 ("Gaylord", "`consolidation` `type: gaylord`", "A pallet-sized bulk box used to consolidate parcels.", ["bulk box", "bulk bin", "octabin", "pallet box"], "24 §6"),
 ("ULD", "`consolidation` `type: uld`", "An aircraft unit load device: an air cargo container or pallet.", ["unit load device", "air container", "AKE / LD3", "PMC pallet"], "24, B"),
 ("Container", "`consolidation` `type: container`", "An ISO intermodal container identified by ISO 6346.", ["box (ocean)", "TEU / FEU", "equipment (DCSA)", "intermodal unit"], "24, B"),
 ("Conveyance", "`conveyance` (`cnv_`)", "One departure of one vehicle carrying consolidations.", ["flight", "voyage", "sailing", "trip", "transport movement (ONE Record)", "line-haul run"], "24 §4"),
 ("Facility", "`facility` (`fac_`)", "A physical place in the network with declared functions.", ["hub", "depot", "terminal", "station", "sort center", "gateway", "warehouse", "distribution center (DC)", "fulfillment center"], "16 §1"),
 ("Access point", "`ship_to.access_point`", "A third-party location where consignees collect parcels.", ["PUDO (pick-up drop-off)", "parcel shop", "locker", "service point", "pickup point", "relay point"], "01 §1"),
 ("Vehicle", "`vehicle` (`veh_`)", "A van, truck, aircraft, drone, vessel or rail car.", ["asset", "unit", "tractor / trailer", "aircraft tail", "craft"], "17 §1"),
 ("Device", "`device` (`dev_`)", "A scanner, sorter, locker, telematics unit, tag or sensor.", ["handheld", "RF gun", "IoT device", "tracker tag", "data logger"], "22 §1"),
 ("Dangerous goods", "`items[].dangerous_goods`", "Hazardous materials regulated for transport (IATA DGR, ADR, IMDG).", ["DG", "hazmat", "HAZ", "dangerous goods (DG) declaration", "lithium batteries"], "01 §3"),
],
"Commercial: rates, services and features": [
 ("Rate", "`rate` (`rate_`)", "The price of one service for one shipment, with its charges and delivery estimate.", ["quote", "price", "shipping rate", "tariff line", "offer"], "02"),
 ("Rate quote", "`rate_quote` (`rq_`)", "An expiring snapshot of all rates for exactly one shipment request.", ["rate request result", "rating response", "quotation", "rate token (Amazon)"], "02 §1"),
 ("Service", "`service`, `carrier_configs.{carrier}.service`", "The carrier product being bought, such as ground, express or international economy.", ["product", "shipping product", "service type", "service code", "mail class (USPS)", "product code (DHL)", "shipping method", "delivery option"], "01 §7, 14 §1"),
 ("Service level", "`service.level`", "A normalized speed class used to compare services across carriers.", ["speed tier", "service tier", "delivery speed", "transit class"], "01 §7"),
 ("Carrier configs", "`carrier_configs`", "The product-and-feature configuration: the service plus standardized and carrier-specific features, per carrier.", ["shipping options", "shipment options", "shipping method configuration", "service options", "additional services", "value-added services"], "01 §6"),
 ("Standardized feature", "`carrier_configs.*` registry keys", "A spec-defined feature with one meaning across carriers, mapped by the implementer to each carrier.", ["option", "additional service", "value-added service (VAS)", "special service", "extra service", "add-on", "accessorial (freight)", "feature"], "01 §6.1"),
 ("Carrier-specific feature", "other `carrier_configs.{carrier}` keys", "A feature only one carrier offers, typed by its published schema.", ["carrier option", "proprietary service", "carrier extension"], "01 §6"),
 ("Signature", "`signature`", "A signature requirement on delivery.", ["signature required", "direct signature", "adult signature", "indirect signature", "signature confirmation"], "01 §6.1"),
 ("Cash on delivery", "`cash_on_delivery`", "The carrier collects payment from the consignee on delivery.", ["COD", "collect on delivery", "Nachnahme"], "01 §6.1"),
 ("Insurance (carrier)", "`insurance`", "The carrier's declared value or liability cover.", ["declared value", "DV", "excess value cover", "carrier liability"], "01 §6.1"),
 ("Coverage (third party)", "`coverage` (`cov_`)", "Insurance from a third-party insurer, bought through the insurance interface.", ["parcel insurance", "shipping protection", "cargo insurance", "shipment insurance"], "26 §5"),
 ("Authority to leave", "`authority_to_leave`", "Permission to deliver without a signature.", ["safe place", "shipper release", "leave without signature", "ATL"], "01 §6.1"),
 ("Billable weight", "`rate.billable_weight`", "The weight the carrier charges for: the greater of actual and dimensional weight, after rounding.", ["chargeable weight", "rated weight", "billed weight"], "15 §1"),
 ("Dimensional weight", "`dimensional_weight`", "A weight derived from volume using a divisor.", ["DIM weight", "volumetric weight", "cubed weight", "dimensional factor"], "14 §1, 15"),
 ("Zone", "`zone` (`zone_`)", "A named geographic area used for coverage, pricing or service areas.", ["rating zone", "shipping zone", "delivery area", "lane (pair of zones)", "postcode zone"], "14 §5"),
 ("Rate sheet", "`rate_sheet` (`rs_`)", "A versioned tariff by service, zone and weight band.", ["tariff", "rate card", "price list", "rate table", "zone chart"], "15 §1"),
 ("Surcharge", "`surcharge` (`sur_`), `Charge.kind`", "A rule adding a charge: fuel, residential, remote area, peak, dangerous goods.", ["accessorial", "supplement", "fee", "extra charge", "add-on charge"], "15 §2"),
 ("Fuel surcharge", "`fuel_surcharge`", "A percentage surcharge indexed to fuel prices, usually changing weekly.", ["FSC", "fuel supplement", "bunker adjustment factor (ocean, BAF)"], "15 §2"),
 ("Pricing rule", "`pricing_rule` (`prule_`)", "A markup, discount or contract override applied on top of a rate.", ["markup", "discount", "negotiated rate", "contract rate", "account rate", "price rule"], "15 §3"),
 ("Landed cost", "`landed_cost` (`lc_`)", "Duties, taxes and fees for an import, optionally guaranteed.", ["duties and taxes", "DDP quote", "total landed cost (TLC)", "import charges"], "13 §4"),
 ("Label", "`documents[type=label]`", "The printed document identifying a handling unit to the carrier.", ["shipping label", "waybill label", "AWB label", "address label", "routing label"], "01 §10, 03"),
 ("Purchase", "`purchase` instruction, `POST /v1/shipments/{id}/purchase`", "Buying the label, which commits the carrier service.", ["buy label", "book", "ship", "create shipment", "confirm shipment", "process shipment"], "03 §2"),
 ("Void", "`POST /v1/shipments/{id}/void`", "Cancelling a purchased label, with any refund.", ["cancel label", "delete shipment", "cancel shipment", "label refund", "void shipment"], "03 §5"),
 ("Return shipment", "`returns`, `POST /v1/shipments/{id}/return`", "A shipment moving goods back from the consignee.", ["return label", "RMA shipment", "reverse logistics", "return to vendor"], "03 §6"),
 ("Tracking number", "`tracking.number`, `handling_units[].tracking_number`", "The identifier a carrier uses for a shipment or unit.", ["waybill number", "air waybill (AWB)", "consignment number", "parcel number", "PRO number (LTL)", "item ID", "barcode", "S10 (postal)"], "03, 07"),
 ("Reference", "`reference`, `references` feature", "Shipper text printed on the label and the carrier invoice.", ["customer reference", "PO number", "cost center", "order reference"], "01 §11"),
 ("Incoterm", "`customs_declaration.incoterm`", "The ICC rule that allocates costs and risks between seller and buyer.", ["terms of delivery", "trade terms", "DDP", "DAP", "DDU (legacy)", "EXW"], "01 §5"),
 ("DDP", "`incoterm: DDP`", "Delivered duty paid: the seller pays import duties and taxes.", ["duties paid", "landed", "delivered duty paid"], "13 §4"),
 ("De minimis", "`landed_cost.de_minimis`", "The value threshold below which duties or taxes are not collected.", ["duty-free threshold", "low-value threshold", "Section 321 (US)"], "13 §4"),
],
"Operations": [
 ("Pickup", "`pickup` (`pck_`)", "A collection of handling units from an address within a window.", ["collection", "on-call pickup", "courier collection", "pickup request"], "04"),
 ("Pickup schedule", "`pickup_schedule` (`psch_`)", "A recurring collection, managed by the carrier or booked occurrence by occurrence.", ["regular pickup", "daily pickup", "standing pickup", "scheduled collection"], "04 §7"),
 ("Manifest", "`manifest` (`mfst_`)", "The end-of-day declaration of which labels a carrier should expect.", ["end of day (EOD)", "close-out", "SCAN form (USPS)", "ground close (FedEx)", "bordereau", "transmit (Canada Post)", "despatch", "order summary (Australia Post)", "shipment manifest"], "05"),
 ("Close group", "`handover.close_group`", "A subset of the day's shipments closed together.", ["dock group", "wave", "shipping point", "group ID"], "05 §4"),
 ("Handover", "`handover`", "How goods leave the shipper: pickup, drop-off, manifest.", ["tender", "induction", "drop-off", "dispatch"], "03 §1"),
 ("Injection", "`shipment.injection`", "Handing shipments from one network to another for onward movement.", ["induction", "tender to partner", "zone skipping", "partner handoff", "hand-over to last mile"], "18"),
 ("Advance shipping notice", "`asn` (`asn_`)", "An announcement of a physical delivery of goods to a facility.", ["ASN", "pre-alert", "despatch advice", "inbound notice", "delivery notification"], "18 §4"),
 ("Receiving", "`POST /v1/asns/{id}/receive`, `receive` movements", "Scanning goods in at a facility and reconciling against what was announced.", ["check-in", "inbound scan", "goods receipt", "arrival scan"], "18 §4, 29"),
 ("Interline", "`interline_agreement` (`ila_`)", "An agreement letting one carrier hand shipments to another.", ["handoff agreement", "codeshare (air)", "partner agreement", "through-booking"], "21 §3"),
 ("Mile segments", "`carrier.segments`, journey segment types", "The relay stages of a journey: first, middle and last mile, or end to end.", ["first mile", "middle mile", "line haul", "last mile", "final mile", "pickup and delivery (P&D)"], "21 §1, 16 §4"),
 ("Route", "`route` (`rte_`)", "A plan of ordered stops and legs, optionally recurring.", ["lane", "line-haul route", "delivery route", "round", "tour", "milk run"], "16 §2"),
 ("Leg", "`legs[]` (`leg_`)", "The movement between two consecutive stops.", ["segment", "sector (air)", "hop", "trunk"], "16 §2"),
 ("Route run", "`route_run` (`run_`)", "One execution of a route on a date.", ["trip", "tour", "run", "dispatch", "manifest run"], "16 §3"),
 ("Journey", "`journey` (`jrn_`)", "A shipment's path through the network across runs and carriers.", ["itinerary", "routing", "multi-leg route", "transport plan"], "16 §4"),
 ("Sortation", "facility function `sortation`", "Receiving, sorting and dispatching units without storing them.", ["sorting", "sort center operations", "hub operations"], "16 §1"),
 ("Cross-dock", "facility function `cross_dock`", "Moving goods between inbound and outbound without storage.", ["cross-docking", "flow-through", "transloading"], "16 §1"),
 ("Optimization", "`optimization` (`optj_`)", "Planning routes for many jobs across vehicles and drivers.", ["route optimization", "VRP solving", "dispatch planning"], "17 §3"),
 ("Custody", "`GET /v1/shipments/{id}/custody`", "Which unit, consolidation and conveyance currently hold a shipment.", ["chain of custody", "containment", "where-is-it"], "24 §5"),
],
"Tracking and visibility": [
 ("Tracker", "`tracker` (`trk_`)", "Follows one tracking number with one carrier.", ["tracking subscription", "watch", "shipment tracking"], "07"),
 ("Tracking event", "`tracking_event` (`tev_`)", "One lossless carrier or device report about a shipment.", ["scan", "checkpoint", "status update", "event", "activity"], "07 §1"),
 ("Tracking status", "`tracker.status`", "The small canonical status projected from events.", ["delivery status", "shipment status", "status code"], "07 §2"),
 ("Status detail", "`status_detail`", "The reason within a status, such as `customs_hold`.", ["reason code", "exception code", "sub-status"], "07 §2"),
 ("Exception", "`status: exception`", "Something needs attention: a failed attempt, a customs hold, damage.", ["delivery exception", "incident", "NDR (non-delivery report)", "alert"], "07 §2"),
 ("Proof of delivery", "`proof_of_delivery`", "Evidence of delivery: signature, photo, location.", ["POD", "e-POD", "signature capture", "delivery receipt"], "07 §8"),
 ("Milestone", "`timeline.milestones[]`", "A standard journey stage derived from events across parties.", ["key event", "checkpoint (milestone)", "visibility milestone"], "23 §7.2"),
 ("Timeline", "`timeline`", "The end-to-end view of a shipment assembled from every party's records.", ["end-to-end tracking", "shipment visibility", "control tower view"], "23 §7"),
 ("Identifier link", "`identifier_link` (`idl_`)", "A record that two identifiers are the same goods, or one contains the other.", ["cross-reference", "aggregation link", "identifier mapping"], "23 §7.1"),
 ("Device event", "`device_event`", "A scan, sensor, position, geofence or locker event from a device.", ["scan event", "telemetry", "EPCIS event", "IoT event"], "22 §2"),
 ("Condition monitoring", "`handling_units[].conditions`", "Environmental limits checked against sensor readings.", ["cold chain monitoring", "temperature excursion", "shock monitoring"], "22 §3"),
 ("ETA", "`estimated_delivery`, stop `eta`", "The predicted arrival time.", ["estimated time of arrival", "delivery estimate", "promise date"], "07, 17 §4"),
],
"Customs and trade": [
 ("Customs declaration", "`customs_declaration`", "The legal declaration for cross-border goods: parties, incoterm, duties, certification.", ["customs info", "CN22 / CN23", "export declaration", "customs data", "commercial invoice data"], "01 §5"),
 ("Commercial invoice", "document `commercial_invoice`, `order.invoice`", "The seller's invoice used for customs valuation.", ["CI", "customs invoice", "pro forma (for non-sales)"], "01 §4, 06"),
 ("HS code", "`export_hs_code`, `import_hs_code`", "Harmonized System commodity classification, plus national extensions.", ["tariff code", "commodity code", "HTS (US import)", "Schedule B (US export)", "TARIC / CN code (EU)", "harmonized code"], "01 §3"),
 ("Country of origin", "`items[].origin_country`", "Where goods were manufactured.", ["COO", "made in", "origin"], "01 §3"),
 ("EORI", "`tax_ids[type=eori]`", "The EU and UK economic operator registration number.", ["EORI number", "customs ID"], "01 §1"),
 ("IOSS", "`tax_ids[type=ioss]`", "The EU Import One-Stop Shop VAT number for low-value B2C imports.", ["IOSS number", "VAT OSS"], "01 §1, 13"),
 ("Export filing", "`customs_declaration.export_declaration`", "The export declaration reference.", ["EEI / AES (US)", "ITN", "MRN (EU)", "export entry", "EAD"], "01 §5"),
 ("Paperless trade", "`paperless_trade`", "Submitting customs documents electronically.", ["ETD (FedEx)", "PLT (DHL)", "paperless invoice", "electronic trade documents"], "06"),
 ("Document upload", "`document_upload` (`dupl_`)", "A submission of trade documents to a carrier.", ["ETD upload", "electronic trade documents", "customs document submission"], "06 §2"),
 ("Classification", "`classification` (`cls_`)", "Suggesting HS codes for items.", ["HS classification", "tariff classification", "product classification"], "13 §2"),
 ("Compliance screening", "`compliance_screening` (`scr_`)", "Checking parties and goods against sanctions lists and restrictions.", ["denied party screening (DPS)", "restricted party screening (RPS)", "export control check", "sanctions screening"], "13 §3"),
 ("Duty collection", "`duty_collection` (`dcol_`)", "Duties and taxes paid under DDP and collected from the shipper.", ["duty billing", "tax collection", "disbursement"], "13 §6"),
],
"Inventory and fulfillment": [
 ("Stock", "`stock` (`stk_`)", "A quantity of one product at one location, lot and status.", ["inventory", "on-hand", "stock on hand (SOH)", "quantity on hand"], "29 §2"),
 ("Stock movement", "`stock_movement` (`mov_`)", "One append-only change to stock.", ["inventory transaction", "goods movement", "stock transaction"], "29 §3"),
 ("Storage location", "`storage_location` (`loc_`)", "A zone, aisle, rack, shelf or bin holding stock.", ["bin", "slot", "location", "pick face", "pallet position"], "29 §1"),
 ("Fulfillment order", "`fulfillment_order` (`fo_`)", "A request to ship stock to a customer, through allocation, pick, pack and ship.", ["outbound order", "warehouse order", "pick ticket", "shipment order"], "29 §4"),
 ("Wave", "`wave` (`wave_`)", "A group of orders released for picking together.", ["pick wave", "batch pick", "pick run"], "29 §4"),
 ("Pick list", "document `pick_list`", "The sequenced list of picks for a wave or order.", ["pick sheet", "picking list", "pick ticket"], "29 §4, 25"),
 ("Cycle count", "`inventory_count` (`cnt_`)", "Counting part of the stock and reconciling against expected quantities.", ["stocktake", "physical inventory", "spot count"], "29 §5"),
 ("Lot", "`stock.lot`", "A batch of goods with a manufacture or expiry date.", ["batch", "lot number", "FEFO / FIFO policy"], "29 §2"),
],
"Billing and payments": [
 ("Invoice", "`invoice` (`invc_`)", "A bill for transport, usage, settlement or duties.", ["carrier invoice", "freight bill", "statement", "billing document"], "28 §1"),
 ("Reconciliation", "`reconciliation` (`rcn_`)", "Matching invoice lines to shipments and classifying differences.", ["freight audit", "invoice audit", "parcel audit", "billing reconciliation"], "28 §2"),
 ("Adjustment", "`lines[].kind: adjustment`, `Charge.kind: adjustment`", "A post-shipment change to charges.", ["reweigh", "audit correction", "chargeback", "address correction fee", "billing adjustment"], "28 §2"),
 ("Meter", "`meter` (`mtr_`)", "A definition of something billable, counted from events or reports.", ["billable metric", "usage meter"], "28 §4"),
 ("Usage record", "`usage_record` (`ur_`)", "One occurrence of billable usage.", ["usage event", "billable event", "consumption record"], "28 §4"),
 ("Price plan", "`price_plan` (`plan_`)", "How meters are priced: tiers, per unit, percentage, minimums.", ["pricing plan", "subscription plan", "fee schedule"], "28 §4"),
 ("Balance", "`balance`", "A prepaid amount debited by label purchases.", ["prepaid postage", "postage account", "wallet", "shipping credit"], "28 §5"),
 ("Settlement", "`settlement` (`stl_`)", "Periodic netting of ledger entries between parties.", ["clearing", "netting statement", "revenue share statement"], "21 §5"),
 ("Payment method", "`payment_method` (`pm_`)", "A provider token for a card, bank account or wallet. Never raw card numbers.", ["card on file", "mandate", "payment token"], "28 §6"),
 ("Payout", "`payout` (`po_`)", "Money sent to an account, such as a network member.", ["remittance", "disbursement", "transfer"], "28 §6"),
],
"Platform and API concepts": [
 ("Mode", "`modes`", "A conformance profile: Universal, Carrier, Network, 3PL, Fleet or Data Network.", ["implementer type", "deployment profile"], "12"),
 ("Module", "`modules`", "A unit of functionality an implementer claims, such as `pickups` or `trade`.", ["feature set", "API product"], "12 §1, 11"),
 ("Capability", "`capabilities`", "A finer-grained feature flag, such as `void.partial` or `rates.stream`.", ["feature flag", "supported feature"], "11 §2"),
 ("API surface", "REST `/v1` and GraphQL `/graphql`", "REST for integrators, GraphQL for back-office and LSP administration.", ["public API", "admin API", "dashboard API"], "00 §16, GraphQL Reference"),
 ("Idempotency key", "`Idempotency-Key` header", "A client-chosen key that makes retries safe.", ["request ID (client)", "dedupe key"], "00 §8"),
 ("Webhook endpoint", "`webhook_endpoint` (`we_`)", "A URL that receives signed events.", ["webhook", "callback URL", "notification endpoint", "push subscription"], "08 §3"),
 ("Event", "`event` (`evt_`)", "A record that something changed, delivered to webhooks and listable.", ["notification", "webhook event", "push message"], "08 §1"),
 ("Inbound event", "`inbound_event` (`ibe_`)", "Events entering the API from carriers or clients.", ["carrier push", "event injection", "status feed"], "08 §6–7"),
 ("Federated carrier", "carrier ID `fed_…`", "A carrier or provider implementing this spec, onboarded without adapter code.", ["spec-native carrier", "plug-and-play carrier"], "09 §6"),
 ("Connect session", "`connect_session` (`cs_`)", "The OAuth or OIDC flow that creates a connection.", ["carrier onboarding flow", "account linking", "OAuth handshake"], "09 §5"),
 ("Metadata namespaces", "`user_metadata`, `carrier_metadata`, `system_metadata`", "Client data, provider data and implementer provenance, each with one writer.", ["metadata", "meta", "custom fields", "extra data"], "00 §5.1"),
 ("Job", "`job` (`job_`)", "The envelope for any asynchronous operation.", ["background task", "batch job", "async operation"], "27"),
 ("Batch", "`batch` (`bat_`)", "Many items processed in one asynchronous request.", ["bulk operation", "bulk upload", "mass action"], "10 §7"),
 ("Document template", "`document_template` (`dtpl_`)", "A portable Liquid or ZPL template bound to a canonical object.", ["label template", "print template", "layout", "report template"], "25 §1"),
 ("Label spec", "`label_spec` (`lspec_`)", "A carrier's machine-checkable label rules, with certification.", ["label specification", "label guide", "barcode spec", "label certification"], "25 §6"),
 ("Document ingestion", "`document_ingestion` (`ding_`)", "Turning PDFs, scans or EDI into structured data.", ["document capture", "OCR extraction", "EDI parsing", "IDP"], "25 §7"),
 ("Record", "`record` (`rec_`)", "A signed, content-addressed version of a canonical object in the data network.", ["ledger record", "attested record", "content-addressed object"], "23 §3"),
 ("Anchor", "`anchor` (`anc_`)", "A Merkle root of records written to a ledger.", ["blockchain anchor", "timestamp proof", "notarization"], "23 §3"),
 ("Attestation", "`attestation` (`att_`)", "A signed statement by a participant about a record.", ["sign-off", "certification", "verified claim"], "23 §6"),
 ("Access grant", "`access_grant` (`grt_`), `access_policy`", "Explicit or role-derived permission to read fields of records.", ["data sharing permission", "consent", "ACL"], "23 §4"),
 ("DID", "`participant.did`", "A W3C decentralized identifier for an organization or person.", ["decentralized identifier", "did:web"], "23 §2"),
],
}

ALIASES_EXTRA = {}  # alias -> term, for aliases shared by several terms that should point somewhere specific


def anchor(term):
    return re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")


def build():
    out = ['---', 'title: "Appendix C: Glossary"',
           'description: "Every term, name and concept in the spec, its definition, the names used for it across the industry, and where the spec defines it."',
           '---', '',
           'Logistics uses many names for the same thing, and the same name for different things. A carrier\'s *product* is another\'s *service*. A *manifest* is a SCAN form, a close-out or a bordereau depending on who you ask. This glossary fixes the spec\'s term for each concept, defines it, and lists the names the industry uses for it, so readers can translate in either direction.', '',
           '- **Spec name** is the object, field or endpoint, with its ID prefix.',
           '- **Also called** lists industry names: carrier, ERP, freight, postal and regional usage. Some are near-synonyms rather than exact equivalents, and the definition says what the spec means.',
           '- **Where** points to the chapter and section.', '',
           'The [alias index](#alias-index) at the end maps every alternative name back to its spec term.', '']
    alias_map = {}
    for section, rows in GLOSSARY.items():
        out.append(f"## {section}\n")
        out.append("| Term | Spec name | Definition | Also called | Where |")
        out.append("|---|---|---|---|---|")
        for term, spec, definition, aliases, where in rows:
            out.append(f"| **{term}** | {spec} | {definition} | {', '.join(aliases)} | {where} |")
            for a in aliases:
                alias_map.setdefault(a.lower(), []).append((a, term, section))
        out.append("")
    out.append("## Alias index\n")
    out.append("| Industry name | Spec term |")
    out.append("|---|---|")
    for key in sorted(alias_map):
        entries = alias_map[key]
        name = entries[0][0]
        terms = sorted({t for _, t, _ in entries})
        out.append(f"| {name} | {', '.join('**' + t + '**' for t in terms)} |")
    out.append("")
    text = "\n".join(out)
    (ROOT / "spec" / "C-glossary.md").write_text(text)
    n = sum(len(r) for r in GLOSSARY.values())
    print(f"wrote spec/C-glossary.md: {n} terms, {len(alias_map)} aliases")


if __name__ == "__main__":
    build()
