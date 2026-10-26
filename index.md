---
title: "Open Logistics Specs"
description: "One resource model and one wire format for rates, labels, pickups, manifests, customs documents, tracking, webhooks and carrier connections."
---

**Status:** Draft 0.1 · 2026-10-06 · Editor: Daniel Kobina (Eben Labs)

This is an open specification for a universal, multi-carrier shipping API. Any party can implement it:

| Mode | Implementer | Adds |
|---|---|---|
| **Universal** | Multi-carrier aggregators | Carrier connections and OAuth apps |
| **Carrier** | Parcel carriers and postal operators | Trade engine, service catalog, rate sheets, routes |
| **3PL** | Logistics and fulfillment providers | Trade engine, service catalog, rate sheets, routes, subcontracted legs |
| **Network** | Carrier and LSP networks, marketplaces | Carrier member accounts, composed rates, interline agreements, settlement |
| **Fleet** | Operators of vans, aircraft, drones, vessels | Service catalog, rate sheets, routes, vehicles and drivers, IoT |
| **Data Network** | Logistics data network nodes | Signed, anchored records with field-level access for every participant |

Every mode shares the same core: rates, shipments, pickups, tracking, webhooks, and one object model. Platforms consume it once and reach every implementer. See [Modes](/spec/12-modes).

The API borrows Stripe's conventions on purpose: prefixed IDs, `Idempotency-Key`, cursor pagination, `expand[]`, metadata, dated versions, test and live keys, and signed webhook events.

## Explore

The [Industry Map](/map) shows every party, platform module and canonical object in three views (orbit, journey lanes and matrix), with shipment simulations. It links back into these pages.

## Two audiences

| Audience | Start here |
|---|---|
| **Agents** (LLM agents, MCP clients) | [shipping.md](/shipping), the discovery file an implementer hosts at its domain root, in the same spirit as `auth.md` |
| **Developers** | [Conventions](/spec/00-conventions), then the chapters, then the API Reference tab |

## Normative language

MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as defined in RFC 2119 and RFC 8174.
