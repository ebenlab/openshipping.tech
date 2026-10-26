---
title: "Appendix B: Standards mapping"
description: "How the spec's objects map to GS1 (SSCC, GTIN, GLN, EPCIS 2.0), IATA (ONE Record, ULD, AWB), DCSA, UPU, ISO 6346, UN/LOCODE, WCO and W3C standards."
---

The spec does not replace the standards each sector already runs on. It gives them one canonical home. Implementers map to and from these standards at their edges, which is how a parcel API, an airline's ONE Record server, an ocean carrier's DCSA endpoints and a postal operator's EDI can describe the same consignment without losing information.

The mappings below are **informative**. Where a standard is normative for a sector (IATA for air cargo, UPU for posts), the spec's object carries that standard's identifiers verbatim in `identifiers` or `carrier_metadata`, and never renames them.

## 1. Identifiers

| Thing | Standard identifier | Spec field |
|---|---|---|
| Logistics unit (pallet, gaylord, carton) | GS1 SSCC (18 digits) | `handling_unit.tracking_number`, `consolidation.identifiers.sscc` |
| Trade item | GS1 GTIN | `product.barcodes[type=gtin13\|gtin14]` |
| Location or party | GS1 GLN | `facility.codes.gln`, `participant` credentials |
| Air waybill | IATA AWB (3-digit prefix + 8 digits) | `legs[].air.awb_prefix` plus the shipment's air waybill document, and `carrier_metadata.awb` |
| ULD | IATA ULD ID (type + serial + owner, e.g. `AKE12345SW`) | `consolidation.identifiers.uld_id` |
| Container | ISO 6346 (owner + category + serial + check digit) | `consolidation.identifiers.container_number` |
| Container size and type | ISO 6346 size-type code (`45G1`) | `consolidation.type_code` |
| Vessel | IMO number, MMSI | `vehicle.class.imo_number`, `conveyance.identifiers.imo_number` |
| Aircraft type | ICAO type designator | `vehicle.class.icao_type` |
| Airline | IATA and ICAO airline codes | `account.carrier.codes`, `vehicle.class.operator_codes` |
| Postal item | UPU S10 (e.g. `RR123456785GB`) | `handling_unit.tracking_number` |
| Postal receptacle | UPU S9 receptacle ID | `consolidation.identifiers.postal_receptacle` |
| Location (port, airport, city) | UN/LOCODE | `facility.codes.unlocode`, `conveyance.departure.unlocode` |
| Country and subdivision | ISO 3166-1 and 3166-2 | `address.country`, `address.state` |
| Currency | ISO 4217 | `Money.currency` |
| Commodity classification | WCO Harmonized System (6-digit) plus national extensions | `item.export_hs_code`, `item.import_hs_code`, `product.hs_codes` |
| Dangerous goods | UN number, IATA DGR / ADR / IMDG class | `dangerous_goods.un_number`, `.class` |
| Organization identity | W3C DID | `participant.did` |
| Qualifications | W3C Verifiable Credentials | `participant.credentials` |

## 2. GS1 EPCIS 2.0 (events)

EPCIS is the closest existing standard to the spec's event model. Device and route-run events map directly:

| EPCIS | Spec |
|---|---|
| `ObjectEvent` (action `OBSERVE`) | `device_event` with `type: "scan"` → `tracking_event` |
| `AggregationEvent` (action `ADD`, `DELETE`) | `device_event` with `action: "aggregate"` / `"disaggregate"` → `consolidation` add and remove |
| `TransactionEvent` | Shipment purchase, injection acceptance |
| `bizStep` (`shipping`, `receiving`, `loading`, `departing`, `arriving`) | `tracking_event.status_detail` (`departed_facility`, `arrived_at_facility`…) |
| `readPoint`, `bizLocation` | `tracking_event.location.facility` (GLN) |
| `sensorElementList` | `device_event` with `type: "sensor"`, with `readings` |

Implementers with capability `interop.epcis` expose `GET /v1/epcis/events` (EPCIS 2.0 JSON-LD) and accept `POST /v1/epcis/capture`, so EPCIS repositories can subscribe without custom mapping.

## 3. IATA ONE Record (air cargo)

ONE Record is IATA's linked-data model and API for air cargo. Mapping:

| ONE Record | Spec |
|---|---|
| `Shipment` | `shipment` |
| `Piece` | `handling_unit` |
| `Item`, `Product` | `item`, `product` |
| `ULD` | `consolidation` with `type: "uld"` |
| `TransportMovement` | `conveyance` with `mode: "air"` |
| `LogisticsEvent` | `tracking_event` |
| `Waybill` (master and house) | Shipment documents with `type: "air_waybill"`, and their consolidation relationship |
| `Organization`, `Location` | `participant` and `account`, `facility` |
| Access delegation and subscriptions | `access_grant` and webhooks / data network feed (chapter 23) |

An airline member of a network (chapter 21) can run its ONE Record server alongside, with the implementer synchronizing through its adapter layer. Both models are object-centric and URI-addressable, which keeps the mapping lossless.

## 4. DCSA (ocean)

| DCSA | Spec |
|---|---|
| Booking | `shipment` with an ocean service |
| Transport Document (eBL) | Shipment document of type `bill_of_lading` |
| Track & Trace `ShipmentEvent`, `TransportEvent`, `EquipmentEvent` | `tracking_event` on shipments, `conveyance` status, and `consolidation` (container) events |
| Equipment | `consolidation` with `type: "container"` |
| Vessel schedule, port call | `route` with `mode: sea` legs and recurrence, plus `conveyance` |

## 5. UPU (postal)

| UPU | Spec |
|---|---|
| ITMATT (item attributes, pre-advice) | `shipment` with `customs_declaration`, sent per item before arrival |
| PREDES / RESDES (despatch and receptacle) | `consolidation` (`sack`) contents, plus `conveyance` |
| EMSEVT (event messages) | `tracking_event` |
| CN22 / CN23 | Shipment document of type `customs_declaration` |

## 6. Trade and customs

| Standard | Spec |
|---|---|
| WCO Data Model | `customs_declaration`, `order.invoice`, `items` |
| EU ICS2 (Import Control System 2) pre-loading data | Per-`item` descriptions, HS codes (at least 6 digits) and parties, sent before loading via the carrier adapter |
| Incoterms 2020 | `customs_declaration.incoterm` |

## 7. Where the spec goes beyond the standards

Each sector standard covers its own mode. The spec adds what sits between them:

- **One identity for a consignment across modes.** A shipment that flies on ONE Record, sails on DCSA and is delivered by a van fleet stays one `shipment`, with one tracker, one journey and one custody chain.
- **Commercial lifecycle**: rating, purchase, void, settlement. Most event standards stop at movement.
- **Access by role per shipment** (chapter 23), so the same record can be shared safely between parties that each use a different standard.
