---
title: "Shared objects"
description: "Reusable value objects that are not logistics-specific: money, measurements, contacts and addresses, recurrence, area, messages, metadata, files and documents."
---

These value objects appear across every module. None of them is specific to logistics, so any domain built on this platform can reuse them unchanged.

| Object | Used for | Defined |
|---|---|---|
| [Money](#money) | Every amount | Here |
| [Measurements](#measurements) | Weight, dimensions, distance, volume, temperature | Here |
| [Contact and Address](#contact-and-address) | Any party, and any place | Here (summary), full rules in [Core objects §1](/spec/01-core-objects) |
| [Recurrence](#recurrence) | Anything that repeats | Here |
| [Area](#area) | Any geographic selection | Here |
| [Messages](#messages) | Non-fatal warnings on any response | Here |
| [Metadata namespaces](#metadata-namespaces) | `user_metadata`, `carrier_metadata`, `system_metadata` on every object | [Conventions §5.1](/spec/00-conventions) |
| [File and Document](#file-and-document) | Stored bytes, and rendered or carrier-issued documents | Here (summary), see [Files](/spec/06-documents) and [Templates](/spec/25-documents-generation) |

## Money

```json
{ "amount": 1299, "currency": "usd" }
```

`amount` is an integer in the currency's **minor unit** (its ISO 4217 exponent), and `currency` is a lowercase ISO 4217 code. Floats are never used for money. JPY has exponent 0, so 1299 means ¥1299. KWD has exponent 3, so 1299 means KWD 1.299.

## Measurements

Every physical quantity carries its unit. Implementers convert, and clients never guess.

| Measurement | Shape | Units |
|---|---|---|
| Weight | `{ value, unit }` | `g`, `kg`, `oz`, `lb` |
| Dimensions | `{ length, width, height, unit }` | `mm`, `cm`, `in` |
| Distance | `{ value, unit }` | `m`, `km`, `mi` |
| Volume | `{ value, unit }` | `l`, `m3`, `ft3` |
| Temperature | `{ value, unit }` | `c`, `f` |
| Speed | `{ value, unit }` | `km/h`, `mph` |

When converting for a counterparty that bills on a rounded value, round **up** to its precision.

## Contact and Address

A **Contact** is a party (a person or an organization) with an optional nested **Address** (a place). Keeping them separate lets each exist alone: a contact with no address, such as a phone line, or an address with no contact, such as a facility.

```json
{ "name": "Grace Hopper", "company": "Navy Research Lab", "email": "grace@example.com", "phone": "+442079460000", "tax_ids": [{ "type": "eori", "value": "GB123456789000" }], "address": { "line1": "Downing St", "street_number": "10", "line2": null, "city": "London", "state": null, "postal_code": "SW1A 2AA", "country": "GB", "residential": true } }
```

`phone` is E.164, `country` is ISO 3166-1 alpha-2, and `state` is an ISO 3166-2 subdivision code. The full field rules, including street-number handling and validation, are in [Core objects §1](/spec/01-core-objects).

## Recurrence

The shared schedule shape for anything that repeats. In logistics it drives pickup schedules (chapter 04 §7), routes (chapter 16), driver shifts (chapter 17), end-of-day close (chapter 05 §7) and job schedules (chapter 27).

```json
{
  "frequency": "weekly",
  "interval": 1,
  "days": ["mon", "wed", "fri"],
  "day_of_month": null,
  "times": ["15:00"],
  "timezone": "America/Toronto",
  "starts_on": "2026-10-12",
  "ends_on": null,
  "count": null,
  "exceptions": ["2026-12-25", "2027-01-01"],
  "additions": [],
  "holiday_calendar": "ca_qc",
  "rrule": null
}
```

| Field | Notes |
|---|---|
| `frequency` | `daily`, `weekly`, `monthly` |
| `interval` | Every N periods, default 1 |
| `days` | For `weekly`: `mon`…`sun`. For `daily`, it restricts to these weekdays, with business days as the default. |
| `day_of_month` | For `monthly`: 1–31, or -1 for the last day |
| `times` | Local `HH:MM` occurrence times in `timezone` |
| `starts_on`, `ends_on`, `count` | Bounds. `ends_on` and `count` are mutually exclusive. |
| `exceptions` | Dates skipped |
| `additions` | Extra one-off dates |
| `holiday_calendar` | A registry ID (`us_federal`, `ca_qc`, `gb_eaw`, `de_by`…). Occurrences on holidays are skipped. |
| `rrule` | An RFC 5545 RRULE, as an alternative for patterns the fields above cannot express. If set, it takes precedence over `frequency`, `interval`, `days` and `day_of_month`. |

Implementers MUST expand recurrences in `timezone`, including across DST changes. A `15:00` occurrence stays at 15:00 local time.

## Area

The shared geography selector. In logistics it backs zones (chapter 14 §5), which rate sheets, service coverage and fleet service areas reference.

```json
{
  "countries": ["US"],
  "subdivisions": ["US-CA", "US-OR"],
  "postal_codes": ["94*", "95000-95999"],
  "cities": [{ "country": "US", "state": "CA", "name": "San Francisco" }],
  "polygons": null,
  "radius": null,
  "exclude": { "postal_codes": ["94128"] }
}
```

- An address matches an area if it matches **any** included selector and **no** excluded selector.
- `postal_codes` supports exact values, `*` prefix wildcards, and inclusive ranges with `-`. Ranges compare postal codes as strings of equal length.
- `polygons` is a GeoJSON `MultiPolygon` for fleet service areas. `radius` is `{ center: { latitude, longitude }, distance: { value, unit: "km" | "mi" } }`. Geometric selectors need geocoded addresses, and implementers that cannot geocode MUST reject areas that use them, with `option_unsupported`.

## Messages

Successful responses MAY carry non-fatal `messages[]`:

```json
{ "level": "warning", "code": "reference_truncated", "message": "Reference truncated to 30 characters.", "param": "reference" }
```

`level` is `info` or `warning`. Errors are never messages.

## Metadata namespaces

Every object carries `user_metadata` (written by the client), `carrier_metadata` (written by an external provider, read-only and unversioned) and `system_metadata` (written by the implementer, for provenance). See [Conventions §5.1](/spec/00-conventions).

## File and Document

- A **file** (`file_`) is stored bytes with a purpose, a content type, a size and a SHA-256 hash. It is uploaded as multipart or base64 JSON. See [Files](/spec/06-documents).
- A **document** (`doc_`) is a rendered or provider-issued artifact attached to an object: a type, a format, a short-lived signed `url` or inline `data`, and, when it was rendered from a template, `template` and `template_version`. See [Templates & generation](/spec/25-documents-generation).
