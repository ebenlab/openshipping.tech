"""Generate openapi.yaml for the Open Logistics Specs draft 0.1."""
import sys, yaml

R = lambda n: {"$ref": f"#/components/schemas/{n}"}
S = lambda t, **k: {"type": t, **k}
STR = S("string"); INT = S("integer"); BOOL = S("boolean"); NUM = S("number"); TS = S("integer", format="unix-time", description="Unix timestamp (seconds)")
DATE = S("string", format="date")
def arr(x, **k): return {"type": "array", "items": x, **k}
def enum(*v, **k): return {"type": "string", "enum": list(v), **k}
def obj(props, req=None, **k):
    o = {"type": "object", "properties": props, **{a: b for a, b in k.items() if b is not None}}
    if req: o["required"] = req
    return o
def nullable(x): return {"anyOf": [x, {"type": "null"}]}
def idref(prefix, expand=None):
    d = {"type": "string", "description": f"ID ({prefix}...)" + (f". Expandable to `{expand}`." if expand else "")}
    return nullable(d) if expand is None else {"anyOf": [d, R(expand), {"type": "null"}]}

def resource(name, prefix, props, req=None, desc=None):
    base = {
        "id": S("string", description=f"Prefixed `{prefix}`", examples=[f"{prefix}1Q2w3E4r"]),
        "object": enum(name),
        "livemode": BOOL,
        "created": TS,
        "updated": TS,
    }
    base.update(props)
    base.setdefault("user_metadata", R("UserMetadata"))
    base.setdefault("carrier_metadata", R("CarrierMetadata"))
    base.setdefault("system_metadata", R("SystemMetadata"))
    return obj(base, ["id", "object", "livemode", "created"] + (req or []), description=desc)

schemas = {}
def C(name, schema):
    if name in schemas:
        raise SystemExit(f"duplicate schema name: {name}")
    schemas[name] = schema

# ---------- primitives ----------
C("CarrierMetadata", obj({}, additionalProperties=True, readOnly=True,
    description="Read-only. Carrier-returned data not modelled by the spec (routing codes, internal IDs). Untrusted and unversioned; keys may change with the carrier's API."))
C("SystemMetadata", obj({
    "source": enum("api", "dashboard", "batch", "inbound", "automation", "system"),
    "created_by": obj({"type": enum("api_key", "oauth_app", "user", "system"), "id": STR}),
    "request_id": nullable(STR), "idempotency_key": nullable(STR), "batch": nullable(STR), "generated": BOOL, "test_scenario": nullable(STR)},
    additionalProperties=True, readOnly=True, description="Read-only. Implementer provenance. Implementer-specific keys are prefixed x_."))
C("UserMetadata", obj({}, additionalProperties=S("string", maxLength=500), maxProperties=50, description="Client-writable. Up to 50 string key/value pairs. Never sent to carriers."))
C("Money", obj({"amount": S("integer", description="Minor units (ISO 4217 exponent)"), "currency": S("string", pattern="^[a-z]{3}$", examples=["usd"])}, ["amount", "currency"]))
C("Weight", obj({"value": S("number", exclusiveMinimum=0), "unit": enum("g", "kg", "oz", "lb")}, ["value", "unit"]))
C("Dimensions", obj({"length": NUM, "width": NUM, "height": NUM, "unit": enum("mm", "cm", "in")}, ["length", "width", "height", "unit"]))
C("Message", obj({"level": enum("info", "warning"), "code": STR, "message": STR, "param": STR, "carrier": STR}, ["level", "code", "message"]))
C("Messages", arr(R("Message")))
C("TaxId", obj({"type": enum("eori", "vat", "ioss", "voec", "gst", "ein", "ssn_last4", "cpf", "cnpj", "rfc", "abn", "state_tax_id", "other"), "value": STR, "country": STR}, ["type", "value"]))
C("Address", obj({
    "line1": S("string", description="Street. Street name only when street_number is set; otherwise street and number. No city/state/postal code."),
    "street_number": S("string", description="House/building number incl. suffix (10, 221B, 12-14). Recommended for DE, NL, BE, AT, CH, PL, BR."),
    "line2": S("string", description="Apartment, suite, floor, building, c/o"), "city": STR,
    "state": S("string", description="ISO 3166-2 subdivision without country prefix"),
    "postal_code": STR, "country": S("string", pattern="^[A-Z]{2}$"), "residential": nullable(BOOL),
    "validation": nullable(obj({"status": enum("verified", "corrected", "unverified", "invalid"), "suggested": {"$ref": "#/components/schemas/Address"}, "messages": R("Messages")}, readOnly=True)),
}, ["line1", "country"]))
C("Contact", obj({
    "name": STR, "company": STR, "email": S("string", format="email"), "phone": S("string", description="E.164"),
    "tax_ids": arr(R("TaxId")), "address": R("Address"), "instructions": S("string", maxLength=255),
    "access_point": nullable(obj({"carrier": STR, "id": STR, "type": enum("locker", "parcel_shop", "post_office")})),
}, description="A party to a shipment. Either `name` or `company` is required. `address` is required on ship_from, ship_to, return_to, bill_to."))
C("DangerousGoods", obj({
    "class": STR, "un_number": S("string", pattern="^UN[0-9]{4}$"), "proper_shipping_name": STR, "packing_group": nullable(enum("I", "II", "III")),
    "packing_instruction": STR, "section": STR, "quantity": R("Weight"),
    "lithium": nullable(obj({"type": enum("ion", "metal"), "configuration": enum("alone", "packed_with_equipment", "contained_in_equipment"), "watt_hours": NUM, "lithium_grams": NUM, "cells": INT})),
    "accessibility": enum("accessible", "inaccessible"), "transport_mode": enum("air", "ground", "sea"),
    "excepted_quantity": BOOL, "limited_quantity": BOOL,
    "emergency_contact": obj({"name": STR, "phone": STR}), "declaration_document": nullable(STR)}, ["class", "un_number"]))
C("ItemCompliance", obj({
    "controlled": BOOL, "control_type": enum("dual_use", "military", "sanctions", "agricultural", "pharmaceutical", "cites", "other"),
    "eccn": STR, "license": obj({"type": enum("export", "import"), "number": STR, "expires_on": DATE}),
    "regulatory_agency": STR, "regulatory_program": STR, "regulatory_category_code": STR,
    "certification": obj({"type": STR, "reference": STR})}))
HS = S("string", pattern="^[0-9. ]{6,16}$")
C("Item", obj({
    "title": STR, "description": STR, "sku": STR, "quantity": S("integer", minimum=1),
    "unit_value": R("Money"),
    "unit_net_weight": {**R("Weight"), "description": "Weight of one unit of goods, excluding all packaging"},
    "unit_gross_weight": {**R("Weight"), "description": "Weight of one unit including its retail packaging (not the shipping carton); >= unit_net_weight"}, "origin_country": S("string", pattern="^[A-Z]{2}$"),
    "export_hs_code": {**HS, "description": "Origin country's export classification (e.g. US Schedule B)"},
    "import_hs_code": {**HS, "description": "Destination country's import tariff classification (e.g. HTSUS, UK Trade Tariff, TARIC)"},
    "category": STR, "product_url": S("string", format="uri"), "image_url": S("string", format="uri"),
    "product_id": STR, "variant_id": STR, "order_line_id": STR, "brand": STR, "material": STR,
    "manufacturer": obj({"name": STR, "country": STR, "mid": STR}),
    "compliance": nullable(R("ItemCompliance")), "dangerous_goods": nullable(R("DangerousGoods")), "product": nullable(S("string", description="prod_ ID; fills unset fields, snapshotted at purchase")), "user_metadata": R("UserMetadata")},
    ["quantity"]))
C("HandlingUnit", obj({
    "id": S("string", readOnly=True),
    "type": S("string", enum=["parcel", "envelope", "tube", "pallet", "crate", "skid", "drum", "carton", "uld", "container", "other"], default="parcel"),
    "conditions": nullable(obj({"temperature": obj({"min": obj({"value": NUM, "unit": STR}), "max": obj({"value": NUM, "unit": STR})}), "shock": obj({"max": obj({"value": NUM, "unit": STR})}), "tilt": obj({"max_degrees": NUM})})),
    "weight": R("Weight"), "dimensions": R("Dimensions"),
    "packaging": S("string", description="Generic code (your_packaging, envelope, pak, tube, eur_pallet, us_pallet_48x40) or a carrier packaging code"),
    "freight": nullable(obj({"pallet_standard": enum("eur1", "eur2", "us_48x40", "au_1165", "other"), "stackable": BOOL, "piece_count": INT,
                             "freight_class": STR, "nmfc_code": STR, "hazmat_placard": BOOL})),
    "reference": STR, "description": STR, "items": arr(R("Item")), "tracking_number": S("string", readOnly=True), "carrier_metadata": R("CarrierMetadata")}, ["weight"]))
C("OrderInvoice", obj({"number": STR, "date": DATE, "type": enum("commercial", "proforma"),
    "terms_of_payment": enum("prepaid", "collect", "free_of_charge"), "file": nullable(STR)}))
C("Order", obj({
    "id": STR, "reference": STR, "channel": STR, "ordered_at": S("string", format="date-time"), "currency": STR,
    "subtotal": R("Money"), "shipping_charge": R("Money"), "insurance_charge": nullable(R("Money")), "discount": R("Money"),
    "tax": R("Money"), "total": R("Money"), "invoice": nullable(R("OrderInvoice")),
    "buyer": nullable(R("Contact")), "seller": nullable(R("Contact"))}))
C("CustomsDocumentRef", obj({"type": STR, "carrier_reference": STR, "document_upload": STR}, ["type"]))
C("CustomsDeclaration", obj({
    "contents_type": enum("merchandise", "gift", "sample", "documents", "returned_goods", "repair", "personal_effects", "other"),
    "contents_explanation": STR, "incoterm": enum("DAP", "DDP", "DDU", "EXW", "FCA", "CPT", "CIP", "DPU"),
    "duties": obj({"paid_by": enum("sender", "recipient", "third_party"), "account_number": nullable(STR), "bill_to": nullable(R("Contact"))}),
    "landed_cost": nullable(STR), "import_broker": nullable(R("Contact")), "export_broker": nullable(R("Contact")), "importer_of_record": nullable(R("Contact")), "exporter_of_record": nullable(R("Contact")), "eu_responsible_person": nullable(R("Contact")),
    "export_declaration": nullable(obj({"type": enum("itn", "eel_pfc", "mrn", "ead"), "value": STR})),
    "non_delivery": enum("return", "abandon"), "paperless_trade": BOOL, "certify": BOOL, "signer": STR,
    "documents": arr(R("CustomsDocumentRef"))}, ["contents_type"], additionalProperties=False))
C("Billing", obj({"paid_by": S("string", enum=["sender", "recipient", "third_party"], default="sender"), "account_number": nullable(STR)},
    description="Which carrier account pays transportation charges. The party is `bill_to`. Country and postal code for validation come from `bill_to.address`."))
MONEY_INLINE = obj({"amount": INT, "currency": STR}, ["amount", "currency"])
STD_FEATURES = {
    "signature": enum("none", "standard", "indirect", "adult"),
    "age_verification": S("integer", minimum=0),
    "insurance": MONEY_INLINE,
    "cash_on_delivery": obj({"amount": INT, "currency": STR, "method": enum("cash", "check", "any")}, ["amount", "currency"]),
    "saturday_delivery": BOOL, "sunday_delivery": BOOL, "evening_delivery": BOOL,
    "delivery_window": obj({"start": STR, "end": STR}),
    "hold_for_pickup": BOOL, "access_point_delivery": BOOL, "direct_delivery_only": BOOL, "authority_to_leave": BOOL,
    "delivery_confirmation": enum("none", "scan", "photo", "pin"),
    "notifications": obj({"email": BOOL, "sms": BOOL}),
    "dry_ice": obj({"value": NUM, "unit": enum("g", "kg", "oz", "lb")}, ["value", "unit"]),
    "dangerous_goods_service": BOOL, "carbon_neutral": BOOL, "delivery_warranty": BOOL,
    "duty_tax_mode": enum("guaranteed", "collect_from_consignee"),
    "paperless_trade": BOOL, "return_label": BOOL,
    "references": arr(obj({"type": enum("po", "invoice", "department", "customer", "other"), "value": STR}, ["type", "value"])),
    "label_message": S("string", maxLength=60),
}
C("StandardFeatures", obj(dict(STD_FEATURES), additionalProperties=False,
    description="Standardized features (chapter 01 §6.1): one name, type and meaning across carriers; implementers map them to each carrier's native codes and MUST NOT drop them silently."))
C("CarrierConfig", obj({
    "service": S("string", description="The carrier product, e.g. fedex_international_priority"),
    "connection": S("string", description="conn_ ID when the account has several for this carrier"),
    **STD_FEATURES},
    additionalProperties=True,
    description="CarrierConfig<T>: service + connection + standardized features (typed here) + carrier-specific features T "
                "(additional properties, validated against carriers/{id}.shipment_config_schema; standardized names are reserved)."))
C("CarrierConfigs", obj({"*": R("StandardFeatures")}, additionalProperties=R("CarrierConfig"),
    description="Product and feature configuration. '*' applies standardized features to every rated carrier; each other key selects a carrier.",
    examples=[{"*": {"signature": "adult", "insurance": {"amount": 25000, "currency": "usd"}}, "fedex": {"service": "fedex_international_priority", "saturday_delivery": True, "priority_alert": True}, "ups": {}}]))
C("FeatureFulfillment", obj({"value": {}, "carrier_code": nullable(STR), "charge": nullable(R("Money"))}))
C("ServiceLevel", enum("same_day", "overnight", "express", "standard", "economy", "freight", "other"))
C("Service", obj({"carrier": STR, "connection": STR, "code": STR, "name": STR, "level": R("ServiceLevel"), "carrier_code": STR}, ["code"]))
C("Charge", obj({"kind": enum("base", "fuel_surcharge", "residential_surcharge", "remote_area_surcharge", "peak_surcharge", "oversize_surcharge", "dangerous_goods_surcharge", "option", "insurance", "duty", "tax", "customs_fee", "pickup_fee", "discount", "adjustment", "other"),
                 "option": STR, "name": STR, "amount": R("Money"), "carrier_code": STR}, ["kind", "amount"]))
C("DeliveryEstimate", obj({"days": INT, "date": DATE, "window": obj({"start": S("string", format="date-time"), "end": S("string", format="date-time")}), "guaranteed": BOOL, "business_days": BOOL}))
C("LabelFormat", obj({"format": enum("pdf", "png", "zpl", "epl", "gif", "jpg"), "size": STR, "dpi": enum("203", "300"), "inline": BOOL}))
C("Document", obj({"id": STR, "object": enum("document"),
    "type": enum("label", "return_label", "commercial_invoice", "proforma_invoice", "certificate_of_origin", "customs_declaration", "packing_slip", "manifest", "scan_form", "close_report", "cod_report", "dangerous_goods_report", "order_summary", "pickup_confirmation", "dangerous_goods_declaration", "pick_list", "consolidation_label", "bill_of_lading", "cmr", "air_waybill", "delivery_receipt", "insurance_certificate", "invoice", "custom", "other"),
    "format": enum("pdf", "png", "zpl", "epl", "gif", "jpg"), "size": STR, "url": S("string", format="uri"), "url_expires_at": TS,
    "data": nullable(S("string", contentEncoding="base64")), "handling_unit": nullable(STR), "bundle": nullable(arr(STR)), "template": nullable(STR), "template_version": nullable(INT), "related": nullable(obj({"type": STR, "id": STR})), "file": nullable(STR), "sha256": nullable(STR)}, ["id", "object", "type", "format"]))
C("ListMeta", obj({"object": enum("list"), "url": STR, "has_more": BOOL}, ["object", "has_more"]))
C("Deleted", obj({"id": STR, "object": STR, "deleted": enum("true")}, ["id", "object", "deleted"]))

# ---------- error ----------
C("Error", obj({"error": obj({
    "type": enum("invalid_request_error", "authentication_error", "billing_error", "permission_error", "idempotency_error", "state_error", "carrier_error", "rate_limit_error", "carrier_unavailable", "api_error"),
    "code": STR, "message": STR, "param": STR, "doc_url": STR, "request_id": STR,
    "carrier": nullable(obj({"id": STR, "connection": STR, "code": STR, "message": STR})),
    "shipment": nullable(STR),
    "details": arr(obj({"code": STR, "message": STR, "param": STR}, additionalProperties=True))}, ["type", "code", "message"])}, ["error"]))

# ---------- rates ----------
RATE_REQ_PROPS = {
    "ship_from": R("Contact"), "ship_to": R("Contact"), "return_to": R("Contact"),
    "bill_to": R("Contact"), "billing": R("Billing"),
    "handling_units": arr(R("HandlingUnit"), minItems=1, maxItems=99), "order": R("Order"), "customs_declaration": R("CustomsDeclaration"),
    "carrier_configs": R("CarrierConfigs"),
    "ship_date": DATE, "returns": obj({"is_return": BOOL}),
}
C("RateRequest", obj({**RATE_REQ_PROPS,
    "levels": arr(R("ServiceLevel")),
    "currency": STR, "timeout_ms": S("integer", minimum=1000, maximum=30000, default=8000),
    "shipment": STR, "validate_addresses": BOOL, "user_metadata": R("UserMetadata")}, ["ship_from", "ship_to", "handling_units"], additionalProperties=False))
C("Rate", obj({
    "id": STR, "object": enum("rate"), "service": R("Service"), "total": R("Money"), "total_in_account_currency": R("Money"),
    "charges": arr(R("Charge")),
    "landed_cost": nullable(R("LandedCost")),
    "delivery": R("DeliveryEstimate"), "carrier_configs": R("CarrierConfigs"), "features": obj({}, additionalProperties=R("FeatureFulfillment")), "billable_weight": R("Weight"), "zone": STR,
    "pricing": enum("list", "negotiated", "implementer", "retail", "rate_sheet"), "composition": nullable(obj({"segments": arr(obj({"sequence": INT, "segment": enum("first_mile", "middle_mile", "last_mile", "end_to_end"), "carrier": STR, "service": STR, "from": STR, "to": STR, "amount": R("Money")})), "interline_agreements": arr(STR)})), "pricing_details": nullable(R("PricingDetails")), "tags": arr(enum("cheapest", "fastest", "best_value")),
    "documents": obj({"label_formats": arr(STR), "label_sizes": arr(STR)}), "requires": arr(STR),
    "expires_at": TS, "messages": R("Messages"), "carrier_metadata": R("CarrierMetadata")}, ["id", "object", "service", "total", "expires_at"]))
C("ConnectionError", obj({"connection": STR, "carrier": STR, "type": STR, "code": STR, "message": STR}, ["connection", "code", "message"]))
C("RateQuote", resource("rate_quote", "rq_", {
    "expires_at": TS, "shipment": nullable(STR), "request": obj(RATE_REQ_PROPS),
    "rates": arr(R("Rate")), "errors": arr(R("ConnectionError")), "messages": R("Messages")}, ["expires_at", "rates", "errors"]))

# ---------- shipments ----------
SHIP_STATUS = enum("draft", "purchasing", "purchase_failed", "purchased", "manifested", "void_pending", "voided", "void_failed")
TRACK_STATUS = enum("pre_transit", "in_transit", "out_for_delivery", "available_for_pickup", "delivered", "exception", "return_to_sender", "returned", "cancelled", "unknown")
C("ShipmentStatus", SHIP_STATUS); C("TrackingStatus", TRACK_STATUS)
C("Void", obj({"requested_at": TS, "reason": STR, "status": enum("pending", "succeeded", "failed"),
    "refund": obj({"status": enum("not_applicable", "pending", "refunded", "partially_refunded", "rejected"), "amount": R("Money"), "expected_by": DATE}),
    "carrier_reference": STR}))
LABEL_SPEC = R("LabelFormat")
C("ShipmentPurchaseInfo", obj({
    "rate": idref("rate_", "Rate"), "rate_quote": idref("rq_", "RateQuote"), "service": nullable(R("Service")),
    "amount": nullable(R("Money")), "charges": arr(R("Charge")), "delivery": nullable(R("DeliveryEstimate")),
    "label_format": R("LabelFormat"), "purchased_at": nullable(TS), "error": nullable(obj({}, additionalProperties=True)), "void": nullable(R("Void")), "coverage": nullable(STR)},
    readOnly=True, description="What was bought and its commercial outcome. Null until the first purchase attempt."))
C("ShipmentTracking", obj({"status": nullable(R("TrackingStatus")), "number": nullable(STR), "url": nullable(STR),
    "tracker": idref("trk_", "Tracker"), "journey": idref("jrn_", "Journey")}, readOnly=True))
C("ShipmentHandover", obj({"close_group": nullable(STR), "pickup": idref("pck_", "Pickup"), "manifest": idref("mfst_", "Manifest")}))
C("ShipmentReturns", obj({"is_return": BOOL, "outbound_shipment": idref("shp_", "Shipment"), "return_shipment": idref("shp_", "Shipment")}))
C("Shipment", resource("shipment", "shp_", {
    "status": R("ShipmentStatus"), "reference": nullable(STR), "ship_date": DATE,
    "ship_from": R("Contact"), "ship_to": R("Contact"), "return_to": R("Contact"), "bill_to": nullable(R("Contact")), "billing": R("Billing"),
    "handling_units": arr(R("HandlingUnit")), "order": nullable(R("Order")), "customs_declaration": nullable(R("CustomsDeclaration")),
    "carrier_configs": R("CarrierConfigs"),
    "purchase": nullable(R("ShipmentPurchaseInfo")), "tracking": R("ShipmentTracking"), "handover": R("ShipmentHandover"), "injection": nullable(R("Injection")), "returns": R("ShipmentReturns"),
    "documents": arr(R("Document")), "messages": R("Messages")}, ["status"]))
C("PurchaseInstruction", obj({"rate": STR, "label_format": R("LabelFormat"), "max_increase": R("Money"), "coverage": obj({"quote": STR})}, additionalProperties=False,
    description="Presence means: buy the label now (Idempotency-Key required)."))
SHIP_INPUT = {k: v for k, v in RATE_REQ_PROPS.items() if k != "returns"}
C("ShipmentCreate", obj({**SHIP_INPUT, "reference": S("string", maxLength=35),
    "handover": obj({"close_group": STR}), "returns": obj({"is_return": BOOL, "include_return_label": BOOL}),
    "purchase": R("PurchaseInstruction"), "injection": R("InjectionInput"), "user_metadata": R("UserMetadata")}, additionalProperties=False,
    description="Either `purchase.rate` (shipment built from the quote); or shipment fields + `purchase` with exactly one `carrier_configs` entry that has a `service`; or shipment fields only (draft)."))
C("ShipmentUpdate", obj({**SHIP_INPUT, "reference": STR, "handover": obj({"close_group": STR}), "returns": obj({"is_return": BOOL, "include_return_label": BOOL}),
    "user_metadata": R("UserMetadata"), "redact": BOOL}, additionalProperties=False))
C("ShipmentPurchase", obj({"rate": STR, "label_format": R("LabelFormat"), "max_increase": R("Money")}, additionalProperties=False))
C("ShipmentVoid", obj({"reason": enum("customer_cancelled", "duplicate", "wrong_address", "wrong_service", "damaged_label", "other"), "handling_units": nullable(arr(STR))}, additionalProperties=False))
C("ShipmentReturn", obj({"carrier_configs": R("CarrierConfigs"), "handling_units": arr(R("HandlingUnit")), "bill_to": R("Contact"), "billing": R("Billing"), "purchase": R("PurchaseInstruction"), "delivery_method": enum("label", "qr_code", "email", "pickup"), "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("RateFilters", obj({"carrier_configs": R("CarrierConfigs"), "levels": arr(R("ServiceLevel")), "timeout_ms": INT}, additionalProperties=False))

# ---------- pickups ----------
C("PickupWindow", obj({"ready_at": S("string", pattern="^[0-2][0-9]:[0-5][0-9]$"), "close_at": S("string", pattern="^[0-2][0-9]:[0-5][0-9]$")}, ["ready_at", "close_at"]))
LOC = enum("front_door", "back_door", "side_door", "front_desk", "reception", "mailroom", "loading_dock", "garage", "other")
C("Pickup", resource("pickup", "pck_", {
    "status": enum("scheduled", "rescheduled", "completed", "missed", "cancelled", "failed"),
    "connection": STR, "carrier": STR, "confirmation_number": nullable(STR), "contact": R("Contact"),
    "date": DATE, "timezone": STR, "window": R("PickupWindow"), "location": LOC, "instructions": STR,
    "shipments": arr(STR), "manifest": idref("mfst_", "Manifest"), "handling_unit_count": INT, "total_weight": R("Weight"), "type": enum("one_time", "scheduled"),
    "schedule": idref("psch_", "PickupSchedule"), "amount": nullable(R("Money")), "documents": arr(R("Document")),
    "cancellation": nullable(obj({"requested_at": TS, "reason": STR, "carrier_reference": STR})), "messages": R("Messages")},
    ["status", "connection", "date", "window"]))
C("PickupCreate", obj({"connection": STR, "contact": R("Contact"), "date": DATE, "window": R("PickupWindow"),
    "shipments": arr(STR), "handling_unit_count": INT, "total_weight": R("Weight"), "location": LOC, "instructions": STR,
    "carrier_configs": R("CarrierConfigs"), "user_metadata": R("UserMetadata")},
    ["date", "window"], additionalProperties=False))
C("PickupUpdate", obj({"date": DATE, "window": R("PickupWindow"), "shipments": arr(STR), "handling_unit_count": INT, "total_weight": R("Weight"),
    "location": LOC, "instructions": STR, "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("PickupAvailabilityRequest", obj({"connection": STR, "contact": R("Contact"), "date": DATE, "handling_unit_count": INT, "total_weight": R("Weight")}, ["connection", "contact"], additionalProperties=False))
C("PickupAvailability", obj({"object": enum("pickup_availability"), "connection": STR,
    "dates": arr(obj({"date": DATE, "windows": arr(R("PickupWindow")), "cutoff_at": TS, "fee": R("Money")})), "messages": R("Messages")}))

# ---------- manifests ----------
MANIFEST_ERR = obj({"shipment": STR, "code": STR, "message": STR, "carrier_metadata": R("CarrierMetadata")})
C("Manifest", resource("manifest", "mfst_", {
    "status": enum("pending", "submitted", "partially_submitted", "failed"), "mode": enum("explicit", "close_all"),
    "trigger": enum("api", "schedule", "carrier_auto"), "connection": STR, "carrier": STR,
    "ship_date": DATE, "timezone": STR, "address": nullable(R("Address")), "group": nullable(STR),
    "shipments": arr(STR), "shipment_count": INT, "handling_unit_count": INT, "total_weight": R("Weight"),
    "carrier_manifests": arr(obj({"carrier_reference": STR, "shipments": arr(STR), "documents": arr(STR), "carrier_metadata": R("CarrierMetadata")})),
    "documents": arr(R("Document")), "pickup": idref("pck_", "Pickup"),
    "errors": arr(MANIFEST_ERR), "reference": nullable(STR), "submitted_at": nullable(TS), "messages": R("Messages")},
    ["status", "mode", "trigger", "connection"]))
C("ManifestPreviewRequest", obj({"connection": STR, "shipments": arr(STR), "ship_date": DATE, "address": R("Address"), "group": STR,
    "mode": enum("explicit", "close_all"), "split": enum("auto", "none"), "ship_date_policy": enum("strict", "roll_forward")}, ["connection"], additionalProperties=False))
C("ManifestPreview", obj({"object": enum("manifest_preview"), "connection": STR, "carrier": STR, "ship_date": DATE, "cutoff_at": nullable(TS),
    "batches": arr(obj({"address": nullable(R("Address")), "group": nullable(STR), "shipments": arr(STR), "shipment_count": INT, "handling_unit_count": INT})),
    "blocked": arr(MANIFEST_ERR), "excluded": arr(MANIFEST_ERR)}, ["object", "connection", "batches"]))
C("ManifestCreate", obj({"connection": STR, "mode": enum("explicit", "close_all"), "shipments": arr(STR), "ship_date": DATE, "address": R("Address"),
    "group": STR, "ship_date_policy": enum("strict", "roll_forward"), "split": enum("auto", "none"),
    "pickup": {"anyOf": [STR, obj({"book": BOOL, "window": R("PickupWindow"), "contact": R("Contact")})]},
    "carrier_configs": R("CarrierConfigs"), "reference": STR, "user_metadata": R("UserMetadata")}, ["connection"], additionalProperties=False))
C("MetadataUpdate", obj({"user_metadata": R("UserMetadata"), "reference": STR}, additionalProperties=False))

# ---------- files & documents ----------
FILE_PURPOSE = enum("customs_document", "dangerous_goods_declaration", "label", "manifest", "signature_image", "proof_of_delivery", "logo", "export", "other")
C("File", resource("file", "file_", {"purpose": FILE_PURPOSE, "filename": STR, "content_type": STR, "size": INT, "sha256": STR,
    "url": S("string", format="uri"), "url_expires_at": TS, "expires_at": nullable(TS)}, ["purpose", "size"]))
C("FileCreateJson", obj({"purpose": FILE_PURPOSE, "filename": STR, "content_type": STR, "data": S("string", contentEncoding="base64"), "user_metadata": R("UserMetadata")}, ["purpose", "filename", "content_type", "data"]))
DOC_TYPE = enum("commercial_invoice", "proforma_invoice", "certificate_of_origin", "export_license", "import_permit", "packing_list", "dangerous_goods_declaration", "power_of_attorney", "usmca_certificate", "eur1", "other")
C("DocumentUpload", resource("document_upload", "dupl_", {
    "status": enum("pending", "accepted", "partially_accepted", "rejected"), "connection": STR, "carrier": STR,
    "shipment": nullable(STR), "tracking_number": nullable(STR), "stage": enum("pre_shipment", "post_shipment"),
    "origin_country": nullable(STR), "destination_country": nullable(STR),
    "documents": arr(obj({"file": STR, "type": DOC_TYPE, "name": STR, "status": enum("pending", "accepted", "rejected"),
                          "carrier_reference": nullable(STR), "error": nullable(obj({"code": STR, "message": STR}))})),
    "reference": nullable(STR), "messages": R("Messages")}, ["status", "stage", "documents"]))
C("DocumentUploadCreate", obj({"shipment": STR, "connection": STR, "tracking_number": STR, "origin_country": STR, "destination_country": STR,
    "documents": arr(obj({"file": {"anyOf": [STR, R("FileCreateJson")]}, "type": DOC_TYPE, "name": STR}, ["file", "type"]), minItems=1, maxItems=10),
    "reference": STR, "user_metadata": R("UserMetadata")}, ["documents"], additionalProperties=False))

# ---------- tracking ----------
C("Location", obj({"city": STR, "state": STR, "postal_code": STR, "country": STR, "facility": nullable(STR), "latitude": NUM, "longitude": NUM}))
C("ProofOfDelivery", obj({"signed_by": STR, "signature_file": STR, "photo_files": arr(STR), "location": obj({"latitude": NUM, "longitude": NUM}), "delivered_to": STR}))
C("TrackingEvent", obj({"id": STR, "object": enum("tracking_event"), "occurred_at": S("string", format="date-time"), "received_at": TS,
    "status": R("TrackingStatus"), "status_detail": STR, "description": STR, "carrier_code": nullable(STR), "carrier_status": nullable(STR),
    "location": nullable(R("Location")), "source": enum("carrier_poll", "carrier_push", "injected", "test_helper", "implementer", "device"), "carrier_metadata": R("CarrierMetadata")},
    ["id", "object", "occurred_at", "status"]))
C("Tracker", resource("tracker", "trk_", {
    "tracking_number": STR, "carrier": STR, "connection": nullable(STR), "shipment": idref("shp_", "Shipment"),
    "status": R("TrackingStatus"), "status_detail": STR, "status_updated_at": TS, "delivered_at": nullable(TS),
    "estimated_delivery": nullable(obj({"date": DATE, "window": obj({"start": STR, "end": STR}), "source": enum("carrier", "implementer")})),
    "origin": nullable(R("Location")), "destination": nullable(R("Location")), "signed_by": nullable(STR),
    "proof_of_delivery": nullable(R("ProofOfDelivery")), "attempts": INT, "events": arr(R("TrackingEvent")),
    "tracking_url": nullable(STR), "public_url": nullable(STR),
    "refresh": obj({"mode": enum("auto", "manual"), "next_at": nullable(TS), "last_at": nullable(TS), "stopped_reason": nullable(enum("terminal", "not_found", "manual", "shipment_voided"))}),
    "messages": R("Messages")}, ["tracking_number", "carrier", "status"]))
C("TrackerCreate", obj({"tracking_number": STR, "carrier": STR, "connection": STR, "shipment": STR, "ship_date": DATE,
    "destination_postal_code": STR, "destination_country": STR, "refresh": obj({"mode": enum("auto", "manual")}), "user_metadata": R("UserMetadata")},
    ["tracking_number"], additionalProperties=False))
C("TrackerUpdate", obj({"refresh": obj({"mode": enum("auto", "manual")}), "user_metadata": R("UserMetadata")}, additionalProperties=False))

# ---------- webhooks & events ----------
C("WebhookEndpoint", resource("webhook_endpoint", "we_", {
    "url": S("string", format="uri"), "description": nullable(STR), "enabled_events": arr(STR), "status": enum("enabled", "disabled", "auto_disabled"),
    "api_version": STR, "filters": obj({"carriers": nullable(arr(STR)), "connections": nullable(arr(STR)), "user_metadata": nullable(R("UserMetadata"))}),
    "secret": nullable(S("string", description="Only returned on create and rotate_secret")), "secret_preview": STR,
    "disabled_reason": nullable(STR), "delivery": obj({"last_success_at": nullable(TS), "last_failure_at": nullable(TS), "failure_streak": INT})},
    ["url", "enabled_events", "status"]))
C("WebhookEndpointCreate", obj({"url": S("string", format="uri"), "enabled_events": arr(STR, minItems=1), "description": STR, "api_version": STR,
    "filters": obj({"carriers": arr(STR), "connections": arr(STR), "user_metadata": R("UserMetadata")}), "user_metadata": R("UserMetadata")}, ["url", "enabled_events"], additionalProperties=False))
C("WebhookEndpointUpdate", obj({"url": S("string", format="uri"), "enabled_events": arr(STR), "description": STR, "status": enum("enabled", "disabled"),
    "filters": obj({"carriers": arr(STR), "connections": arr(STR), "user_metadata": R("UserMetadata")}), "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("Event", obj({"id": STR, "object": enum("event"), "livemode": BOOL, "created": TS, "type": STR, "api_version": STR, "account": nullable(STR),
    "data": obj({"object": obj({}, additionalProperties=True), "previous_attributes": nullable(obj({}, additionalProperties=True))}, ["object"]),
    "related": obj({}, additionalProperties=STR), "request": obj({"id": nullable(STR), "idempotency_key": nullable(STR)}), "pending_webhooks": INT},
    ["id", "object", "type", "data", "created"]))
C("WebhookDelivery", obj({"id": STR, "object": enum("webhook_delivery"), "event": STR, "webhook_endpoint": STR, "attempt": INT,
    "status": enum("pending", "succeeded", "failed"), "response_status": nullable(INT), "response_body_excerpt": nullable(STR),
    "duration_ms": INT, "created": TS, "next_retry_at": nullable(TS)}, ["id", "object", "event", "webhook_endpoint", "status"]))
C("InboundTrackingEvent", obj({"occurred_at": S("string", format="date-time"), "status": R("TrackingStatus"), "status_detail": STR, "description": STR,
    "carrier_code": STR, "location": R("Location"), "proof_of_delivery": R("ProofOfDelivery")}, ["occurred_at", "status"]))
C("InboundEventCreate", obj({"type": enum("tracking", "shipment_charge"), "tracker": STR, "carrier": STR, "tracking_number": STR, "create_tracker": BOOL,
    "events": arr(R("InboundTrackingEvent"), maxItems=100), "shipment": STR,
    "charges": arr(obj({"kind": STR, "amount": R("Money"), "carrier_code": STR, "reason": STR}))}, ["type"], additionalProperties=False))
C("InboundEvent", resource("inbound_event", "ibe_", {"type": enum("tracking", "shipment_charge"), "source": enum("api", "carrier_push"),
    "status": enum("processed", "partially_processed", "failed"), "connection": nullable(STR), "tracker": nullable(STR), "shipment": nullable(STR),
    "accepted": INT, "rejected": INT, "errors": arr(obj({"index": INT, "code": STR, "message": STR}))}, ["type", "status"]))

# ---------- carriers / connections / apps ----------
C("JsonSchema", obj({}, additionalProperties=True, description="JSON Schema 2020-12 document, may use x-ui-* and x-secret hints"))
C("ConnectionMethod", obj({"type": enum("credentials", "oauth"), "label": STR,
    "issuer": STR, "authorization_endpoint": STR, "token_endpoint": STR, "openid": BOOL, "scopes": arr(STR),
    "grant_after_callback": enum("authorization_code", "client_credentials_from_callback"),
    "app": obj({"required": BOOL, "system_app": BOOL, "dynamic_registration": BOOL}),
    "credentials_schema": R("JsonSchema"), "config_schema": R("JsonSchema")}, ["type"]))
C("Carrier", obj({"id": STR, "object": enum("carrier"), "name": STR, "logo_url": STR, "status": enum("available", "beta", "deprecated"),
    "countries": obj({"origin": {"anyOf": [arr(STR), enum("*")]}, "destination": {"anyOf": [arr(STR), enum("*")]}}),
    "capabilities": arr(STR),
    "services": arr(obj({"code": STR, "name": STR, "level": R("ServiceLevel"), "carrier_code": STR, "domestic": BOOL, "international": BOOL, "countries": arr(STR)})),
    "packagings": arr(obj({"code": STR, "name": STR, "max_weight": R("Weight"), "dimensions": R("Dimensions")})),
    "label": obj({"formats": arr(STR), "sizes": arr(STR)}), "standardized_features": arr(STR), "shipment_config_schema": R("JsonSchema"), "manifest_config_schema": R("JsonSchema"),
    "manifest": nullable(obj({"required": BOOL, "scope": arr(enum("connection", "ship_date", "origin", "group")), "modes": arr(enum("explicit", "close_all")), "async": BOOL, "multiple_per_request": BOOL, "ship_date_policies": arr(STR), "cutoff_local_time": nullable(STR), "carrier_auto_close": BOOL, "void_after": BOOL, "reprint": BOOL, "max_shipments": INT, "documents": arr(STR)})), "carrier_metadata_schema": R("JsonSchema"), "pickup_config_schema": R("JsonSchema"),
    "pickup": nullable(obj({"requires": arr(STR), "same_day_cutoff": STR})),
    "tracking": obj({"number_patterns": arr(STR), "public_url_template": STR}),
    "connection_methods": arr(R("ConnectionMethod")),
    "inbound": obj({"supported": BOOL, "registration": enum("automatic", "manual"), "signature": STR, "header": STR}),
    "test_environment": enum("sandbox", "simulator", "none")}, ["id", "object", "name", "capabilities"]))
C("Connection", resource("connection", "conn_", {
    "integration": STR, "interfaces": arr(STR), "carrier": S("string", description="Alias of integration for lsp connections"), "method": enum("credentials", "oauth"), "display_name": STR, "account_number": nullable(STR),
    "status": enum("active", "inactive", "error", "reauthorization_required", "pending"), "default": BOOL, "capabilities": arr(STR),
    "config": obj({}, additionalProperties=True), "credentials": {"type": "null", "description": "Write-only; always null in responses"},
    "credentials_preview": nullable(obj({}, additionalProperties=STR)),
    "oauth": nullable(obj({"app": STR, "issuer": STR, "subject": STR, "scopes": arr(STR), "access_token_expires_at": TS, "refresh_token_expires_at": nullable(TS), "last_refreshed_at": TS, "status": enum("valid", "refreshing", "invalid")})),
    "ownership": enum("account", "platform", "system"),
    "inbound": nullable(obj({"url": STR, "status": enum("registered", "manual_registration_required", "unsupported")})),
    "verification": obj({"status": enum("verified", "unverified", "failed"), "checked_at": nullable(TS), "error": nullable(obj({"code": STR, "message": STR}))})},
    ["carrier", "method", "status"]))
C("ConnectionCreate", obj({"carrier": STR, "display_name": STR, "credentials": obj({}, additionalProperties=True, writeOnly=True),
    "config": obj({}, additionalProperties=True), "default": BOOL, "verify": S("boolean", default=True), "user_metadata": R("UserMetadata")},
    ["carrier", "credentials"], additionalProperties=False))
C("ConnectionUpdate", obj({"display_name": STR, "credentials": obj({}, additionalProperties=True, writeOnly=True), "config": obj({}, additionalProperties=True),
    "status": enum("active", "inactive"), "default": BOOL, "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("App", resource("app", "app_", {"carrier": STR, "name": STR, "client_id": STR, "client_secret": nullable(S("string", description="Only on create/rotate")),
    "client_secret_preview": STR, "client_secret_expires_at": nullable(TS), "redirect_uris": arr(STR), "scopes": arr(STR), "issuer": STR, "openid": BOOL,
    "token_endpoint_auth_method": enum("client_secret_basic", "client_secret_post", "private_key_jwt", "none"), "pkce": enum("S256", "none"),
    "registration": enum("manual", "dynamic"), "visibility": enum("private", "platform"), "status": enum("active", "disabled"), "connection_count": INT},
    ["carrier", "client_id", "registration"]))
C("AppCreate", obj({"carrier": STR, "issuer": STR, "name": STR, "client_id": STR, "client_secret": S("string", writeOnly=True), "scopes": arr(STR),
    "redirect_uris": arr(STR), "visibility": enum("private", "platform"), "registration": enum("manual", "dynamic"),
    "initial_access_token": S("string", writeOnly=True), "user_metadata": R("UserMetadata")}, ["carrier"], additionalProperties=False))
C("AppUpdate", obj({"name": STR, "scopes": arr(STR), "visibility": enum("private", "platform"), "client_secret": S("string", writeOnly=True),
    "status": enum("active", "disabled"), "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("ConnectSession", obj({"id": STR, "object": enum("connect_session"), "livemode": BOOL, "created": TS,
    "status": enum("open", "completed", "failed", "expired"), "mode": enum("redirect", "device"), "carrier": STR, "app": nullable(STR),
    "url": S("string", format="uri"), "user_code": nullable(STR), "expires_at": TS, "return_url": nullable(STR),
    "connection": nullable(STR), "error": nullable(obj({"code": enum("access_denied", "invalid_grant", "subject_already_connected", "id_token_invalid", "expired"), "message": STR}))},
    ["id", "object", "status", "carrier", "url", "expires_at"]))
C("ConnectSessionCreate", obj({"carrier": STR, "app": STR, "mode": enum("redirect", "device"), "return_url": S("string", format="uri"),
    "display_name": STR, "config": obj({}, additionalProperties=True), "scopes": arr(STR), "connection": STR, "login_hint": STR, "user_metadata": R("UserMetadata")},
    ["carrier"], additionalProperties=False))

# ---------- batches ----------
C("Batch", resource("batch", "bat_", {"operation": enum("shipments.create", "trackers.create", "shipments.void", "pickups.cancel", "products.upsert"),
    "status": enum("processing", "completed", "completed_with_errors"), "counts": obj({"total": INT, "succeeded": INT, "failed": INT}),
    "results_file": nullable(STR)}, ["operation", "status"]))
C("BatchCreate", obj({"operation": enum("shipments.create", "trackers.create", "shipments.void", "pickups.cancel", "products.upsert"),
    "items": arr(obj({}, additionalProperties=True), minItems=1, maxItems=1000), "webhook_endpoint": STR, "user_metadata": R("UserMetadata")}, ["operation", "items"], additionalProperties=False))


# ---------- shared: recurrence, area ----------
DAYS = enum("mon", "tue", "wed", "thu", "fri", "sat", "sun")
C("Recurrence", obj({"frequency": enum("daily", "weekly", "monthly"), "interval": S("integer", minimum=1, default=1), "days": arr(DAYS),
    "day_of_month": nullable(S("integer", minimum=-1, maximum=31)), "times": arr(S("string", description="HH:MM or HH:MM-HH:MM")), "timezone": STR,
    "starts_on": DATE, "ends_on": nullable(DATE), "count": nullable(INT), "exceptions": arr(DATE), "additions": arr(DATE),
    "holiday_calendar": nullable(STR), "rrule": nullable(S("string", description="RFC 5545 RRULE; overrides frequency/interval/days"))}, ["timezone"]))
GEO = obj({"latitude": NUM, "longitude": NUM}, ["latitude", "longitude"])
C("Area", obj({"countries": arr(STR), "subdivisions": arr(STR), "postal_codes": arr(STR),
    "cities": arr(obj({"country": STR, "state": STR, "name": STR})), "polygons": nullable(obj({}, additionalProperties=True, description="GeoJSON MultiPolygon")),
    "radius": nullable(obj({"center": GEO, "distance": obj({"value": NUM, "unit": enum("km", "mi")})})),
    "exclude": nullable({"$ref": "#/components/schemas/Area"})}))
MEASURE = lambda: obj({"value": NUM, "unit": STR})
CAPACITY = obj({"weight": R("Weight"), "volume": MEASURE(), "handling_units": INT, "pallets": INT})

# ---------- pickup schedules ----------
C("PickupSchedule", resource("pickup_schedule", "psch_", {
    "status": enum("pending", "active", "paused", "cancelled", "failed"), "connection": STR, "carrier": STR,
    "management": enum("carrier", "implementer"), "contact": R("Contact"), "recurrence": R("Recurrence"), "window": R("PickupWindow"),
    "location": STR, "instructions": STR, "estimate": obj({"handling_unit_count": INT, "total_weight": R("Weight")}),
    "booking": obj({"book_ahead_hours": INT, "skip_if_empty": BOOL, "empty_check_at": STR, "attach_shipments": enum("eligible", "none")}),
    "carrier_configs": R("CarrierConfigs"), "paused_until": nullable(DATE),
    "next_occurrences": arr(obj({"date": DATE, "status": enum("upcoming", "booked", "skipped", "completed", "missed", "failed"), "pickup": nullable(STR)})),
    "carrier_reference": nullable(STR)}, ["status", "connection", "management", "recurrence", "window"]))
C("PickupScheduleCreate", obj({"connection": STR, "management": enum("carrier", "implementer"), "contact": R("Contact"), "recurrence": R("Recurrence"),
    "window": R("PickupWindow"), "location": STR, "instructions": STR, "estimate": obj({"handling_unit_count": INT, "total_weight": R("Weight")}),
    "booking": obj({"book_ahead_hours": INT, "skip_if_empty": BOOL, "empty_check_at": STR, "attach_shipments": enum("eligible", "none")}),
    "carrier_configs": R("CarrierConfigs"), "user_metadata": R("UserMetadata")}, ["connection", "contact", "recurrence", "window"], additionalProperties=False))
C("PickupScheduleUpdate", obj({"contact": R("Contact"), "recurrence": R("Recurrence"), "window": R("PickupWindow"), "location": STR, "instructions": STR,
    "booking": obj({}, additionalProperties=True), "carrier_configs": R("CarrierConfigs"), "apply_to_booked": BOOL, "user_metadata": R("UserMetadata")}, additionalProperties=False))

# ---------- trade ----------
TRADE_CTX = {"ship_from": R("Contact"), "ship_to": R("Contact"), "items": arr(R("Item")), "order": R("Order"),
             "customs_declaration": R("CustomsDeclaration"), "shipment": STR}
HS_CAND = obj({"country": STR, "hs_code": STR, "description": STR, "confidence": S("number", minimum=0, maximum=1),
               "alternatives": arr(obj({"hs_code": STR, "confidence": NUM}))})
RESTRICTION = obj({"country": STR, "level": enum("prohibited", "restricted", "license_required", "agency_review"), "agency": nullable(STR),
                   "code": STR, "message": STR, "license_types": arr(STR), "documents_required": arr(STR)})
C("Classification", resource("classification", "cls_", {"status": enum("pending", "completed", "failed"),
    "items": arr(obj({"index": INT, "sku": nullable(STR), "export": nullable(HS_CAND), "import": arr(HS_CAND), "requires_review": BOOL,
                      "rationale": STR, "restrictions": arr(RESTRICTION)})), "messages": R("Messages")}, ["status", "items"]))
C("ClassificationCreate", obj({"items": arr(R("Item"), minItems=1), "export_country": STR, "import_countries": arr(STR),
    "include_restrictions": BOOL, "user_metadata": R("UserMetadata")}, ["items"], additionalProperties=False))
C("ComplianceScreening", resource("compliance_screening", "scr_", {"decision": enum("clear", "review", "blocked"),
    "parties": arr(obj({"role": STR, "decision": enum("clear", "review", "blocked"),
                        "matches": arr(obj({"list": STR, "name": STR, "score": NUM, "entry_id": STR, "url": STR}))})),
    "items": arr(obj({"index": INT, "decision": enum("clear", "review", "blocked"), "restrictions": arr(RESTRICTION)})),
    "embargo": nullable(obj({"country": STR, "program": STR})), "lists_version": STR}, ["decision"]))
C("ComplianceScreeningCreate", obj({"parties": arr(obj({"role": STR, "contact": R("Contact")})), "items": arr(R("Item")),
    "ship_from": R("Contact"), "ship_to": R("Contact"), "lists": arr(STR), "shipment": STR, "user_metadata": R("UserMetadata")}, additionalProperties=False))
TAXLINE = obj({"kind": STR, "name": STR, "rate": NUM, "basis": STR, "amount": R("Money"), "measure": STR, "preferential": nullable(STR)})
C("LandedCost", resource("landed_cost", "lc_", {"expires_at": TS, "guaranteed": BOOL, "currency": STR, "incoterm": STR,
    "regime": obj({"type": enum("standard", "eu_ioss", "uk_low_value", "no_voec", "au_lvg", "ch_low_value", "us_section_321", "other"),
                   "threshold": nullable(R("Money")), "collected_at": enum("point_of_sale", "import")}),
    "de_minimis": obj({"duty": nullable(R("Money")), "tax": nullable(R("Money")), "duty_applied": BOOL, "tax_applied": BOOL}),
    "items": arr(obj({"index": INT, "import_hs_code": STR, "customs_value": R("Money"), "duties": arr(TAXLINE), "taxes": arr(TAXLINE)})),
    "fees": arr(R("Charge")), "totals": obj({"duties": R("Money"), "taxes": R("Money"), "fees": R("Money"), "total": R("Money")}),
    "messages": R("Messages")}, ["totals", "guaranteed"]))
C("LandedCostCreate", obj({**TRADE_CTX, "service": STR, "currency": STR, "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("Tariff", obj({"object": enum("tariff"), "country": STR, "hs_code": STR, "description": STR,
    "duty": arr(obj({"measure": STR, "rate": NUM, "agreement": STR, "origin_country": STR})), "taxes": arr(obj({"name": STR, "rate": NUM})),
    "restrictions": arr(RESTRICTION), "valid_on": DATE}))
C("DutyCollection", resource("duty_collection", "dcol_", {"status": enum("pending_assessment", "due", "paid", "disputed", "waived"),
    "shipment": STR, "landed_cost": nullable(STR), "assessed": obj({"duties": R("Money"), "taxes": R("Money"), "fees": R("Money")}),
    "total": R("Money"), "variance": R("Money"), "assessed_at": nullable(TS), "due_by": nullable(DATE), "entry_number": nullable(STR),
    "payment": nullable(obj({}, additionalProperties=True))}, ["status", "shipment"]))

# ---------- catalog ----------
CAT_STATUS = enum("draft", "active", "retired")
C("CatalogService", resource("service", "svc_", {"code": STR, "name": STR, "description": STR, "level": R("ServiceLevel"), "carrier_code": STR,
    "status": CAT_STATUS, "domestic": BOOL, "international": BOOL,
    "coverage": arr(obj({"origin_zone": STR, "destination_zone": STR, "transit": obj({"min_days": INT, "max_days": INT, "business_days": BOOL})})),
    "cutoff": nullable(obj({"local_time": STR, "facility": nullable(STR)})), "handover": arr(enum("drop_off", "pickup")),
    "limits": obj({"handling_unit_types": arr(STR), "weight": obj({"min": R("Weight"), "max": R("Weight")}), "dimensions": obj({}, additionalProperties=R("Weight") if False else MEASURE()),
                   "declared_value": obj({"max": R("Money")}), "handling_units_per_shipment": INT}),
    "dimensional_weight": nullable(obj({"divisor": NUM, "unit": STR, "applies": enum("always", "when_greater", "never")})),
    "packagings": arr(STR), "options": arr(obj({"option": STR, "default": {}, "required": BOOL, "allowed": arr({})})),
    "requires": arr(STR), "features": obj({}, additionalProperties=True), "label": obj({"formats": arr(STR), "sizes": arr(STR), "template": nullable(STR), "spec": nullable(STR)}),
    "effective_from": nullable(DATE), "effective_until": nullable(DATE), "version": INT}, ["code", "name", "level", "status"]))
C("CatalogOption", resource("option", "opt_", {"key": STR, "standardized": BOOL, "carrier_code": nullable(STR), "name": STR, "description": STR, "schema": R("JsonSchema"),
    "conflicts_with": arr(STR), "requires": arr(STR), "surcharge": nullable(STR), "status": CAT_STATUS, "version": INT}, ["key", "schema", "status"]))
C("Packaging", resource("packaging", "pkg_", {"code": STR, "name": STR, "type": enum("envelope", "pak", "box", "tube", "pallet", "crate", "custom"),
    "inner_dimensions": nullable(R("Dimensions")), "outer_dimensions": nullable(R("Dimensions")), "tare_weight": nullable(R("Weight")),
    "max_weight": nullable(R("Weight")), "flat_rate": BOOL, "status": CAT_STATUS, "version": INT}, ["code", "type", "status"]))
C("Zone", resource("zone", "zone_", {"name": STR, "purpose": arr(enum("coverage", "pricing", "service_area", "surcharge")), "area": R("Area"),
    "priority": INT, "status": CAT_STATUS, "version": INT}, ["name", "area", "status"]))
C("ServiceAvailability", obj({"object": enum("service_availability"), "services": arr(obj({"service": STR, "code": STR, "carrier": STR,
    "available": BOOL, "delivery": nullable(R("DeliveryEstimate")), "cutoff_at": nullable(TS), "reason": nullable(obj({"code": STR, "param": STR}))}))}))
C("ServiceAvailabilityRequest", obj({"ship_from": R("Contact"), "ship_to": R("Contact"), "handling_units": arr(R("HandlingUnit")), "ship_date": DATE,
    "carrier_configs": R("CarrierConfigs")}, ["ship_from", "ship_to"], additionalProperties=False))
C("ZoneMatch", obj({"object": enum("list"), "data": arr(R("Zone"))}))

# ---------- pricing ----------
BAND = obj({"max_weight": R("Weight"), "price": R("Money"), "cost": R("Money"), "base": R("Money"),
            "per_unit": obj({"amount": INT, "currency": STR, "per": MEASURE(), "after": MEASURE()})}, ["max_weight"])
C("RateSheet", resource("rate_sheet", "rs_", {"name": STR, "status": CAT_STATUS, "version": INT, "currency": STR,
    "effective_from": nullable(DATE), "effective_until": nullable(DATE), "services": arr(STR), "origin_zones": arr(STR),
    "weight_rounding": obj({"increment": R("Weight"), "mode": enum("up", "nearest", "none")}),
    "dimensional_weight": nullable(obj({"divisor": NUM, "unit": STR, "applies": STR})), "aggregate": enum("handling_unit", "shipment"),
    "rates": arr(obj({"service": STR, "origin_zone": nullable(STR), "destination_zone": STR, "bands": arr(BAND), "min_charge": nullable(R("Money")),
                      "transit": nullable(obj({"min_days": INT, "max_days": INT}))})),
    "surcharges": arr(STR), "assignments": obj({"accounts": nullable(arr(STR)), "default": BOOL})}, ["name", "status", "currency", "rates"]))
C("Surcharge", resource("surcharge", "sur_", {"name": STR, "kind": STR,
    "calculation": obj({"type": enum("fixed", "percentage", "per_unit", "table"), "amount": R("Money"), "rate": NUM,
                        "basis": enum("base", "base_plus_fixed_surcharges", "total"), "per": MEASURE(), "rows": arr(obj({}, additionalProperties=True))}, ["type"]),
    "conditions": obj({}, additionalProperties=True), "schedule": arr(obj({"effective_from": DATE, "rate": NUM, "amount": R("Money")})),
    "status": enum("active", "inactive")}, ["name", "kind", "calculation"]))
C("PricingRule", resource("pricing_rule", "prule_", {"name": STR, "type": enum("markup", "discount", "override"),
    "adjustment": obj({"type": enum("percentage", "fixed"), "rate": NUM, "amount": R("Money"), "basis": STR}),
    "conditions": obj({"accounts": nullable(arr(STR)), "levels": nullable(arr(STR)), "carriers": nullable(arr(STR)), "services": nullable(arr(STR)),
                       "connections": nullable(arr(STR)), "destination_zones": nullable(arr(STR))}),
    "floor": nullable(obj({"margin": obj({"type": STR, "rate": NUM})})), "priority": INT, "visible": BOOL,
    "effective_from": nullable(DATE), "effective_until": nullable(DATE), "status": enum("active", "inactive")}, ["name", "type", "adjustment"]))
C("PricingDetails", obj({"rate_sheet": nullable(STR), "version": nullable(INT), "origin_zone": nullable(STR), "destination_zone": nullable(STR),
    "billable_weight": R("Weight"), "band_index": nullable(INT), "surcharges": arr(STR), "pricing_rules": arr(STR)}))

# ---------- routes ----------
ACT = enum("load", "unload", "pickup", "delivery", "handover", "sort", "export_clearance", "import_clearance", "cross_dock", "fuel", "break")
OPERATOR = obj({"type": enum("self", "carrier", "partner"), "connection": STR, "service": STR, "name": STR, "reference": STR}, ["type"])
C("Facility", resource("facility", "fac_", {"name": STR,
    "type": enum("hub", "sort_center", "depot", "gateway", "warehouse", "fulfillment_center", "cross_dock", "airport", "seaport", "rail_terminal", "access_point", "customs_bonded", "partner"),
    "status": enum("active", "inactive"), "contact": R("Contact"), "location": nullable(GEO), "timezone": STR, "operating_hours": nullable(R("Recurrence")),
    "codes": obj({}, additionalProperties=STR), "capabilities": arr(STR), "service_zones": arr(STR),
    "functions": obj({k: nullable(obj({}, additionalProperties=True)) for k in ["sortation", "storage", "fulfillment", "cross_dock", "returns", "customs", "hazmat"]})}, ["name", "type", "contact", "timezone"]))
C("Stop", obj({"id": STR, "sequence": INT, "facility": nullable(STR), "contact": nullable(R("Contact")), "activities": arr(ACT),
    "arrive_offset": nullable(STR), "depart_offset": nullable(STR), "cutoff_offset": nullable(STR), "service_minutes": INT,
    "window": nullable(obj({"arrive_after": STR, "arrive_before": STR}))}, ["id", "sequence", "activities"]))
C("Leg", obj({"id": STR, "from_stop": STR, "to_stop": STR, "mode": enum("road", "air", "sea", "rail", "courier", "bike", "walk", "drone"),
    "operator": OPERATOR, "vehicle_type": nullable(STR), "air": nullable(obj({"flight_number": STR, "awb_prefix": STR, "uld_assignments": arr(obj({"uld_id": STR, "uld_type": STR, "position": STR, "handling_units": arr(STR)}))})), "duration_minutes": INT, "distance": nullable(MEASURE()), "capacity": CAPACITY,
    "cost": nullable(R("Money")), "carrier_metadata": R("CarrierMetadata")}, ["id", "from_stop", "to_stop", "mode", "operator"]))
C("Route", resource("route", "rte_", {"name": STR, "type": enum("linehaul", "first_mile", "last_mile", "mixed"), "status": enum("draft", "active", "inactive"),
    "recurrence": nullable(R("Recurrence")), "generate_runs_ahead_days": INT, "stops": arr(R("Stop")), "legs": arr(R("Leg"))}, ["name", "type", "status", "stops"]))
C("RouteCreate", obj({"name": STR, "type": enum("linehaul", "first_mile", "last_mile", "mixed"), "recurrence": R("Recurrence"),
    "generate_runs_ahead_days": INT, "stops": arr(R("StopInput")), "user_metadata": R("UserMetadata")}, ["name", "type"], additionalProperties=False))
C("RouteUpdate", obj({"name": STR, "recurrence": nullable(R("Recurrence")), "generate_runs_ahead_days": INT, "apply_to_existing_runs": BOOL,
    "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("StopInput", obj({"sequence": INT, "facility": STR, "contact": R("Contact"), "activities": arr(ACT), "arrive_offset": STR, "depart_offset": STR,
    "cutoff_offset": STR, "service_minutes": INT, "window": obj({"arrive_after": STR, "arrive_before": STR})}, additionalProperties=False))
C("LegUpdate", obj({"mode": STR, "operator": OPERATOR, "vehicle_type": STR, "duration_minutes": INT, "distance": MEASURE(), "capacity": CAPACITY, "cost": R("Money")}, additionalProperties=False))
RUN_STOP = obj({"id": STR, "facility": nullable(STR), "contact": nullable(R("Contact")), "status": enum("pending", "arrived", "departed", "completed", "skipped", "failed"),
    "reason": nullable(STR), "scheduled_arrival": nullable(STR), "scheduled_departure": nullable(STR), "eta": nullable(STR),
    "arrived_at": nullable(TS), "departed_at": nullable(TS), "shipments": obj({}, additionalProperties=arr(STR))})
RUN_LEG = obj({"id": STR, "status": enum("pending", "in_transit", "arrived", "cancelled"), "departed_at": nullable(TS), "arrived_at": nullable(TS),
    "delay_minutes": INT, "load": obj({"weight": R("Weight"), "handling_units": INT}), "carrier_metadata": R("CarrierMetadata")})
C("RouteRun", resource("route_run", "run_", {"route": nullable(STR), "date": DATE, "status": enum("planned", "dispatched", "in_progress", "completed", "cancelled"),
    "scheduled_start": STR, "started_at": nullable(TS), "completed_at": nullable(TS), "vehicle": idref("veh_", "Vehicle"), "driver": idref("drv_", "Driver"),
    "stops": arr(RUN_STOP), "legs": arr(RUN_LEG), "shipment_count": INT}, ["date", "status", "stops"]))
C("RouteRunCreate", obj({"route": STR, "date": DATE, "scheduled_start": STR, "stops": arr(R("StopInput")), "vehicle": STR, "driver": STR,
    "user_metadata": R("UserMetadata")}, ["date"], additionalProperties=False))
C("StopOutcome", obj({"at": STR, "position": GEO, "results": arr(obj({"shipment": STR, "outcome": enum("delivered", "picked_up", "loaded", "unloaded"),
    "reason": STR, "proof_of_delivery": R("ProofOfDelivery")}))}, additionalProperties=False))
C("Journey", obj({"id": STR, "object": enum("journey"), "shipment": nullable(STR), "status": enum("planned", "on_track", "at_risk", "delayed", "rerouted", "completed"),
    "segments": arr(obj({"sequence": INT, "type": enum("first_mile", "middle_mile", "last_mile", "end_to_end"), "run": nullable(STR), "leg": nullable(STR),
                         "operator": nullable(OPERATOR), "from": STR, "to": STR, "planned_departure": nullable(STR), "planned_arrival": nullable(STR),
                         "actual_departure": nullable(STR), "actual_arrival": nullable(STR), "subcontracted_shipment": nullable(STR)})),
    "planned_delivery": nullable(DATE), "estimated_delivery": nullable(DATE)}, ["object", "status", "segments"]))
C("JourneyPlanRequest", obj({"ship_from": R("Contact"), "ship_to": R("Contact"), "handling_units": arr(R("HandlingUnit")), "service": STR, "ship_date": DATE}, ["ship_from", "ship_to"], additionalProperties=False))

# ---------- fleet ----------
C("Vehicle", resource("vehicle", "veh_", {"name": STR, "type": enum("car", "van", "truck", "trailer", "bike", "cargo_bike", "scooter", "walker", "drone", "aircraft", "vessel", "rail_car"), "class": obj({}, additionalProperties=True, description="Type-specific attributes (aircraft, drone, vessel, rail_car, road)"),
    "status": enum("active", "maintenance", "retired"), "registration": obj({"plate": STR, "country": STR}), "capacity": CAPACITY,
    "features": arr(STR), "home_facility": nullable(STR), "range": nullable(MEASURE()), "telematics": nullable(obj({"provider": STR, "device_id": STR}))}, ["name", "type", "status"]))
C("Driver", resource("driver", "drv_", {"contact": R("Contact"), "status": enum("active", "inactive"), "home_facility": nullable(STR),
    "qualifications": arr(obj({"type": STR, "class": STR, "expires_on": DATE})), "skills": arr(STR), "shifts": nullable(R("Recurrence")),
    "availability_exceptions": arr(obj({"date": DATE, "available": BOOL, "reason": STR})), "app_user": nullable(STR)}, ["contact", "status"]))
C("Position", obj({"at": S("string", format="date-time"), "latitude": NUM, "longitude": NUM, "heading": NUM, "speed": MEASURE(), "accuracy_m": NUM,
    "source": enum("driver_app", "telematics", "manual")}, ["at", "latitude", "longitude"]))
C("Optimization", resource("optimization", "optj_", {"status": enum("pending", "completed", "failed"), "date": DATE, "depot": STR,
    "proposed_runs": arr(obj({"vehicle": STR, "driver": STR, "stops": arr(R("StopInput")), "distance": MEASURE(), "duration_minutes": INT, "load": obj({"handling_units": INT})})),
    "unassigned": arr(obj({"shipment": STR, "reason": STR})), "summary": obj({}, additionalProperties=True), "runs": arr(STR)}, ["status"]))
C("OptimizationCreate", obj({"date": DATE, "depot": STR, "jobs": obj({"shipments": arr(STR), "pickups": arr(STR)}), "vehicles": arr(STR), "drivers": arr(STR),
    "service_area": STR, "objective": enum("minimize_duration", "minimize_distance", "minimize_vehicles", "balance_load"),
    "constraints": obj({}, additionalProperties=True), "commit": BOOL}, ["date", "depot", "jobs", "vehicles"], additionalProperties=False))


# ---------- injection ----------
INJ_COMMON = {"channel": enum("carrier", "marketplace", "ecommerce_platform", "merchant"), "upstream_reference": STR, "upstream_carrier": nullable(STR),
    "upstream_tracking_number": nullable(STR), "label_mode": enum("pre_labeled", "relabel", "label_required"), "injection_point": nullable(STR),
    "expected_at": nullable(STR), "asn": nullable(STR),
    "tracking_feedback": obj({"mode": enum("push", "pull", "none"), "target": enum("partner_webhooks", "federated"), "number": enum("upstream", "local")})}
C("Injection", obj({"partner": STR, **INJ_COMMON, "status": enum("submitted", "accepted", "on_hold", "rejected", "received", "missing", "cancelled"),
    "decision": obj({"reasons": arr(obj({"code": STR, "message": STR, "param": STR}))}),
    "received": nullable(obj({"at": TS, "facility": STR, "condition": enum("ok", "damaged"), "measured": obj({"weight": R("Weight"), "dimensions": R("Dimensions")})}))},
    ["partner", "channel", "upstream_reference", "label_mode", "status"]))
C("InjectionInput", obj(INJ_COMMON, ["channel", "upstream_reference", "label_mode"], additionalProperties=False))
SCAN = obj({"tracking_number": STR, "sscc": STR, "at": STR, "condition": enum("ok", "damaged"), "measured": obj({"weight": R("Weight"), "dimensions": R("Dimensions")})})
C("Asn", resource("asn", "asn_", {"partner": STR, "facility": STR, "status": enum("announced", "in_transit", "arrived", "receiving", "closed", "cancelled"),
    "expected_at": STR, "arrived_at": nullable(TS), "transport": obj({"mode": STR, "carrier_name": STR, "vehicle": STR, "registration": STR, "seal_number": STR, "reference": STR}),
    "shipments": arr(STR), "expected": obj({"shipments": INT, "handling_units": INT, "weight": R("Weight"), "containers": arr(obj({"type": STR, "count": INT}))}),
    "received": obj({"handling_units": INT, "damaged": INT, "unexpected": INT}),
    "discrepancies": arr(obj({"type": enum("missing", "unexpected", "damaged", "weight_variance", "misrouted_asn"), "shipment": nullable(STR), "tracking_number": nullable(STR),
                              "note": STR, "declared": R("Weight"), "measured": R("Weight")})),
    "closed_at": nullable(TS), "documents": arr(R("Document"))}, ["partner", "facility", "status"]))
C("AsnCreate", obj({"facility": STR, "expected_at": STR, "transport": obj({}, additionalProperties=True),
    "shipments": arr({"anyOf": [STR, R("ShipmentCreate")]}), "user_metadata": R("UserMetadata")}, ["facility", "shipments"], additionalProperties=False))
C("AsnUpdate", obj({"expected_at": STR, "transport": obj({}, additionalProperties=True), "add_shipments": arr(STR), "remove_shipments": arr(STR), "user_metadata": R("UserMetadata")}, additionalProperties=False))

# ---------- accounts & identity ----------
C("Account", resource("account", "acct_", {"type": enum("merchant", "carrier", "partner", "platform", "internal"),
    "carrier": nullable(obj({"id": STR, "kinds": arr(STR), "codes": obj({}, additionalProperties=nullable(STR)), "status": enum("onboarding", "listed", "paused", "delisted"), "visibility": enum("network", "private", "interline_only"), "service_area": arr(STR),
        "segments": obj({k: nullable(obj({"lanes": arr(obj({"from_zone": STR, "to_zone": STR, "modes": arr(STR)})), "zones": arr(STR), "handoff_points": arr(STR), "customs": obj({"export": BOOL, "import": BOOL})})) for k in ["first_mile", "middle_mile", "last_mile", "end_to_end"]})})),
    "status": enum("onboarding", "active", "restricted", "suspended", "closed"), "parent": nullable(STR),
    "profile": obj({"legal_name": STR, "display_name": STR, "contact": R("Contact"), "website": STR, "industry": STR}),
    "settings": obj({"timezone": STR, "currency": STR, "units": obj({"weight": STR, "dimensions": STR}), "label_format": R("LabelFormat"),
                     "default_ship_from": nullable(R("Contact")), "api_version": STR}),
    "modules": arr(STR), "requirements": obj({"currently_due": arr(STR), "pending_verification": arr(STR)})}, ["type", "status"]))
C("AccountCreate", obj({"type": enum("merchant", "partner"), "profile": obj({}, additionalProperties=True), "settings": obj({}, additionalProperties=True),
    "modules": arr(STR), "user_metadata": R("UserMetadata")}, ["type"], additionalProperties=False))
C("AccountUpdate", obj({"profile": obj({}, additionalProperties=True), "settings": obj({}, additionalProperties=True), "modules": arr(STR), "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("IdentityProvider", resource("identity_provider", "idp_", {"account": STR, "type": enum("oidc", "saml"), "status": enum("pending", "active", "disabled"),
    "issuer": STR, "client_id": STR, "client_secret": nullable(S("string", description="Write-only")), "scopes": arr(STR),
    "domains": arr(obj({"domain": STR, "verified": BOOL, "verification": obj({"type": STR, "name": STR, "value": STR})})),
    "claims": obj({"email": STR, "name": STR, "groups": STR}), "role_mapping": arr(obj({"group": STR, "role": STR})), "default_role": nullable(STR),
    "provisioning": obj({"jit": BOOL, "deprovision_on_missing_group": BOOL, "scim": obj({"enabled": BOOL, "endpoint": nullable(STR)})}), "enforce": BOOL},
    ["account", "type", "issuer"]))
C("IdentityProviderInput", obj({"type": enum("oidc", "saml"), "issuer": STR, "client_id": STR, "client_secret": S("string", writeOnly=True), "scopes": arr(STR),
    "domains": arr(obj({"domain": STR})), "claims": obj({}, additionalProperties=STR), "role_mapping": arr(obj({"group": STR, "role": STR})),
    "default_role": STR, "provisioning": obj({}, additionalProperties=True), "enforce": BOOL}, additionalProperties=False))
IDENT = obj({"issuer": STR, "subject": STR, "email": STR, "name": STR}, ["issuer", "subject"])
C("Membership", resource("membership", "mbr_", {"account": STR, "identity": IDENT, "role": STR, "status": enum("invited", "active", "suspended", "removed"),
    "source": enum("invitation", "jit", "scim", "idp_group", "api"), "last_sign_in_at": nullable(TS)}, ["account", "identity", "role", "status"]))
C("Invitation", resource("invitation", "inv_", {"account": STR, "email": STR, "role": STR, "status": enum("pending", "accepted", "revoked", "expired"),
    "expires_at": TS, "membership": nullable(STR)}, ["email", "role", "status"]))
C("Role", resource("role", "role_", {"name": STR, "scopes": arr(STR), "built_in": BOOL}, ["name", "scopes"]))
C("ApiKey", resource("api_key", "key_", {"account": STR, "name": STR, "mode": enum("test", "live"), "type": enum("secret", "restricted"), "scopes": arr(STR),
    "prefix": STR, "last4": STR, "secret": nullable(S("string", description="Only on create and roll")), "created_by": nullable(STR),
    "last_used_at": nullable(TS), "expires_at": nullable(TS), "allowed_ips": arr(STR)}, ["name", "mode", "type"]))
C("ApiKeyInput", obj({"name": STR, "mode": enum("test", "live"), "type": enum("secret", "restricted"), "scopes": arr(STR), "expires_at": TS, "allowed_ips": arr(STR)}, additionalProperties=False))

# ---------- products ----------
PROD_FIELDS = {"status": enum("active", "archived", "draft"), "sku": STR, "title": STR, "description": STR, "variant_of": nullable(STR),
    "options": obj({}, additionalProperties=STR), "category": STR, "brand": STR, "material": STR, "origin_country": STR,
    "manufacturer": obj({"name": STR, "country": STR, "mid": STR}), "unit_value": R("Money"), "unit_net_weight": R("Weight"),
    "unit_gross_weight": R("Weight"), "unit_dimensions": R("Dimensions"),
    "hs_codes": obj({"export": obj({}, additionalProperties=STR), "import": obj({}, additionalProperties=STR)}),
    "classification": nullable(obj({"source": STR, "reviewed": BOOL, "reviewed_at": nullable(TS)})),
    "compliance": nullable(R("ItemCompliance")), "dangerous_goods": nullable(R("DangerousGoods")),
    "barcodes": arr(obj({"type": STR, "value": STR})), "product_url": STR, "image_url": STR,
    "external_ids": arr(obj({"source": STR, "id": STR}, ["source", "id"]))}
C("Product", resource("product", "prod_", {**PROD_FIELDS, "restrictions": arr(RESTRICTION), "version": INT}, ["status", "sku"]))
C("ProductInput", obj({**PROD_FIELDS, "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("ProductUpsert", obj({"match": obj({"external_id": obj({"source": STR, "id": STR}), "sku": STR, "id": STR}), "product": R("ProductInput"),
    "fields_owned": arr(STR)}, ["match", "product"], additionalProperties=False))


# ---------- network ----------
C("InterlineAgreement", resource("interline_agreement", "ila_", {"status": enum("proposed", "active", "suspended", "terminated"),
    "from_carrier": STR, "to_carrier": STR, "handoff_points": arr(obj({"facility": STR, "cutoff_local_time": STR, "days": arr(DAYS)})),
    "services": obj({"from": arr(STR), "to": arr(STR)}), "label": enum("first_carrier", "relabel", "network"), "tracking_number": enum("first_carrier", "relabel", "network"),
    "handoff_fee": nullable(obj({"amount": INT, "currency": STR, "paid_by": STR})),
    "pricing": obj({"basis": enum("to_carrier_rate_sheet", "fixed", "revenue_share"), "rate_sheet": nullable(STR), "share": nullable(NUM), "amount": nullable(R("Money"))}),
    "liability": obj({"transfers_at": enum("receive_scan", "handoff_point_arrival"), "max_per_kg": R("Money")}),
    "data_sharing": obj({"policy": nullable(STR)}), "effective_from": DATE, "effective_until": nullable(DATE),
    "signatures": arr(obj({"account": STR, "signed_at": TS}))}, ["status", "from_carrier", "to_carrier"]))
C("InterlineAgreementInput", obj({"from_carrier": STR, "to_carrier": STR, "handoff_points": arr(obj({}, additionalProperties=True)), "services": obj({}, additionalProperties=True),
    "label": STR, "tracking_number": STR, "handoff_fee": obj({}, additionalProperties=True), "pricing": obj({}, additionalProperties=True),
    "liability": obj({}, additionalProperties=True), "data_sharing": obj({"policy": STR}), "effective_from": DATE, "effective_until": DATE, "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("LedgerEntry", resource("ledger_entry", "le_", {"type": enum("shipper_charge", "segment_charge", "handoff_fee", "network_fee", "adjustment", "claim", "refund"),
    "shipment": nullable(STR), "parent_shipment": nullable(STR), "debit_account": STR, "credit_account": STR, "amount": R("Money"),
    "basis": obj({}, additionalProperties=True), "status": enum("pending", "posted", "reversed")}, ["type", "debit_account", "credit_account", "amount", "status"]))
C("Settlement", resource("settlement", "stl_", {"account": STR, "period": obj({"from": DATE, "to": DATE}), "currency": STR,
    "totals": obj({"debits": R("Money"), "credits": R("Money"), "net": R("Money")}), "status": enum("open", "closed", "invoiced", "paid", "disputed"),
    "statement": nullable(STR)}, ["account", "period", "status"]))
C("NetworkServiceLevel", resource("service_level", "sla_", {"carrier": STR, "metric": enum("on_time_delivery", "first_attempt_success", "scan_compliance"),
    "target": NUM, "window_days": INT, "achieved": nullable(NUM)}, ["carrier", "metric", "target"]))

# ---------- iot ----------
C("Device", resource("device", "dev_", {"type": enum("scanner", "sorter", "locker", "telematics", "tracker_tag", "sensor", "gateway", "drone_autopilot", "driver_app"),
    "status": enum("active", "inactive", "offline"), "name": STR, "manufacturer": STR, "model": STR, "serial_number": STR,
    "attached_to": obj({"facility": nullable(STR), "vehicle": nullable(STR), "handling_unit": nullable(STR)}), "capabilities": arr(STR),
    "authentication": obj({"method": enum("mtls", "device_token", "gateway"), "certificate_fingerprint": nullable(STR), "expires_at": nullable(TS)}),
    "default_location": obj({"facility": nullable(STR)}), "last_seen_at": nullable(TS), "firmware": nullable(STR)}, ["type", "status"]))
C("DeviceInput", obj({"type": STR, "name": STR, "manufacturer": STR, "model": STR, "serial_number": STR, "capabilities": arr(STR),
    "authentication": obj({"method": enum("mtls", "device_token", "gateway")}), "default_location": obj({"facility": STR}), "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("DeviceEvent", obj({"id": STR, "device": STR, "type": enum("scan", "sensor", "position", "geofence", "locker"), "at": S("string", format="date-time"),
    "barcode": obj({"symbology": STR, "value": STR}), "parent": nullable(STR),
    "action": enum("inbound", "sort", "outbound", "load_vehicle", "delivery", "exception", "aggregate", "disaggregate", "deposited", "collected", "expired"),
    "reason": STR, "location": obj({"facility": STR, "zone": STR}), "readings": obj({}, additionalProperties=obj({"value": NUM, "unit": STR})),
    "latitude": NUM, "longitude": NUM, "speed": MEASURE(), "geofence": STR, "transition": enum("enter", "exit"), "slot": STR, "pin_issued": BOOL},
    ["id", "device", "type", "at"]))

# ---------- data network ----------
C("Participant", resource("participant", "ptc_", {"did": STR, "account": nullable(STR), "kinds": arr(STR),
    "verification_methods": arr(obj({"id": STR, "type": STR, "public_key_jwk": obj({}, additionalProperties=True)})),
    "credentials": arr(obj({"type": STR, "issuer": STR, "valid_until": DATE, "vc": STR})), "status": enum("active", "suspended", "revoked")}, ["did", "kinds", "status"]))
C("ParticipantRegister", obj({"did": STR, "kinds": arr(STR), "challenge_signature": STR}, ["did", "challenge_signature"], additionalProperties=False))
C("Record", obj({"id": STR, "object": enum("record"), "cid": STR, "subject": obj({"type": STR, "id": STR, "shipment": nullable(STR)}),
    "previous": nullable(STR), "producer": STR, "role": STR, "produced_at": STR, "schema": STR,
    "payload": obj({"encryption": STR, "key_id": STR, "location": STR, "size": INT}), "public_fields": obj({}, additionalProperties=True),
    "signature": obj({"alg": STR, "kid": STR, "value": STR}), "anchor": nullable(obj({"batch": STR, "merkle_proof": arr(STR), "status": STR}))},
    ["id", "object", "cid", "subject", "producer", "signature"]))
C("RecordCreate", obj({"subject": obj({"type": STR, "id": STR, "shipment": STR}), "object": obj({}, additionalProperties=True), "role": STR}, ["subject", "object"], additionalProperties=False))
C("Anchor", obj({"id": STR, "object": enum("anchor"), "ledger": obj({"network": STR, "contract": STR, "tx": STR, "block": INT}), "merkle_root": STR,
    "records": INT, "created": TS, "status": enum("pending", "submitted", "confirmed", "failed")}, ["id", "object", "merkle_root", "status"]))
C("Verification", obj({"valid": BOOL, "cid_matches": BOOL, "signature_valid": BOOL, "producer": STR, "anchored_at": nullable(TS), "ledger_tx": nullable(STR)}))
C("AccessPolicy", resource("access_policy", "pol_", {"rules": arr(obj({"role": STR, "objects": arr(STR), "fields": arr(STR), "scope": STR, "deny": BOOL, "require_credentials": arr(STR)}))}, ["rules"]))
C("AccessGrant", resource("access_grant", "grt_", {"grantor": STR, "grantee": STR, "subjects": obj({"shipments": arr(STR)}), "fields": arr(STR), "purpose": STR,
    "expires_at": nullable(TS), "status": enum("active", "revoked", "expired")}, ["grantor", "grantee", "status"]))
C("AccessGrantInput", obj({"grantee": STR, "subjects": obj({"shipments": arr(STR)}), "fields": arr(STR), "purpose": STR, "expires_at": TS}, ["grantee", "subjects"], additionalProperties=False))
C("Attestation", resource("attestation", "att_", {"attester": STR, "about": STR, "statement": STR, "evidence": arr(STR), "signature": obj({}, additionalProperties=True)}, ["attester", "about", "statement"]))

# ---------- consolidation ----------
C("Consolidation", resource("consolidation", "csl_", {"type": enum("bag", "sack", "tote", "cage", "gaylord", "pallet", "uld", "container", "trailer", "swap_body", "rail_wagon", "other"),
    "status": enum("open", "closed", "sealed", "loaded", "in_transit", "arrived", "deconsolidated"), "owner": STR,
    "identifiers": obj({"sscc": nullable(STR), "label": nullable(STR), "uld_id": nullable(STR), "container_number": nullable(STR), "postal_receptacle": nullable(STR)}),
    "type_code": nullable(STR), "parent": nullable(STR), "contents": obj({"consolidations": arr(STR), "handling_units": arr(STR)}),
    "counts": obj({"handling_units": INT, "shipments": INT, "consolidations": INT}), "weight": R("Weight"), "dimensions": nullable(R("Dimensions")),
    "origin": nullable(STR), "destination": nullable(STR), "seal": nullable(obj({"number": STR, "type": STR, "applied_at": TS, "applied_by": STR})),
    "dangerous_goods": obj({"contains": BOOL, "classes": arr(STR), "lithium": arr(STR), "declaration": nullable(STR)}),
    "customs": obj({"status": enum("not_required", "pending", "cleared", "held"), "reference": nullable(STR)}),
    "conveyance": nullable(STR), "documents": arr(R("Document")), "location": obj({"facility": nullable(STR), "at": nullable(TS)})}, ["type", "status", "owner"]))
C("ConsolidationInput", obj({"type": STR, "identifiers": obj({}, additionalProperties=nullable(STR)), "type_code": STR, "origin": STR, "destination": STR, "parent": STR,
    "user_metadata": R("UserMetadata")}, additionalProperties=False))
CONTENTS_IO = obj({"handling_units": arr(STR), "consolidations": arr(STR), "scans": arr(obj({"barcode": STR}))})
C("Conveyance", resource("conveyance", "cnv_", {"mode": enum("air", "sea", "road", "rail"), "route_run": nullable(STR), "leg": nullable(STR), "vehicle": nullable(STR),
    "operator": STR, "identifiers": obj({"flight_number": nullable(STR), "voyage_number": nullable(STR), "imo_number": nullable(STR), "trip_number": nullable(STR)}),
    "departure": obj({"location": STR, "unlocode": STR, "scheduled": STR, "actual": nullable(STR)}),
    "arrival": obj({"location": STR, "unlocode": STR, "scheduled": STR, "estimated": nullable(STR), "actual": nullable(STR)}),
    "status": enum("planned", "loading", "closed", "departed", "arrived", "unloaded", "cancelled"),
    "load": arr(obj({"consolidation": STR, "position": nullable(STR)})), "manifests": arr(obj({"type": STR, "document": STR})),
    "capacity": obj({"weight": R("Weight"), "positions": INT}), "used": obj({"weight": R("Weight"), "positions": INT})}, ["mode", "status", "operator"]))
C("ConveyanceInput", obj({"mode": STR, "route_run": STR, "leg": STR, "vehicle": STR, "identifiers": obj({}, additionalProperties=nullable(STR)),
    "departure": obj({}, additionalProperties=True), "arrival": obj({}, additionalProperties=True), "capacity": obj({}, additionalProperties=True), "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("Custody", obj({"object": enum("custody"), "shipment": STR, "chain": arr(obj({"handling_unit": STR, "consolidations": arr(STR), "conveyance": nullable(STR), "location": nullable(STR)}))}))

# ---------- templates ----------
C("DocumentTemplate", resource("document_template", "dtpl_", {"name": STR, "slug": STR, "type": STR, "status": CAT_STATUS, "version": INT,
    "related_object": enum("shipment", "order", "manifest", "pickup", "consolidation", "conveyance", "product", "route_run", "none"),
    "engine": enum("liquid", "zpl"), "source": STR, "assets": obj({}, additionalProperties=nullable(STR)),
    "page": obj({"size": STR, "orientation": enum("portrait", "landscape"), "margins_mm": NUM, "dpi": INT}), "formats": arr(enum("pdf", "png", "zpl", "html")),
    "locale": STR, "triggers": arr(obj({"event": STR, "conditions": obj({}, additionalProperties=True)})), "attach_to": enum("related_object", "none"),
    "default_for": arr(STR), "preview": nullable(obj({"object": STR, "url": STR}))}, ["name", "type", "related_object", "engine", "source", "status"]))
C("DocumentTemplateInput", obj({"name": STR, "slug": STR, "type": STR, "related_object": STR, "engine": STR, "source": STR, "assets": obj({}, additionalProperties=STR),
    "page": obj({}, additionalProperties=True), "formats": arr(STR), "locale": STR, "triggers": arr(obj({}, additionalProperties=True)),
    "attach_to": STR, "default_for": arr(STR), "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("DocumentGenerate", obj({"template": STR, "type": STR, "object": obj({"type": STR, "id": STR}), "data": obj({}, additionalProperties=True),
    "format": enum("pdf", "png", "zpl", "html"), "attach": BOOL, "locale": STR, "inline": BOOL, "options": obj({"copies": INT})}, additionalProperties=False))
C("DocumentJob", resource("document_job", "djob_", {"template": nullable(STR), "type": nullable(STR), "status": enum("processing", "completed", "completed_with_errors"),
    "counts": obj({"total": INT, "succeeded": INT, "failed": INT}), "output": enum("merged", "individual"), "result_file": nullable(STR),
    "errors": arr(obj({"object": STR, "code": STR, "message": STR}))}, ["status", "output"]))
C("DocumentJobCreate", obj({"template": STR, "type": STR, "objects": obj({"type": STR, "ids": arr(STR, maxItems=5000), "query": STR}), "format": STR,
    "output": enum("merged", "individual"), "attach": BOOL, "sort": STR}, ["objects"], additionalProperties=False))


# ---------- integrations ----------
C("Integration", obj({"id": STR, "object": enum("integration"), "name": STR,
    "kind": enum("carrier", "network", "3pl", "fleet", "address_validation", "insurance", "trade", "notifications"),
    "interfaces": obj({}, additionalProperties=obj({}, additionalProperties=True)), "connection_methods": arr(R("ConnectionMethod")),
    "config_schema": R("JsonSchema"), "federated": nullable(obj({"configuration": STR})), "pricing": nullable(obj({"model": STR, "documentation": STR})),
    "status": enum("available", "beta", "deprecated")}, ["id", "object", "name", "kind", "interfaces"]))
C("AddressValidation", obj({"id": STR, "object": enum("address_validation"), "status": enum("verified", "corrected", "ambiguous", "unverified", "invalid"),
    "deliverability": enum("deliverable", "deliverable_missing_unit", "undeliverable", "unknown"), "input": R("Address"), "suggested": nullable(R("Address")),
    "alternatives": arr(R("Address")), "components": obj({}, additionalProperties=nullable(STR)), "residential": nullable(BOOL),
    "geocode": nullable(obj({"latitude": NUM, "longitude": NUM, "accuracy": enum("rooftop", "parcel", "interpolated", "postal_code", "city")})),
    "changes": arr(STR), "connection": STR, "messages": R("Messages"), "carrier_metadata": R("CarrierMetadata")}, ["id", "object", "status"]))
C("AddressValidationRequest", obj({"address": R("Address"), "contact": nullable(R("Contact")), "connection": STR, "features": arr(STR)}, ["address"], additionalProperties=False))
C("InsuranceQuote", obj({"id": STR, "object": enum("insurance_quote"), "connection": STR, "provider": STR, "premium": R("Money"), "insured_value": R("Money"),
    "deductible": R("Money"), "coverage_types": arr(STR), "exclusions": arr(STR), "terms_url": STR, "expires_at": TS}, ["id", "object", "premium", "insured_value"]))
C("InsuranceQuoteRequest", obj({"shipment": STR, "insured_value": R("Money"), "coverage_types": arr(enum("loss", "damage", "delay", "theft")), "connections": arr(STR)}, ["insured_value"], additionalProperties=False))
C("Coverage", resource("coverage", "cov_", {"status": enum("pending", "active", "expired", "cancelled", "claimed"), "shipment": STR, "connection": STR,
    "policy_number": nullable(STR), "insured_value": R("Money"), "premium": R("Money"), "coverage_types": arr(STR),
    "period": obj({"starts": STR, "ends": STR, "days": INT}), "certificate": nullable(STR), "claims": arr(STR)}, ["status", "shipment", "insured_value"]))
C("CoverageCreate", obj({"quote": STR, "shipment": STR, "connection": STR, "insured_value": R("Money"), "user_metadata": R("UserMetadata")}, additionalProperties=False))
C("Claim", resource("claim", "clm_", {"coverage": STR, "type": enum("loss", "damage", "delay", "shortage"), "amount": R("Money"), "description": STR,
    "evidence": arr(STR), "status": enum("submitted", "under_review", "information_requested", "approved", "denied", "paid", "withdrawn"),
    "resolution": nullable(obj({"amount": R("Money"), "paid_at": nullable(TS), "reason": STR}))}, ["coverage", "type", "amount", "status"]))
C("ClaimInput", obj({"coverage": STR, "type": STR, "amount": R("Money"), "description": STR, "evidence": arr(STR), "user_metadata": R("UserMetadata")}, additionalProperties=False))

# ---------- jobs ----------
JOB_STATUS = enum("queued", "running", "succeeded", "partially_succeeded", "failed", "cancelling", "cancelled")
C("Job", resource("job", "job_", {"type": STR, "status": JOB_STATUS, "source": enum("api", "schedule", "system"), "schedule": nullable(STR),
    "subject": nullable(obj({"type": STR, "id": STR})), "parameters": obj({}, additionalProperties=True),
    "progress": obj({"total": nullable(INT), "completed": INT, "failed": INT, "percent": nullable(NUM), "eta_seconds": nullable(INT), "stage": nullable(STR)}),
    "attempt": INT, "max_attempts": INT, "priority": enum("low", "normal", "high"), "queued_at": TS, "started_at": nullable(TS), "finished_at": nullable(TS),
    "result": nullable(obj({"file": nullable(STR), "error_file": nullable(STR), "objects": nullable(obj({"type": STR, "ids": arr(STR)})), "summary": nullable(obj({}, additionalProperties=True))})),
    "errors": arr(obj({"item": STR, "code": STR, "message": STR})), "created_by": nullable(obj({"type": STR, "id": STR}))}, ["type", "status", "source", "progress"]))
C("JobCreate", obj({"type": STR, "parameters": obj({}, additionalProperties=True), "priority": enum("low", "normal", "high"), "user_metadata": R("UserMetadata")}, ["type"], additionalProperties=False))
C("JobLog", obj({"at": TS, "level": enum("debug", "info", "warning", "error"), "message": STR, "item": nullable(STR)}, ["at", "level", "message"]))
C("JobSchedule", resource("job_schedule", "jsch_", {"status": enum("active", "paused"), "type": STR, "parameters": obj({}, additionalProperties=True),
    "recurrence": R("Recurrence"), "overlap": enum("skip", "queue", "cancel_previous"), "next_run_at": nullable(TS), "last_job": nullable(STR),
    "last_status": nullable(JOB_STATUS)}, ["status", "type", "recurrence"]))
C("JobScheduleInput", obj({"type": STR, "parameters": obj({}, additionalProperties=True), "recurrence": R("Recurrence"), "overlap": enum("skip", "queue", "cancel_previous"),
    "user_metadata": R("UserMetadata")}, additionalProperties=False))


# ---------- billing ----------
PARTY_REF = obj({"account": nullable(STR), "integration": nullable(STR), "connection": nullable(STR), "name": STR, "tax_ids": arr(R("TaxId"))})
C("InvoiceLine", obj({"id": STR, "kind": enum("transport", "surcharge", "adjustment", "fee", "duty", "tax", "usage", "subscription", "credit"),
    "shipment": nullable(STR), "tracking_number": nullable(STR), "service": nullable(STR), "description": STR, "charge_kind": nullable(STR),
    "reason": nullable(enum("dimensional_reweigh", "weight_correction", "address_correction", "residential_reclassification", "service_change", "undeliverable_return")),
    "billed_weight": nullable(R("Weight")), "zone": nullable(STR), "declared": nullable(obj({}, additionalProperties=True)), "audited": nullable(obj({}, additionalProperties=True)),
    "meter": nullable(STR), "quantity": nullable(NUM), "unit_amount": nullable(NUM), "amount": R("Money"), "tax": nullable(R("Money")), "external_ref": nullable(STR)}, ["kind", "amount"]))
C("Invoice", resource("invoice", "invc_", {"kind": enum("transport", "usage", "settlement", "duties", "subscription", "credit_note"),
    "direction": enum("payable", "receivable"), "status": enum("draft", "open", "partially_paid", "paid", "overdue", "disputed", "void", "uncollectible"),
    "issuer": PARTY_REF, "recipient": PARTY_REF, "number": nullable(STR), "issued_on": nullable(DATE), "due_on": nullable(DATE),
    "period": nullable(obj({"from": DATE, "to": DATE})), "currency": STR, "lines": arr(R("InvoiceLine")),
    "totals": obj({"subtotal": R("Money"), "tax": R("Money"), "total": R("Money"), "paid": R("Money"), "due": R("Money")}),
    "reconciliation": nullable(obj({"id": STR, "status": STR, "matched": INT, "mismatched": INT, "unknown": INT, "disputed_amount": R("Money")})),
    "source": obj({"type": enum("issued", "import", "settlement", "usage_cycle"), "format": nullable(STR), "file": nullable(STR), "job": nullable(STR)}),
    "documents": arr(R("Document")), "payments": arr(STR), "external_ids": arr(obj({"source": STR, "id": STR}))}, ["kind", "status", "currency", "lines", "totals"]))
C("InvoiceInput", obj({"kind": STR, "recipient": PARTY_REF, "due_on": DATE, "period": obj({"from": DATE, "to": DATE}), "currency": STR,
    "lines": arr(R("InvoiceLine")), "user_metadata": R("UserMetadata")}, additionalProperties=False))
INV_FORMATS = enum("edi_210", "edifact_invoic", "ubl", "carrier_csv", "json", "csv")
C("ReconciliationLine", obj({"invoice_line": STR, "shipment": nullable(STR),
    "result": enum("matched", "amount_mismatch", "unknown_shipment", "voided_but_billed", "duplicate", "not_billed"),
    "expected": nullable(R("Money")), "billed": nullable(R("Money")), "cause": nullable(STR), "evidence": arr(STR),
    "suggested_action": nullable(enum("accept", "dispute", "rebill", "write_off")),
    "resolution": nullable(obj({"action": enum("accept", "dispute", "rebill", "write_off"), "note": STR, "at": TS}))}, ["invoice_line", "result"]))
C("Reconciliation", resource("reconciliation", "rcn_", {"type": enum("invoice_vs_shipments", "usage_vs_invoice"), "invoice": STR, "rules": nullable(STR),
    "status": enum("running", "completed", "failed"), "summary": obj({}, additionalProperties=True), "lines": arr(R("ReconciliationLine"))}, ["type", "invoice", "status"]))
C("Meter", resource("meter", "mtr_", {"key": STR, "name": STR, "source": obj({"event": nullable(STR), "reported": BOOL}),
    "aggregation": enum("count", "sum", "max", "unique"), "value_path": nullable(STR), "filters": obj({}, additionalProperties=True), "unit": STR,
    "status": enum("active", "archived")}, ["key", "source", "aggregation"]))
C("UsageRecord", resource("usage_record", "ur_", {"meter": STR, "account": STR, "quantity": NUM, "occurred_at": STR, "subject": nullable(obj({"type": STR, "id": STR})),
    "properties": obj({}, additionalProperties=True), "source": enum("event", "reported", "import"), "event": nullable(STR)}, ["meter", "account", "quantity", "occurred_at"]))
C("UsageRecordInput", obj({"meter": STR, "account": STR, "quantity": NUM, "occurred_at": STR, "subject": obj({"type": STR, "id": STR}),
    "properties": obj({}, additionalProperties=True)}, ["meter", "quantity", "occurred_at"], additionalProperties=False))
C("PricePlan", resource("price_plan", "plan_", {"name": STR, "currency": STR, "base_fee": nullable(obj({"amount": INT, "currency": STR, "interval": STR})),
    "prices": arr(obj({"meter": STR, "model": enum("per_unit", "graduated", "volume", "package", "percentage"), "unit_amount": NUM, "included": INT, "rate": NUM,
                       "tiers": arr(obj({"up_to": nullable(INT), "unit_amount": NUM})), "package": obj({"size": INT, "amount": INT})})),
    "minimum": nullable(obj({"amount": INT, "currency": STR, "interval": STR})), "status": enum("active", "archived")}, ["name", "currency", "prices"]))
C("BillingProfile", obj({"object": enum("billing_profile"), "account": STR, "currency": STR, "cycle": obj({"interval": enum("week", "month"), "anchor_day": INT}),
    "plans": arr(STR), "payment_methods": obj({"default": nullable(STR), "fallback": nullable(STR)}), "collection": enum("charge_automatically", "send_invoice"),
    "balance": obj({"enabled": BOOL, "auto_top_up": nullable(obj({"below": R("Money"), "amount": R("Money")}))}),
    "invoice_delivery": obj({"email": STR, "formats": arr(STR)}), "tax": obj({"ids": arr(R("TaxId")), "exempt": BOOL}), "payments_connection": nullable(STR)}, ["object", "account"]))
C("Balance", obj({"object": enum("balance"), "account": STR, "available": R("Money"), "pending": R("Money"), "low_balance_threshold": nullable(R("Money"))}))
C("BalanceTransaction", obj({"id": STR, "object": enum("balance_transaction"), "type": enum("top_up", "label_charge", "label_refund", "adjustment", "coverage_premium", "fee", "payout"),
    "amount": R("Money"), "balance_after": R("Money"), "source": nullable(obj({"type": STR, "id": STR})), "created": TS}, ["id", "object", "type", "amount"]))
C("PaymentMethod", resource("payment_method", "pm_", {"type": enum("card", "us_bank_account", "sepa_debit", "wallet", "invoice_terms"), "connection": STR,
    "brand": nullable(STR), "last4": nullable(STR), "exp_month": nullable(INT), "exp_year": nullable(INT), "bank_name": nullable(STR)}, ["type", "connection"]))
C("PaymentMethodSetup", obj({"client_secret": STR, "provider": STR, "hosted_url": nullable(STR), "expires_at": TS}))
C("Payment", resource("payment", "pay_", {"amount": R("Money"), "status": enum("requires_action", "processing", "succeeded", "failed", "refunded", "partially_refunded"),
    "invoice": nullable(STR), "purpose": enum("invoice", "top_up", "coverage"), "payment_method": STR, "connection": STR,
    "failure": nullable(obj({"code": STR, "message": STR})), "refunded": R("Money")}, ["amount", "status", "payment_method"]))
C("Refund", resource("refund", "rf_", {"payment": STR, "amount": R("Money"), "status": enum("pending", "succeeded", "failed"), "reason": nullable(STR)}, ["payment", "amount", "status"]))
C("Payout", resource("payout", "po_", {"account": STR, "amount": R("Money"), "settlement": nullable(STR), "connection": STR,
    "status": enum("pending", "in_transit", "paid", "failed", "cancelled"), "arrival_date": nullable(DATE)}, ["account", "amount", "status"]))


# ---------- inventory ----------
C("StorageLocation", resource("storage_location", "loc_", {"facility": STR, "code": STR, "path": obj({k: nullable(STR) for k in ["zone", "aisle", "rack", "shelf", "bin"]}),
    "type": enum("pick_face", "reserve", "bulk", "pallet_rack", "shelving", "cold", "frozen", "hazmat", "bonded", "quarantine", "returns", "staging", "dock"),
    "temperature_class": enum("ambient", "chilled", "frozen", "controlled_room_temperature"),
    "capacity": obj({"volume": nullable(MEASURE()), "weight": nullable(R("Weight")), "units": nullable(INT), "pallets": nullable(INT)}),
    "restrictions": obj({"hazmat_classes": arr(STR), "owners": nullable(arr(STR)), "max_sku_count": nullable(INT)}),
    "status": enum("active", "blocked", "retired"), "barcode": STR, "pick_sequence": INT}, ["facility", "code", "type"]))
LOT = obj({"number": STR, "manufactured_on": nullable(DATE), "expires_on": nullable(DATE)})
STOCK_STATUS = enum("available", "reserved", "picked", "damaged", "quarantine", "expired", "in_transit")
C("Stock", resource("stock", "stk_", {"owner": STR, "product": STR, "facility": STR, "location": STR, "status": STOCK_STATUS, "quantity": INT,
    "lot": nullable(LOT), "serials": nullable(arr(STR)), "handling_unit": nullable(STR)}, ["owner", "product", "facility", "status", "quantity"]))
C("InventoryLevel", obj({"object": enum("inventory_level"), "owner": STR, "product": STR, "facility": nullable(STR),
    **{k: INT for k in ["on_hand", "available", "reserved", "picked", "damaged", "quarantine", "inbound", "in_transit_out"]}, "as_of": TS}))
C("StockMovement", resource("stock_movement", "mov_", {"type": enum("receive", "putaway", "move", "reserve", "unreserve", "pick", "ship", "adjust", "status_change", "return", "transfer_out", "transfer_in"),
    "owner": STR, "product": STR, "quantity": INT, "from": nullable(obj({"location": nullable(STR), "status": nullable(STOCK_STATUS)})),
    "to": nullable(obj({"location": nullable(STR), "status": nullable(STOCK_STATUS)})), "lot": nullable(STR), "serials": nullable(arr(STR)),
    "reason": nullable(enum("count_variance", "damaged", "lost", "found", "expired", "quality_hold")),
    "reference": obj({"fulfillment_order": nullable(STR), "asn": nullable(STR), "count": nullable(STR)}), "source": enum("api", "device", "asn", "fulfillment", "count", "return"),
    "device_event": nullable(STR), "performed_by": nullable(obj({"type": STR, "id": STR})), "occurred_at": STR}, ["type", "owner", "product", "quantity"]))
C("StockMovementInput", obj({"type": enum("putaway", "move", "adjust", "status_change"), "product": STR, "quantity": INT,
    "from": obj({"location": STR, "status": STR}), "to": obj({"location": STR, "status": STR}), "lot": STR, "serials": arr(STR), "reason": STR, "occurred_at": STR},
    ["type", "product", "quantity"], additionalProperties=False))
FO_LINE = obj({"product": STR, "quantity": INT, "allocated": INT, "picked": INT, "packed": INT, "lot_policy": enum("fefo", "fifo", "specific")})
C("FulfillmentOrder", resource("fulfillment_order", "fo_", {"owner": STR,
    "status": enum("received", "allocated", "backordered", "picking", "packed", "shipped", "partially_shipped", "cancelled"),
    "channel": obj({"source": STR, "order_id": STR, "upstream_reference": STR}), "order": nullable(R("Order")), "ship_to": R("Contact"), "lines": arr(FO_LINE),
    "facility": nullable(STR), "allocation": obj({"strategy": STR, "split_allowed": BOOL, "decided_at": nullable(TS)}),
    "shipping": obj({"carrier_configs": R("CarrierConfigs"), "rate_shop": obj({}, additionalProperties=True), "promise": obj({"deliver_by": DATE})}),
    "packing": obj({"packaging": STR, "inserts": arr(STR), "gift_message": nullable(STR)}),
    "tasks": arr(obj({"type": STR, "location": STR, "product": STR, "quantity": INT, "status": STR, "wave": nullable(STR)})),
    "shipments": arr(STR), "documents": arr(R("Document"))}, ["owner", "status", "ship_to", "lines"]))
C("FulfillmentOrderInput", obj({"channel": obj({}, additionalProperties=STR), "order": R("Order"), "ship_to": R("Contact"),
    "lines": arr(obj({"product": STR, "quantity": INT, "lot_policy": STR}, ["product", "quantity"])), "facility": STR,
    "allocation": obj({"strategy": STR, "split_allowed": BOOL}), "shipping": obj({}, additionalProperties=True), "packing": obj({}, additionalProperties=True),
    "cancel_unfulfillable": BOOL, "user_metadata": R("UserMetadata")}, ["ship_to", "lines"], additionalProperties=False))
C("Wave", resource("wave", "wave_", {"facility": STR, "strategy": enum("zone", "batch", "single_order"), "status": enum("released", "in_progress", "completed"),
    "fulfillment_orders": arr(STR), "pick_list": nullable(STR)}, ["facility", "status"]))
C("InventoryCount", resource("inventory_count", "cnt_", {"facility": STR, "type": enum("cycle", "full", "spot"), "blind": BOOL, "status": enum("open", "completed", "approved"),
    "scope": obj({"locations": arr(STR), "products": arr(STR), "zone": nullable(STR)}),
    "lines": arr(obj({"location": STR, "product": STR, "lot": nullable(STR), "expected": nullable(INT), "counted": INT, "variance": nullable(INT), "value_variance": nullable(R("Money"))}))},
    ["facility", "type", "status"]))

# ---------- label specs & ingestion ----------
C("LabelSpec", resource("label_spec", "lspec_", {"owner": STR, "carrier": STR, "template": STR, "services": arr(STR), "sizes": arr(STR), "dpi": arr(INT),
    "required_fields": arr(STR), "barcodes": arr(obj({"role": STR, "symbology": STR, "payload": nullable(STR), "payload_schema": nullable(STR),
                                                       "min_module_width_mm": nullable(NUM), "quiet_zone_mm": nullable(NUM), "min_size_mm": nullable(NUM)})),
    "zones": arr(obj({"name": STR, "x_mm": NUM, "y_mm": NUM, "w_mm": NUM, "h_mm": NUM, "required": BOOL})),
    "tracking_numbers": obj({"format": STR, "allocation": enum("range", "api"), "check_digit": nullable(STR)}),
    "certification": obj({"required": BOOL, "samples": INT}), "version": INT, "status": CAT_STATUS}, ["carrier", "template", "status"]))
C("DocumentIngestion", obj({"id": STR, "object": enum("document_ingestion"), "status": enum("processing", "needs_review", "applied", "rejected", "failed"),
    "type": STR, "detected_type": nullable(STR), "format": enum("pdf_text", "pdf_scanned", "image", "edi_x12", "edifact", "ubl", "xml", "json"), "file": STR,
    "extraction": obj({"fields": obj({}, additionalProperties=obj({"value": {}, "confidence": NUM}, additionalProperties=True)),
                       "mapped": arr(obj({"target": STR, "value": {}}))}),
    "attach_to": nullable(obj({"type": STR, "id": STR})), "document": nullable(STR), "job": nullable(STR), "messages": R("Messages")}, ["id", "object", "status", "file"]))
C("DocumentIngestRequest", obj({"file": STR, "type": STR, "attach_to": obj({"type": STR, "id": STR}), "apply": enum("auto", "review", "none")}, ["file"], additionalProperties=False))


# ---------- timelines ----------
IDENT_REF = obj({"scheme": enum("tracking_number", "shipment", "sscc", "uld", "container", "awb", "postal_receptacle", "bag", "upstream_reference"), "value": STR, "carrier": nullable(STR)}, ["scheme", "value"])
C("IdentifierLink", obj({"id": STR, "object": enum("identifier_link"), "relation": enum("same_as", "contains"), "parent": IDENT_REF, "child": IDENT_REF,
    "valid_from": nullable(STR), "valid_to": nullable(STR), "producer": STR, "record": nullable(STR)}, ["object", "relation", "parent", "child"]))
C("IdentifierLinkInput", obj({"relation": enum("same_as", "contains"), "parent": IDENT_REF, "child": IDENT_REF, "valid_from": STR, "valid_to": STR}, ["relation", "parent", "child"], additionalProperties=False))
SOURCE = obj({"record": STR, "producer": STR, "via": nullable(IDENT_REF)})
C("Timeline", obj({"object": enum("timeline"), "shipment": STR, "identifiers": arr(IDENT_REF),
    "milestones": arr(obj({"milestone": STR, "occurred_at": STR, "status": enum("confirmed", "corroborated", "attested", "inferred", "disputed"),
                           "sources": arr(SOURCE), "conflicts": arr(obj({"record": STR, "producer": STR, "statement": STR}))})),
    "events": obj({"count": INT, "url": STR}), "gaps": arr(obj({"expected": STR, "after": nullable(STR), "reason": STR, "severity": enum("info", "warning", "critical")})),
    "eta": nullable(obj({"date": DATE, "source": STR})), "as_of": TS}, ["object", "shipment", "milestones"]))
C("MilestoneDefinitions", obj({"object": enum("milestone_definitions"), "version": STR,
    "milestones": arr(obj({"milestone": STR, "derived_from": arr(STR), "order": INT}))}))

def listof(name):
    return obj({"object": enum("list"), "url": STR, "has_more": BOOL, "data": arr(R(name))}, ["object", "has_more", "data"])
def searchof(name):
    return obj({"object": enum("search_result"), "has_more": BOOL, "next_page": nullable(STR), "data": arr(R(name))}, ["object", "has_more", "data"])

# ---------- paths ----------
paths = {}
P = {
  "Limit": {"name": "limit", "in": "query", "schema": S("integer", minimum=1, maximum=100, default=10)},
  "StartingAfter": {"name": "starting_after", "in": "query", "schema": STR},
  "EndingBefore": {"name": "ending_before", "in": "query", "schema": STR},
  "Expand": {"name": "expand[]", "in": "query", "schema": arr(STR), "style": "form", "explode": True},
  "IdempotencyKey": {"name": "Idempotency-Key", "in": "header", "schema": S("string", maxLength=255)},
  "IdempotencyKeyRequired": {"name": "Idempotency-Key", "in": "header", "required": True, "schema": S("string", maxLength=255)},
  "ShippingVersion": {"name": "Shipping-Version", "in": "header", "schema": STR, "example": "2026-10-01"},
  "ShippingAccount": {"name": "Shipping-Account", "in": "header", "schema": STR, "description": "Act on behalf of a connected account (acct_...)"},
  "Query": {"name": "query", "in": "query", "required": True, "schema": STR, "description": "Search query language (chapter 10 §3)"},
  "Page": {"name": "page", "in": "query", "schema": STR},
}
def pref(n): return {"$ref": f"#/components/parameters/{n}"}
COMMON = [pref("ShippingVersion"), pref("ShippingAccount")]
def resp(schema, code="200", desc="OK"):
    return {code: {"description": desc, "content": {"application/json": {"schema": schema}}}}
ERRS = {k: {"$ref": f"#/components/responses/{k}"} for k in ["BadRequest", "Unauthorized", "Forbidden", "NotFound", "Conflict", "CarrierError", "RateLimited", "CarrierUnavailable"]}
def errs(*codes):
    m = {"400": "BadRequest", "401": "Unauthorized", "403": "Forbidden", "404": "NotFound", "409": "Conflict", "422": "CarrierError", "429": "RateLimited", "502": "CarrierUnavailable"}
    return {c: {"$ref": f"#/components/responses/{m[c]}"} for c in codes}
STD = ("400", "401", "403", "429")

def op(tag, opid, summary, *, body=None, ok=None, params=(), code="200", extra_resp=None, desc=None, errors=STD, money=False, scopes=None):
    o = {"tags": [tag], "operationId": opid, "summary": summary, "parameters": COMMON + list(params)}
    if desc: o["description"] = desc
    if body is not None:
        o["requestBody"] = {"required": True, "content": {"application/json": {"schema": body}}}
    responses = {}
    if ok is not None: responses.update(resp(ok, code))
    if extra_resp: responses.update(extra_resp)
    responses.update(errs(*errors))
    o["responses"] = responses
    if money: o["x-spends-money"] = True
    if scopes: o["security"] = [{"apiKey": []}, {"oauth2": scopes}]
    return o
def path(p, **ops):
    paths.setdefault(p, {}).update(ops)
def idp(name="id"): return {"name": name, "in": "path", "required": True, "schema": STR}
def q(name, schema=STR, desc=None):
    d = {"name": name, "in": "query", "schema": schema}
    if desc: d["description"] = desc
    return d
LISTP = [pref("Limit"), pref("StartingAfter"), pref("EndingBefore"), pref("Expand")]
CREATED = [q("created[gte]", INT), q("created[lte]", INT)]

def crud(tag, coll, schema, *, create=None, update=None, delete=False, filters=(), search=False, create_money=False, create_idem=False, scope=None, create_summary=None, delete_summary=None):
    base = f"/v1/{coll}"
    singular = schema
    r, w = (f"{scope}:read", f"{scope}:write") if scope else (None, None)
    if create:
        path(base, post=op(tag, f"{coll}.create", create_summary or f"Create a {tag.lower().rstrip('s')}", body=R(create), ok=R(schema),
             params=[pref("IdempotencyKeyRequired" if create_idem else "IdempotencyKey")], errors=STD + ("409", "422", "502"), money=create_money, scopes=[w] if w else None))
    path(base, get=op(tag, f"{coll}.list", f"List {coll.replace('_', ' ')}", ok=listof(schema), params=LISTP + list(filters) + CREATED, scopes=[r] if r else None))
    if search:
        path(f"{base}/search", get=op(tag, f"{coll}.search", f"Search {coll.replace('_', ' ')}", ok=searchof(schema), params=[pref("Query"), pref("Limit"), pref("Page"), pref("Expand")], scopes=[r] if r else None))
    path(f"{base}/{{id}}", parameters=[idp()],
         get=op(tag, f"{coll}.retrieve", f"Retrieve a {singular}", ok=R(schema), params=[pref("Expand")], errors=STD + ("404",), scopes=[r] if r else None))
    if update:
        path(f"{base}/{{id}}", post=op(tag, f"{coll}.update", f"Update a {singular}", body=R(update), ok=R(schema), errors=STD + ("404", "409"), scopes=[w] if w else None))
    if delete:
        path(f"{base}/{{id}}", delete=op(tag, f"{coll}.delete", delete_summary or f"Delete a {singular}", ok=R("Deleted"), errors=STD + ("404", "409"), scopes=[w] if w else None))

def action(tag, p, opid, summary, *, body=None, ok, idem=False, money=False, errors=STD + ("404", "409", "422", "502"), code="200", scope=None, desc=None, extra_resp=None):
    params = [pref("IdempotencyKeyRequired")] if idem else [pref("IdempotencyKey")]
    path(p, parameters=[idp()] if "{id}" in p else [], post=op(tag, opid, summary, body=body if body is not None else obj({}), ok=ok, params=params, errors=errors, money=money, code=code, scopes=[scope] if scope else None, desc=desc, extra_resp=extra_resp))

# Rates
path("/v1/rates", post=op("Rates", "rates.create", "Get live rates", body=R("RateRequest"), ok=R("RateQuote"),
     desc="Fans out to every eligible connection. Partial carrier failure returns 200 with `errors[]`. Send `Accept: text/event-stream` for streaming (capability rates.stream).",
     scopes=["rates:read"]))
path("/v1/rate_quotes/{id}", parameters=[idp()], get=op("Rates", "rate_quotes.retrieve", "Retrieve a rate quote", ok=R("RateQuote"), params=[pref("Expand")], errors=STD + ("404",), scopes=["rates:read"]))

# Shipments
crud("Shipments", "shipments", "Shipment", create="ShipmentCreate", update="ShipmentUpdate", delete=True, search=True, scope="shipments",
     create_summary="Create a shipment (draft, or purchase with `purchase: true`)", delete_summary="Delete a draft shipment",
     filters=[q("status", R("ShipmentStatus")), q("tracking.status", R("TrackingStatus")), q("carrier"), q("connection"), q("purchase.service.code"), q("tracking.number"), q("reference"), q("order.id"), q("returns.is_return", BOOL), q("handover.manifest", desc="ID or `none`"), q("handover.pickup", desc="ID or `none`"), q("handover.close_group"), q("ship_date[gte]", DATE), q("ship_date[lte]", DATE)])
paths["/v1/shipments"]["post"]["x-spends-money"] = True
paths["/v1/shipments"]["post"]["responses"].update(resp(R("Shipment"), "202", "Purchase in progress (status `purchasing`)"))
paths["/v1/shipments"]["post"]["description"] = "`Idempotency-Key` is REQUIRED when the body carries a `purchase` instruction."
action("Shipments", "/v1/shipments/{id}/purchase", "shipments.purchase", "Purchase a label", body=R("ShipmentPurchase"), ok=R("Shipment"), idem=True, money=True, scope="shipments:write",
       extra_resp=resp(R("Shipment"), "202", "Purchase in progress"))
action("Shipments", "/v1/shipments/{id}/void", "shipments.void", "Void a label", body=R("ShipmentVoid"), ok=R("Shipment"), scope="shipments:write")
action("Shipments", "/v1/shipments/{id}/rates", "shipments.rates", "Re-rate a draft shipment", body=R("RateFilters"), ok=R("RateQuote"), scope="shipments:write")
action("Shipments", "/v1/shipments/{id}/return", "shipments.return", "Create a return shipment", body=R("ShipmentReturn"), ok=R("Shipment"), idem=True, money=True, scope="shipments:write")
action("Shipments", "/v1/shipments/{id}/label", "shipments.label", "Re-render the label", body=R("LabelFormat"), ok=R("Document"), scope="shipments:write")

# Pickups
path("/v1/pickups/availability", post=op("Pickups", "pickups.availability", "Check pickup availability", body=R("PickupAvailabilityRequest"), ok=R("PickupAvailability"), errors=STD + ("422", "502"), scopes=["pickups:write"]))
crud("Pickups", "pickups", "Pickup", create="PickupCreate", update="PickupUpdate", search=True, create_idem=True, create_money=True, scope="pickups",
     create_summary="Book a pickup",
     filters=[q("status"), q("carrier"), q("connection"), q("date[gte]", DATE), q("date[lte]", DATE)])
action("Pickups", "/v1/pickups/{id}/cancel", "pickups.cancel", "Cancel a pickup", body=obj({"reason": STR}), ok=R("Pickup"), scope="pickups:write")

# Manifests
crud("Manifests", "manifests", "Manifest", create="ManifestCreate", update="MetadataUpdate", create_idem=True, scope="manifests",
     create_summary="Create (close out) one or more manifests", filters=[q("status"), q("mode"), q("trigger"), q("group"), q("carrier"), q("connection"), q("ship_date", DATE)])
paths["/v1/manifests"]["post"]["responses"].update(resp(R("Manifest"), "202", "Pending (async carrier)"))
paths["/v1/manifests"]["post"]["responses"]["200"]["content"]["application/json"]["schema"] = {"oneOf": [R("Manifest"), listof("Manifest")]}
paths["/v1/manifests"]["post"]["description"] = "Returns a `list` when `split: auto` produced several manifests (one per carrier scope)."
path("/v1/manifests/preview", post=op("Manifests", "manifests.preview", "Preview the day's close-out", body=R("ManifestPreviewRequest"), ok=R("ManifestPreview"), scopes=["manifests:read"]))
action("Manifests", "/v1/manifests/{id}/reprint", "manifests.reprint", "Re-fetch manifest documents", ok=R("Manifest"), scope="manifests:write")

# Files
path("/v1/files", post={"tags": ["Files"], "operationId": "files.create", "summary": "Upload a file", "parameters": COMMON + [pref("IdempotencyKey")],
     "requestBody": {"required": True, "content": {
        "multipart/form-data": {"schema": obj({"file": S("string", format="binary"), "purpose": FILE_PURPOSE, "user_metadata": R("UserMetadata")}, ["file", "purpose"])},
        "application/json": {"schema": R("FileCreateJson")}}},
     "responses": {**resp(R("File")), **errs(*STD)}, "security": [{"apiKey": []}, {"oauth2": ["documents:write"]}]})
crud("Files", "files", "File", delete=True, filters=[q("purpose")], scope="documents")
path("/v1/files/{id}/contents", parameters=[idp()], get={"tags": ["Files"], "operationId": "files.contents", "summary": "Download file contents", "parameters": COMMON,
     "responses": {"200": {"description": "File bytes", "content": {"application/octet-stream": {"schema": S("string", format="binary")}}}, **errs("401", "404")}})

# Document uploads
crud("Document Uploads", "document_uploads", "DocumentUpload", create="DocumentUploadCreate", update="MetadataUpdate", scope="documents",
     create_summary="Submit customs documents to a carrier", filters=[q("status"), q("stage"), q("shipment"), q("connection")])

# Trackers
crud("Tracking", "trackers", "Tracker", create="TrackerCreate", update="TrackerUpdate", delete=True, search=True, scope="trackers",
     create_summary="Create a tracker", delete_summary="Discard a tracker",
     filters=[q("status", R("TrackingStatus")), q("status_detail"), q("carrier"), q("connection"), q("tracking_number"), q("shipment")])
action("Tracking", "/v1/trackers/{id}/refresh", "trackers.refresh", "Force a carrier poll", ok=R("Tracker"), scope="trackers:write")
path("/v1/trackers/{id}/events", parameters=[idp()], get=op("Tracking", "trackers.events", "List tracking events", ok=listof("TrackingEvent"), params=LISTP, errors=STD + ("404",), scopes=["trackers:read"]))

# Webhooks
crud("Webhooks", "webhook_endpoints", "WebhookEndpoint", create="WebhookEndpointCreate", update="WebhookEndpointUpdate", delete=True, scope="webhooks",
     create_summary="Create a webhook endpoint", filters=[q("status")])
action("Webhooks", "/v1/webhook_endpoints/{id}/rotate_secret", "webhook_endpoints.rotate_secret", "Rotate the signing secret",
       body=obj({"expire_previous_in": S("integer", minimum=0, maximum=604800, default=86400)}), ok=R("WebhookEndpoint"), scope="webhooks:write")
action("Webhooks", "/v1/webhook_endpoints/{id}/test", "webhook_endpoints.test", "Send a test event", body=obj({"type": STR}), ok=R("WebhookDelivery"), scope="webhooks:write")
path("/v1/events", get=op("Events", "events.list", "List events", ok=listof("Event"), params=LISTP + [q("type", desc="Wildcards allowed, e.g. tracker.*"), q("related[shipment]"), q("related[tracker]")] + CREATED))
path("/v1/events/{id}", parameters=[idp()], get=op("Events", "events.retrieve", "Retrieve an event", ok=R("Event"), errors=STD + ("404",)))
path("/v1/events/{id}/deliveries", parameters=[idp()], get=op("Events", "events.deliveries", "List delivery attempts", ok=listof("WebhookDelivery"), params=LISTP, errors=STD + ("404",)))
action("Events", "/v1/events/{id}/redeliver", "events.redeliver", "Redeliver an event", body=obj({"webhook_endpoint": STR}),
       ok=obj({"object": enum("list"), "data": arr(R("WebhookDelivery"))}), scope="webhooks:write")

# Inbound
path("/v1/inbound/{connection_id}", parameters=[idp("connection_id")], post={"tags": ["Inbound"], "operationId": "inbound.carrier_push",
     "summary": "Carrier push receiver (carrier-native payload)", "security": [],
     "description": "Authenticated by the carrier's own signature scheme as declared in `carrier.inbound`. The body is carrier-native.",
     "requestBody": {"required": True, "content": {"*/*": {"schema": {}}}},
     "responses": {"200": {"description": "Accepted (response shape is whatever the carrier expects)"}, "401": {"description": "Signature verification failed"}}})
crud("Inbound", "inbound_events", "InboundEvent", create="InboundEventCreate", scope="inbound", create_summary="Inject canonical events",
     filters=[q("type"), q("status"), q("connection"), q("tracker")])
action("Test Helpers", "/v1/test_helpers/trackers/{id}/advance", "test_helpers.trackers.advance", "Advance a test tracker",
       body=obj({"to": R("TrackingStatus"), "script": enum("standard", "failed_attempt", "customs_hold", "return_to_sender", "lost")}), ok=R("Tracker"))
action("Test Helpers", "/v1/test_helpers/shipments/{id}/charge_adjustment", "test_helpers.shipments.charge_adjustment", "Simulate a carrier charge adjustment",
       body=obj({"charges": arr(R("Charge"))}), ok=R("Shipment"))

# Carriers, connections, apps
path("/v1/carriers", get=op("Carriers", "carriers.list", "List carriers", ok=listof("Carrier"), params=LISTP + [q("capability"), q("country"), q("status")]))
path("/v1/carriers/{id}", parameters=[idp()], get=op("Carriers", "carriers.retrieve", "Retrieve a carrier", ok=R("Carrier"), errors=STD + ("404",)))
crud("Connections", "connections", "Connection", create="ConnectionCreate", update="ConnectionUpdate", delete=True, scope="connections",
     create_summary="Create a credentials-based connection", filters=[q("carrier"), q("method"), q("status"), q("ownership"), q("default", BOOL)])
action("Connections", "/v1/connections/{id}/verify", "connections.verify", "Verify connection credentials", ok=R("Connection"), scope="connections:write")
path("/v1/connect_sessions", post=op("Connections", "connect_sessions.create", "Start an OAuth/OIDC connect flow", body=R("ConnectSessionCreate"), ok=R("ConnectSession"), errors=STD + ("422",), scopes=["connections:write"]))
path("/v1/connect_sessions/{id}", parameters=[idp()], get=op("Connections", "connect_sessions.retrieve", "Retrieve a connect session", ok=R("ConnectSession"), errors=STD + ("404",), scopes=["connections:read"]))
crud("Apps", "apps", "App", create="AppCreate", update="AppUpdate", delete=True, scope="connections",
     create_summary="Register a carrier OAuth app", filters=[q("carrier"), q("visibility"), q("status")])
paths["/v1/apps/{id}"]["delete"]["parameters"].append(q("cascade", BOOL))
action("Apps", "/v1/apps/{id}/rotate_secret", "apps.rotate_secret", "Rotate a dynamic app's client secret", ok=R("App"), scope="connections:write")
path("/v1/oauth/callback", get={"tags": ["Connections"], "operationId": "oauth.callback", "summary": "Carrier OAuth redirect target", "security": [],
     "parameters": [q("code"), q("state"), q("error")], "responses": {"302": {"description": "Redirect to connect_session.return_url"}}})

# Batches
path("/v1/batches", post=op("Batches", "batches.create", "Create a batch", body=R("BatchCreate"), ok=R("Batch"), params=[pref("IdempotencyKeyRequired")], code="202"))
path("/v1/batches/{id}", parameters=[idp()], get=op("Batches", "batches.retrieve", "Retrieve a batch", ok=R("Batch"), errors=STD + ("404",)))


# Pickup schedules
crud("Pickup Schedules", "pickup_schedules", "PickupSchedule", create="PickupScheduleCreate", update="PickupScheduleUpdate", create_idem=True, scope="pickups",
     create_summary="Create a pickup schedule", filters=[q("status"), q("connection"), q("carrier"), q("management")])
for act, body in [("pause", obj({"until": DATE})), ("resume", obj({})), ("cancel", obj({})), ("skip", obj({"dates": arr(DATE)})), ("add", obj({"dates": arr(DATE)}))]:
    action("Pickup Schedules", f"/v1/pickup_schedules/{{id}}/{act}", f"pickup_schedules.{act}", f"{act.capitalize()} a pickup schedule", body=body, ok=R("PickupSchedule"), scope="pickups:write")
path("/v1/pickup_schedules/{id}/occurrences", parameters=[idp()], get=op("Pickup Schedules", "pickup_schedules.occurrences", "List occurrences",
     ok=obj({"object": enum("list"), "data": arr(obj({"date": DATE, "status": STR, "pickup": nullable(STR)}))}), params=[q("from", DATE), q("to", DATE)], errors=STD + ("404",)))

# Trade
crud("Trade", "classifications", "Classification", create="ClassificationCreate", scope="trade", create_summary="Classify items")
action("Trade", "/v1/classifications/{id}/apply", "classifications.apply", "Apply classification to a draft shipment",
       body=obj({"shipment": STR, "items": arr(INT), "import_country": STR}, ["shipment"]), ok=R("Shipment"), scope="trade:write")
action("Trade", "/v1/classifications/{id}/feedback", "classifications.feedback", "Submit classification feedback",
       body=obj({"index": INT, "export": obj({"hs_code": STR}), "import": obj({"country": STR, "hs_code": STR}), "reason": STR}), ok=R("Classification"), scope="trade:write")
crud("Trade", "compliance_screenings", "ComplianceScreening", create="ComplianceScreeningCreate", scope="trade", create_summary="Screen parties and goods")
crud("Trade", "landed_costs", "LandedCost", create="LandedCostCreate", scope="trade", create_summary="Quote landed cost")
path("/v1/tariffs/{country}/{hs_code}", parameters=[idp("country"), idp("hs_code")],
     get=op("Trade", "tariffs.retrieve", "Look up a tariff line", ok=R("Tariff"), params=[q("origin_country"), q("date", DATE)], errors=STD + ("404",)))
crud("Trade", "duty_collections", "DutyCollection", scope="trade", filters=[q("status"), q("shipment")])
action("Trade", "/v1/duty_collections/{id}/pay", "duty_collections.pay", "Pay a duty collection", body=obj({"payment_method": STR}), ok=R("DutyCollection"), idem=True, money=True, scope="trade:write")
action("Trade", "/v1/duty_collections/export", "duty_collections.export", "Export duty collections", body=obj({"filters": obj({}, additionalProperties=True)}), ok=R("File"), scope="trade:read")

# Catalog
path("/v1/service_availability", post=op("Catalog", "service_availability.create", "Check serviceability", body=R("ServiceAvailabilityRequest"), ok=R("ServiceAvailability")))
for coll, sch, scn in [("services", "CatalogService", "service"), ("options", "CatalogOption", "option"), ("packagings", "Packaging", "packaging"), ("zones", "Zone", "zone")]:
    crud("Catalog", coll, sch, create=sch, update=sch, delete=True, scope="catalog", create_summary=f"Create a {scn}", delete_summary=f"Delete a draft {scn}", filters=[q("status")])
    action("Catalog", f"/v1/{coll}/{{id}}/publish", f"{coll}.publish", f"Publish a {scn}", body=obj({"effective_from": DATE}), ok=R(sch), scope="catalog:write")
    path(f"/v1/{coll}/{{id}}/versions", parameters=[idp()], get=op("Catalog", f"{coll}.versions", f"List {scn} versions", ok=listof(sch), params=LISTP, errors=STD + ("404",)))
path("/v1/zones/match", post=op("Catalog", "zones.match", "Match an address to zones", body=obj({"address": R("Address"), "purpose": STR}, ["address"]), ok=R("ZoneMatch")))

# Pricing
crud("Pricing", "rate_sheets", "RateSheet", create="RateSheet", update="RateSheet", delete=True, scope="pricing", create_summary="Create a rate sheet",
     delete_summary="Delete a draft rate sheet", filters=[q("status"), q("service")])
action("Pricing", "/v1/rate_sheets/{id}/publish", "rate_sheets.publish", "Publish a rate sheet", body=obj({"effective_from": DATE}), ok=R("RateSheet"), scope="pricing:write")
action("Pricing", "/v1/rate_sheets/{id}/simulate", "rate_sheets.simulate", "Simulate prices", body=obj({**RATE_REQ_PROPS, "version": STR}),
       ok=obj({"object": enum("list"), "data": arr(R("Rate"))}), scope="pricing:read")
path("/v1/rate_sheets/{id}/versions", parameters=[idp()], get=op("Pricing", "rate_sheets.versions", "List rate sheet versions", ok=listof("RateSheet"), params=LISTP, errors=STD + ("404",)))
path("/v1/rate_sheets/import", post=op("Pricing", "rate_sheets.import", "Import a rate sheet", body=obj({"file": STR, "format": enum("csv", "xlsx"), "template": STR}, ["file"]), ok=R("RateSheet")))
path("/v1/rate_sheets/{id}/export", parameters=[idp()], get={"tags": ["Pricing"], "operationId": "rate_sheets.export", "summary": "Export a rate sheet", "parameters": COMMON + [q("format", enum("csv", "xlsx"))],
     "responses": {"200": {"description": "File", "content": {"text/csv": {"schema": STR}}}, **errs("401", "404")}})
crud("Pricing", "surcharges", "Surcharge", create="Surcharge", update="Surcharge", delete=True, scope="pricing", create_summary="Create a surcharge", filters=[q("kind"), q("status")])
action("Pricing", "/v1/surcharges/{id}/schedule", "surcharges.schedule", "Add a schedule entry", body=obj({"effective_from": DATE, "rate": NUM, "amount": R("Money")}, ["effective_from"]), ok=R("Surcharge"), scope="pricing:write")
crud("Pricing", "pricing_rules", "PricingRule", create="PricingRule", update="PricingRule", delete=True, scope="pricing", create_summary="Create a pricing rule", filters=[q("type"), q("status")])

# Routes
crud("Routes", "facilities", "Facility", create="Facility", update="Facility", delete=True, scope="routes", create_summary="Create a facility", filters=[q("type"), q("status")])
crud("Routes", "routes", "Route", create="RouteCreate", update="RouteUpdate", delete=True, scope="routes", create_summary="Create a route", filters=[q("type"), q("status")])
for act in ["activate", "deactivate"]:
    action("Routes", f"/v1/routes/{{id}}/{act}", f"routes.{act}", f"{act.capitalize()} a route", ok=R("Route"), scope="routes:write")
action("Routes", "/v1/routes/{id}/stops", "routes.stops.create", "Insert a stop", body=R("StopInput"), ok=R("Route"), scope="routes:write")
path("/v1/routes/{id}/stops/{stop_id}", parameters=[idp(), idp("stop_id")],
     post=op("Routes", "routes.stops.update", "Update a stop", body=R("StopInput"), ok=R("Route"), errors=STD + ("404", "409")),
     delete=op("Routes", "routes.stops.delete", "Remove a stop", ok=R("Route"), errors=STD + ("404", "409")))
action("Routes", "/v1/routes/{id}/stops/reorder", "routes.stops.reorder", "Reorder stops", body=obj({"order": arr(STR)}, ["order"]), ok=R("Route"), scope="routes:write")
path("/v1/routes/{id}/legs", parameters=[idp()], get=op("Routes", "routes.legs.list", "List legs", ok=obj({"object": enum("list"), "data": arr(R("Leg"))}), errors=STD + ("404",)))
path("/v1/routes/{id}/legs/{leg_id}", parameters=[idp(), idp("leg_id")], post=op("Routes", "routes.legs.update", "Update a leg", body=R("LegUpdate"), ok=R("Leg"), errors=STD + ("404",)))
crud("Routes", "route_runs", "RouteRun", create="RouteRunCreate", update="RouteRunCreate", scope="routes", create_summary="Create a route run",
     filters=[q("route"), q("date", DATE), q("status"), q("vehicle"), q("driver")])
for act, body in [("dispatch", obj({"vehicle": STR, "driver": STR})), ("start", obj({})), ("complete", obj({})), ("cancel", obj({"reason": STR})),
                  ("assign", obj({"shipments": arr(STR), "stop": STR, "activity": STR}, ["shipments"])), ("unassign", obj({"shipments": arr(STR)}, ["shipments"])),
                  ("optimize", obj({"lock_completed_stops": BOOL}))]:
    action("Routes", f"/v1/route_runs/{{id}}/{act}", f"route_runs.{act}", f"{act.capitalize()} a route run", body=body, ok=R("RouteRun"), scope="routes:write")
for act in ["arrive", "complete", "fail", "skip"]:
    path(f"/v1/route_runs/{{id}}/stops/{{stop_id}}/{act}", parameters=[idp(), idp("stop_id")],
         post=op("Routes", f"route_runs.stops.{act}", f"Stop: {act}", body=R("StopOutcome"), ok=R("RouteRun"), errors=STD + ("404", "409")))
for act in ["depart", "arrive"]:
    path(f"/v1/route_runs/{{id}}/legs/{{leg_id}}/{act}", parameters=[idp(), idp("leg_id")],
         post=op("Routes", f"route_runs.legs.{act}", f"Leg: {act}", body=obj({"at": STR}), ok=R("RouteRun"), errors=STD + ("404", "409")))
path("/v1/route_runs/{id}/positions", parameters=[idp()],
     post=op("Fleet", "route_runs.positions.create", "Report positions", body=obj({"positions": arr(R("Position"), maxItems=500)}, ["positions"]), ok=obj({"accepted": INT}), errors=STD + ("404",)),
     get=op("Fleet", "route_runs.positions.list", "List positions", ok=obj({"object": enum("list"), "data": arr(R("Position"))}), params=[q("since", STR)], errors=STD + ("404",)))
path("/v1/journeys/plan", post=op("Routes", "journeys.plan", "Plan a journey", body=R("JourneyPlanRequest"), ok=R("Journey")))
path("/v1/shipments/{id}/journey", parameters=[idp()], get=op("Routes", "shipments.journey", "Retrieve a shipment's journey", ok=R("Journey"), errors=STD + ("404",)))
action("Routes", "/v1/shipments/{id}/journey/replan", "shipments.journey.replan", "Replan a journey",
       body=obj({"reason": STR, "avoid": obj({"facilities": arr(STR), "runs": arr(STR)})}), ok=R("Journey"), scope="routes:write")

# Fleet
crud("Fleet", "vehicles", "Vehicle", create="Vehicle", update="Vehicle", delete=True, scope="fleet", create_summary="Create a vehicle", filters=[q("type"), q("status")])
path("/v1/vehicles/{id}/position", parameters=[idp()], get=op("Fleet", "vehicles.position", "Latest vehicle position", ok=R("Position"), errors=STD + ("404",)))
crud("Fleet", "drivers", "Driver", create="Driver", update="Driver", delete=True, scope="fleet", create_summary="Create a driver", filters=[q("status")])
crud("Fleet", "optimizations", "Optimization", create="OptimizationCreate", scope="fleet", create_summary="Optimize runs")
action("Fleet", "/v1/optimizations/{id}/commit", "optimizations.commit", "Commit proposed runs", ok=R("Optimization"), scope="fleet:write")


# Injection
action("Injection", "/v1/shipments/{id}/cancel_injection", "shipments.cancel_injection", "Cancel an injected shipment", body=obj({"reason": STR}), ok=R("Shipment"), scope="injection:write")
crud("Injection", "asns", "Asn", create="AsnCreate", update="AsnUpdate", create_idem=True, scope="injection", create_summary="Create an advance shipping notice",
     filters=[q("partner"), q("facility"), q("status"), q("expected_at[gte]", STR), q("expected_at[lte]", STR)])
for act, body in [("dispatch", obj({})), ("arrive", obj({"at": STR})), ("cancel", obj({"reason": STR})), ("close", obj({})),
                  ("receive", obj({"scans": arr(SCAN, maxItems=1000)}, ["scans"]))]:
    action("Injection", f"/v1/asns/{{id}}/{act}", f"asns.{act}", f"ASN: {act}", body=body, ok=R("Asn"), scope="injection:write")

# Accounts & identity
crud("Accounts", "accounts", "Account", create="AccountCreate", update="AccountUpdate", scope="accounts", create_summary="Create a child account",
     filters=[q("type"), q("status")])
for act in ["suspend", "reactivate", "close"]:
    action("Accounts", f"/v1/accounts/{{id}}/{act}", f"accounts.{act}", f"{act.capitalize()} an account", ok=R("Account"), scope="accounts:write")
path("/v1/account", get=op("Accounts", "account.retrieve", "Retrieve the current account", ok=R("Account")))
crud("Accounts", "identity_providers", "IdentityProvider", create="IdentityProviderInput", update="IdentityProviderInput", delete=True, scope="accounts",
     create_summary="Register an identity provider", filters=[q("type"), q("status")])
action("Accounts", "/v1/identity_providers/{id}/verify_domain", "identity_providers.verify_domain", "Verify a domain", body=obj({"domain": STR}, ["domain"]), ok=R("IdentityProvider"), scope="accounts:write")
action("Accounts", "/v1/identity_providers/{id}/test", "identity_providers.test", "Test sign-in", ok=obj({"url": STR}), scope="accounts:write")
crud("Accounts", "memberships", "Membership", update="Membership", delete=True, scope="accounts", filters=[q("role"), q("status")])
crud("Accounts", "invitations", "Invitation", create="Invitation", scope="accounts", create_summary="Invite a member", filters=[q("status")])
action("Accounts", "/v1/invitations/{id}/revoke", "invitations.revoke", "Revoke an invitation", ok=R("Invitation"), scope="accounts:write")
crud("Accounts", "roles", "Role", create="Role", update="Role", delete=True, scope="accounts", create_summary="Create a custom role")
crud("Accounts", "api_keys", "ApiKey", create="ApiKeyInput", update="ApiKeyInput", delete=True, scope="accounts", create_summary="Create an API key", filters=[q("mode"), q("type")])
action("Accounts", "/v1/api_keys/{id}/roll", "api_keys.roll", "Roll an API key", body=obj({"expire_previous_in": INT}), ok=R("ApiKey"), scope="accounts:write")

# Products
crud("Products", "products", "Product", create="ProductInput", update="ProductInput", delete=True, search=True, scope="products",
     create_summary="Create a product", delete_summary="Delete an unreferenced product",
     filters=[q("status"), q("category"), q("origin_country"), q("variant_of"), q("updated[gte]", INT), q("external_ids[source]")])
paths["/v1/products/{id}"]["post"]["parameters"].append({"name": "If-Match", "in": "header", "schema": STR, "description": "Product version for optimistic concurrency"})
path("/v1/products/upsert", post=op("Products", "products.upsert", "Upsert a product", body=R("ProductUpsert"), ok=R("Product"), scopes=["products:write"]))
path("/v1/products/import", post=op("Products", "products.import", "Import products from a file", body=obj({"file": STR, "mapping": obj({}, additionalProperties=STR)}, ["file"]), ok=R("Batch")))
for act in ["archive", "unarchive"]:
    action("Products", f"/v1/products/{{id}}/{act}", f"products.{act}", f"{act.capitalize()} a product", ok=R("Product"), scope="products:write")


# Network
for act in ["list", "pause", "delist"]:
    action("Network", f"/v1/accounts/{{id}}/{act}", f"accounts.member_{act}", f"{act.capitalize()} a carrier member", ok=R("Account"), scope="accounts:write")
crud("Network", "interline_agreements", "InterlineAgreement", create="InterlineAgreementInput", update="InterlineAgreementInput", scope="network",
     create_summary="Propose an interline agreement", filters=[q("status"), q("from_carrier"), q("to_carrier")])
for act in ["sign", "suspend", "terminate"]:
    action("Network", f"/v1/interline_agreements/{{id}}/{act}", f"interline_agreements.{act}", f"{act.capitalize()} an interline agreement", ok=R("InterlineAgreement"), scope="network:write")
crud("Network", "ledger_entries", "LedgerEntry", scope="network", filters=[q("account"), q("shipment"), q("type"), q("status")])
crud("Network", "settlements", "Settlement", scope="network", filters=[q("account"), q("status")])
action("Network", "/v1/settlements/{id}/close", "settlements.close", "Close a settlement", ok=R("Settlement"), scope="network:write")
action("Network", "/v1/settlements/{id}/dispute", "settlements.dispute", "Dispute settlement entries", body=obj({"entries": arr(STR), "reason": STR}, ["reason"]), ok=R("Settlement"), scope="network:write")
crud("Network", "service_levels", "NetworkServiceLevel", create="NetworkServiceLevel", update="NetworkServiceLevel", delete=True, scope="network", create_summary="Define a service level", filters=[q("carrier")])

# IoT
crud("IoT", "devices", "Device", create="DeviceInput", update="DeviceInput", delete=True, scope="iot", create_summary="Register a device",
     filters=[q("type"), q("status"), q("facility"), q("vehicle")])
action("IoT", "/v1/devices/{id}/certificate", "devices.certificate", "Issue a device certificate", body=obj({"csr": STR}, ["csr"]), ok=obj({"certificate": STR, "expires_at": TS}), scope="iot:write")
action("IoT", "/v1/devices/{id}/token", "devices.token", "Issue a device token", ok=obj({"token": STR, "expires_at": TS}), scope="iot:write")
action("IoT", "/v1/devices/{id}/attach", "devices.attach", "Attach a device", body=obj({"facility": STR, "vehicle": STR, "handling_unit": STR}), ok=R("Device"), scope="iot:write")
for act in ["detach", "deactivate"]:
    action("IoT", f"/v1/devices/{{id}}/{act}", f"devices.{act}", f"{act.capitalize()} a device", ok=R("Device"), scope="iot:write")
path("/v1/device_events", post=op("IoT", "device_events.create", "Ingest device events", body=obj({"events": arr(R("DeviceEvent"), maxItems=1000)}, ["events"]),
     ok=obj({"accepted": INT, "rejected": INT, "errors": arr(obj({"index": INT, "code": STR, "message": STR}))}), code="202", scopes=["iot:write"]),
     get=op("IoT", "device_events.list", "List device events", ok=obj({"object": enum("list"), "data": arr(R("DeviceEvent"))}), params=LISTP + [q("device"), q("status")], scopes=["iot:read"]))
path("/v1/shipments/{id}/conditions", parameters=[idp()], get=op("IoT", "shipments.conditions", "Condition readings and excursions",
     ok=obj({"readings": arr(obj({}, additionalProperties=True)), "excursions": arr(obj({}, additionalProperties=True))}), params=[q("handling_unit")], errors=STD + ("404",)))

# Data network
crud("Data Network", "participants", "Participant", create="ParticipantRegister", scope="data", create_summary="Register a participant (DID)", filters=[q("kind"), q("status")])
action("Data Network", "/v1/participants/{id}/credentials", "participants.credentials", "Attach a verifiable credential", body=obj({"vc": STR}, ["vc"]), ok=R("Participant"), scope="data:write")
action("Data Network", "/v1/participants/{id}/rotate_keys", "participants.rotate_keys", "Rotate participant keys", body=obj({"verification_methods": arr(obj({}, additionalProperties=True))}), ok=R("Participant"), scope="data:write")
path("/v1/records", post=op("Data Network", "records.create", "Write a record", body=R("RecordCreate"), ok=R("Record"), scopes=["data:write"]),
     get=op("Data Network", "records.list", "List records", ok=listof("Record"), params=LISTP + [q("subject.shipment"), q("subject.type"), q("producer")], scopes=["data:read"]))
path("/v1/records/query", post=op("Data Network", "records.query", "Query records", body=obj({"select": arr(STR), "where": obj({}, additionalProperties=True), "limit": INT}), ok=listof("Record")))
path("/v1/records/verify", post=op("Data Network", "records.verify", "Verify a record", body=obj({"record": STR, "object": obj({}, additionalProperties=True), "subject": obj({}, additionalProperties=True)}), ok=R("Verification"), errors=("400",)))
path("/v1/records/feed", get=op("Data Network", "records.feed", "Change feed", ok=listof("Record"), params=[q("after"), pref("Limit")]))
path("/v1/records/erase", post=op("Data Network", "records.erase", "Crypto-shred personal data", body=obj({"subject": obj({"shipment": STR}), "reason": STR}, ["subject", "reason"]), ok=obj({"erased_records": INT})))
path("/v1/anchors/{id}", parameters=[idp()], get=op("Data Network", "anchors.retrieve", "Retrieve an anchor", ok=R("Anchor"), errors=STD + ("404",)))
crud("Data Network", "access_policies", "AccessPolicy", create="AccessPolicy", update="AccessPolicy", scope="data", create_summary="Create an access policy")
crud("Data Network", "access_grants", "AccessGrant", create="AccessGrantInput", scope="data", create_summary="Grant access", filters=[q("grantee"), q("status")])
action("Data Network", "/v1/access_grants/{id}/revoke", "access_grants.revoke", "Revoke a grant", ok=R("AccessGrant"), scope="data:write")
crud("Data Network", "attestations", "Attestation", create="Attestation", scope="data", create_summary="Create an attestation", filters=[q("about"), q("attester")])
path("/v1/datasets", post=op("Data Network", "datasets.create", "Create a dataset extract", body=obj({"query": obj({}, additionalProperties=True), "format": enum("parquet", "jsonl"), "anonymization": STR}), ok=R("File")))

# Consolidation
crud("Consolidation", "consolidations", "Consolidation", create="ConsolidationInput", update="ConsolidationInput", scope="consolidation",
     create_summary="Create a consolidation", filters=[q("type"), q("status"), q("origin"), q("destination"), q("conveyance"), q("identifiers.sscc")])
for act, body in [("add", CONTENTS_IO), ("remove", CONTENTS_IO), ("close", obj({})), ("seal", obj({"number": STR, "type": STR}, ["number"])),
                  ("break_seal", obj({"reason": STR}, ["reason"])), ("load", obj({"conveyance": STR, "position": STR}, ["conveyance"])), ("unload", obj({})), ("deconsolidate", obj({}))]:
    action("Consolidation", f"/v1/consolidations/{{id}}/{act}", f"consolidations.{act}", f"Consolidation: {act}", body=body, ok=R("Consolidation"), scope="consolidation:write")
action("Consolidation", "/v1/consolidations/{id}/label", "consolidations.label", "Generate a consolidation label", body=obj({"format": STR}), ok=R("Document"), scope="consolidation:write")
path("/v1/consolidations/{id}/contents", parameters=[idp()], get=op("Consolidation", "consolidations.contents", "List contents",
     ok=obj({"consolidations": arr(STR), "handling_units": arr(STR)}), params=[q("recursive", BOOL)], errors=STD + ("404",)))
crud("Consolidation", "conveyances", "Conveyance", create="ConveyanceInput", update="ConveyanceInput", scope="consolidation", create_summary="Create a conveyance",
     filters=[q("mode"), q("status"), q("identifiers.flight_number"), q("operator")])
for act in ["close", "depart", "arrive", "cancel"]:
    action("Consolidation", f"/v1/conveyances/{{id}}/{act}", f"conveyances.{act}", f"Conveyance: {act}", body=obj({"at": STR}), ok=R("Conveyance"), scope="consolidation:write")
path("/v1/conveyances/{id}/manifest", parameters=[idp()], get=op("Consolidation", "conveyances.manifest", "Conveyance manifest", ok=obj({}, additionalProperties=True), params=[q("format", enum("json", "pdf"))], errors=STD + ("404",)))
path("/v1/shipments/{id}/custody", parameters=[idp()], get=op("Consolidation", "shipments.custody", "Custody chain", ok=R("Custody"), errors=STD + ("404",)))

# Templates
crud("Templates", "document_templates", "DocumentTemplate", create="DocumentTemplateInput", update="DocumentTemplateInput", delete=True, scope="templates",
     create_summary="Create a document template", delete_summary="Delete a draft template", filters=[q("type"), q("related_object"), q("status")])
action("Templates", "/v1/document_templates/{id}/publish", "document_templates.publish", "Publish a template", body=obj({"effective_from": DATE}), ok=R("DocumentTemplate"), scope="templates:write")
action("Templates", "/v1/document_templates/{id}/preview", "document_templates.preview", "Preview a template", body=obj({"object": STR, "data": obj({}, additionalProperties=True), "format": STR, "version": STR}), ok=R("Document"), scope="templates:read")
action("Templates", "/v1/document_templates/{id}/validate", "document_templates.validate", "Validate a template",
       ok=obj({"valid": BOOL, "errors": arr(obj({"line": INT, "message": STR})), "unknown_fields": arr(STR)}), scope="templates:read")
path("/v1/document_templates/{id}/versions", parameters=[idp()], get=op("Templates", "document_templates.versions", "List template versions", ok=listof("DocumentTemplate"), params=LISTP, errors=STD + ("404",)))
path("/v1/documents/generate", post=op("Templates", "documents.generate", "Generate a document", body=R("DocumentGenerate"), ok=R("Document"), errors=STD + ("404", "422"), scopes=["templates:write"]))
crud("Templates", "documents", "Document", delete=True, scope="templates", delete_summary="Delete a standalone document", filters=[q("related.id"), q("type"), q("template")])
crud("Templates", "document_jobs", "DocumentJob", create="DocumentJobCreate", scope="templates", create_summary="Create a document job")


# Integrations
path("/v1/integrations", get=op("Integrations", "integrations.list", "List integrations", ok=listof("Integration"), params=LISTP + [q("interface"), q("kind"), q("country")]),
     post=op("Integrations", "integrations.create", "Onboard a federated provider", body=obj({"federated": obj({"configuration": STR}, ["configuration"])}, ["federated"]), ok=R("Integration"), errors=STD + ("422",)))
path("/v1/integrations/{id}", parameters=[idp()], get=op("Integrations", "integrations.retrieve", "Retrieve an integration", ok=R("Integration"), errors=STD + ("404",)))
path("/v1/address_validations", post=op("Integrations", "address_validations.create", "Validate an address", body=R("AddressValidationRequest"), ok=R("AddressValidation"), errors=STD + ("422", "502")))
path("/v1/address_validations/{id}", parameters=[idp()], get=op("Integrations", "address_validations.retrieve", "Retrieve an address validation", ok=R("AddressValidation"), errors=STD + ("404",)))
path("/v1/insurance_quotes", post=op("Integrations", "insurance_quotes.create", "Quote insurance", body=R("InsuranceQuoteRequest"),
     ok=obj({"object": enum("list"), "data": arr(R("InsuranceQuote")), "errors": arr(R("ConnectionError"))})))
crud("Integrations", "coverages", "Coverage", create="CoverageCreate", create_idem=True, create_money=True, scope="integrations", create_summary="Buy coverage",
     filters=[q("shipment"), q("status")])
action("Integrations", "/v1/coverages/{id}/cancel", "coverages.cancel", "Cancel coverage", ok=R("Coverage"), scope="integrations:write")
crud("Integrations", "claims", "Claim", create="ClaimInput", update="ClaimInput", scope="integrations", create_summary="Submit a claim", filters=[q("coverage"), q("status")])
action("Integrations", "/v1/claims/{id}/withdraw", "claims.withdraw", "Withdraw a claim", ok=R("Claim"), scope="integrations:write")

# Jobs
crud("Jobs", "jobs", "Job", create="JobCreate", scope="jobs", create_summary="Start a job",
     filters=[q("type", desc="Prefix match, e.g. documents.*"), q("status"), q("source"), q("schedule"), q("subject.type")])
action("Jobs", "/v1/jobs/{id}/cancel", "jobs.cancel", "Cancel a job", ok=R("Job"), scope="jobs:write")
action("Jobs", "/v1/jobs/{id}/retry", "jobs.retry", "Retry a job", body=obj({"only_failed": BOOL}), ok=R("Job"), scope="jobs:write")
path("/v1/jobs/{id}/logs", parameters=[idp()], get=op("Jobs", "jobs.logs", "Job logs", ok=obj({"object": enum("list"), "data": arr(R("JobLog")), "has_more": BOOL}), params=[q("after")], errors=STD + ("404",)))
path("/v1/jobs/{id}/stream", parameters=[idp()], get={"tags": ["Jobs"], "operationId": "jobs.stream", "summary": "Stream job progress (SSE)", "parameters": COMMON,
     "responses": {"200": {"description": "Server-Sent Events", "content": {"text/event-stream": {"schema": STR}}}, **errs("401", "404")}})
crud("Jobs", "job_schedules", "JobSchedule", create="JobScheduleInput", update="JobScheduleInput", delete=True, scope="jobs", create_summary="Create a job schedule",
     filters=[q("type"), q("status")])
for act in ["pause", "resume", "run_now"]:
    action("Jobs", f"/v1/job_schedules/{{id}}/{act}", f"job_schedules.{act}", f"Job schedule: {act}", ok=R("JobSchedule"), scope="jobs:write")


# Billing
crud("Billing", "invoices", "Invoice", create="InvoiceInput", update="InvoiceInput", scope="billing", create_summary="Create a draft invoice",
     filters=[q("kind"), q("direction"), q("status"), q("issuer.integration"), q("period.from", DATE)])
for act, body in [("finalize", obj({})), ("send", obj({})), ("void", obj({})), ("mark_uncollectible", obj({})),
                  ("dispute", obj({"lines": arr(STR), "reason": STR, "evidence": arr(STR)}, ["reason"]))]:
    action("Billing", f"/v1/invoices/{{id}}/{act}", f"invoices.{act}", f"Invoice: {act}", body=body, ok=R("Invoice"), scope="billing:write")
action("Billing", "/v1/invoices/{id}/pay", "invoices.pay", "Pay an invoice", body=obj({"payment_method": STR, "amount": R("Money")}), ok=R("Payment"), idem=True, money=True, scope="billing:write")
path("/v1/invoices/import", post=op("Billing", "invoices.import", "Import invoices from a file", body=obj({"file": STR, "format": INV_FORMATS, "connection": STR}, ["file", "format"]), ok=R("Job"), code="202"))
path("/v1/invoices/{id}/export", parameters=[idp()], get={"tags": ["Billing"], "operationId": "invoices.export", "summary": "Export an invoice", "parameters": COMMON + [q("format", INV_FORMATS)],
     "responses": {"200": {"description": "Invoice in the requested format", "content": {"application/json": {"schema": R("Invoice")}, "application/xml": {"schema": STR}, "text/csv": {"schema": STR}, "application/edi-x12": {"schema": STR}}}, **errs("401", "404")}})
path("/v1/invoices/upcoming", get=op("Billing", "invoices.upcoming", "Preview the upcoming usage invoice", ok=R("Invoice")))
crud("Billing", "reconciliations", "Reconciliation", create="Reconciliation", scope="billing", create_summary="Reconcile an invoice", filters=[q("invoice"), q("status"), q("type")])
path("/v1/reconciliations/{id}/lines/{line_id}/resolve", parameters=[idp(), idp("line_id")],
     post=op("Billing", "reconciliations.resolve", "Resolve a reconciliation line", body=obj({"action": enum("accept", "dispute", "rebill", "write_off"), "note": STR}, ["action"]), ok=R("ReconciliationLine"), errors=STD + ("404", "409")))
crud("Billing", "meters", "Meter", create="Meter", update="Meter", scope="billing", create_summary="Create a meter", filters=[q("status")])
crud("Billing", "usage_records", "UsageRecord", create="UsageRecordInput", create_idem=True, scope="billing", create_summary="Report usage",
     filters=[q("meter"), q("account"), q("occurred_at[gte]", STR)])
path("/v1/usage_records/import", post=op("Billing", "usage_records.import", "Import usage records", body=obj({"file": STR, "format": enum("csv", "jsonl")}, ["file"]), ok=R("Job"), code="202"))
path("/v1/usage_summaries", get=op("Billing", "usage_summaries.list", "Usage summary per meter", ok=obj({"account": STR, "period": STR, "meters": arr(obj({"meter": STR, "quantity": NUM, "amount": R("Money"), "included_used": NUM}))}),
     params=[q("account"), q("period")]))
crud("Billing", "price_plans", "PricePlan", create="PricePlan", update="PricePlan", scope="billing", create_summary="Create a price plan", filters=[q("status")])
path("/v1/billing_profile", get=op("Billing", "billing_profile.retrieve", "Retrieve the billing profile", ok=R("BillingProfile")),
     post=op("Billing", "billing_profile.update", "Update the billing profile", body=R("BillingProfile"), ok=R("BillingProfile")))
path("/v1/balance", get=op("Billing", "balance.retrieve", "Retrieve the prepaid balance", ok=R("Balance")))
path("/v1/balance/top_up", post=op("Billing", "balance.top_up", "Top up the balance", body=obj({"amount": R("Money"), "payment_method": STR}, ["amount"]), ok=R("Payment"),
     params=[pref("IdempotencyKeyRequired")], money=True))
path("/v1/balance_transactions", get=op("Billing", "balance_transactions.list", "List balance transactions", ok=listof("BalanceTransaction"), params=LISTP + [q("type")]))
path("/v1/payment_methods/setup", post=op("Billing", "payment_methods.setup", "Start hosted payment method setup", body=obj({"connection": STR}), ok=R("PaymentMethodSetup")))
crud("Billing", "payment_methods", "PaymentMethod", delete=True, scope="billing", filters=[q("type")])
crud("Billing", "payments", "Payment", scope="billing", filters=[q("status"), q("invoice"), q("purpose")])
action("Billing", "/v1/payments/{id}/refund", "payments.refund", "Refund a payment", body=obj({"amount": R("Money")}), ok=R("Refund"), idem=True, scope="billing:write")
path("/v1/payments/reconcile_statement", post=op("Billing", "payments.reconcile_statement", "Reconcile an ISO 20022 camt.053 statement", body=obj({"file": STR}, ["file"]), ok=R("Job"), code="202"))
crud("Billing", "payouts", "Payout", scope="billing", filters=[q("account"), q("status"), q("settlement")])


# Inventory
crud("Inventory", "storage_locations", "StorageLocation", create="StorageLocation", update="StorageLocation", delete=True, scope="inventory",
     create_summary="Create a storage location", filters=[q("facility"), q("type"), q("status")])
path("/v1/storage_locations/import", post=op("Inventory", "storage_locations.import", "Import a facility layout", body=obj({"file": STR, "facility": STR}, ["file", "facility"]), ok=R("Job"), code="202"))
path("/v1/inventory/levels", get=op("Inventory", "inventory.levels", "Stock levels", ok=obj({"object": enum("list"), "data": arr(R("InventoryLevel"))}),
     params=[q("product"), q("facility"), q("owner"), q("group_by"), q("updated[gte]", INT)]))
path("/v1/inventory/thresholds", post=op("Inventory", "inventory.thresholds", "Set low-stock thresholds", body=obj({"product": STR, "facility": STR, "available_below": INT}, ["product", "available_below"]), ok=obj({}, additionalProperties=True)))
crud("Inventory", "stock", "Stock", scope="inventory", filters=[q("product"), q("facility"), q("location"), q("status"), q("owner")])
crud("Inventory", "stock_movements", "StockMovement", create="StockMovementInput", create_idem=True, scope="inventory", create_summary="Record a stock movement",
     filters=[q("product"), q("facility"), q("type"), q("occurred_at[gte]", STR)])
crud("Inventory", "fulfillment_orders", "FulfillmentOrder", create="FulfillmentOrderInput", update="FulfillmentOrderInput", create_idem=True, search=True, scope="inventory",
     create_summary="Create a fulfillment order", filters=[q("status"), q("facility"), q("owner"), q("channel.upstream_reference")])
for act, body in [("allocate", obj({})), ("release_to_pick", obj({})), ("cancel", obj({"reason": STR})),
                  ("pack", obj({"handling_units": arr(R("HandlingUnit"))}, ["handling_units"]))]:
    action("Inventory", f"/v1/fulfillment_orders/{{id}}/{act}", f"fulfillment_orders.{act}", f"Fulfillment order: {act}", body=body, ok=R("FulfillmentOrder"), scope="inventory:write")
action("Inventory", "/v1/fulfillment_orders/{id}/ship", "fulfillment_orders.ship", "Ship a fulfillment order", body=obj({"purchase": R("PurchaseInstruction")}),
       ok=obj({"object": enum("list"), "data": arr(R("Shipment"))}), idem=True, money=True, scope="inventory:write")
crud("Inventory", "waves", "Wave", create="Wave", scope="inventory", create_summary="Release a wave", filters=[q("facility"), q("status")])
crud("Inventory", "inventory_counts", "InventoryCount", create="InventoryCount", scope="inventory", create_summary="Start a count", filters=[q("facility"), q("status")])
action("Inventory", "/v1/inventory_counts/{id}/lines", "inventory_counts.lines", "Add count lines",
       body=obj({"counts": arr(obj({"location": STR, "product": STR, "lot": STR, "counted": INT}))}, ["counts"]), ok=R("InventoryCount"), scope="inventory:write")
action("Inventory", "/v1/inventory_counts/{id}/complete", "inventory_counts.complete", "Complete a count", body=obj({"approve": BOOL}), ok=R("InventoryCount"), scope="inventory:write")

# Label specs & ingestion
crud("Templates", "label_specs", "LabelSpec", create="LabelSpec", update="LabelSpec", scope="templates", create_summary="Create a label spec", filters=[q("carrier"), q("status")])
action("Templates", "/v1/label_specs/{id}/publish", "label_specs.publish", "Publish a label spec", ok=R("LabelSpec"), scope="templates:write")
action("Templates", "/v1/label_specs/{id}/certify", "label_specs.certify", "Certify labels against the spec", body=obj({"samples": arr(STR)}, ["samples"]),
       ok=obj({"result": enum("pass", "fail"), "findings": arr(obj({"code": STR, "message": STR, "sample": STR}))}), scope="templates:write")
action("Templates", "/v1/label_specs/{id}/tracking_ranges", "label_specs.tracking_ranges", "Allocate tracking numbers", body=obj({"count": INT}, ["count"]),
       ok=obj({"from": STR, "to": STR, "count": INT}), idem=True, scope="templates:write")
path("/v1/documents/ingest", post=op("Templates", "documents.ingest", "Ingest a document", body=R("DocumentIngestRequest"), ok=R("DocumentIngestion"), code="202", scopes=["templates:write"]))
crud("Templates", "document_ingestions", "DocumentIngestion", scope="templates", filters=[q("status"), q("type"), q("attach_to.id")])
action("Templates", "/v1/document_ingestions/{id}/apply", "document_ingestions.apply", "Apply extracted data", body=obj({"corrections": obj({}, additionalProperties=True)}), ok=R("DocumentIngestion"), scope="templates:write")
action("Templates", "/v1/document_ingestions/{id}/reject", "document_ingestions.reject", "Reject an ingestion", ok=R("DocumentIngestion"), scope="templates:write")


# Timelines (data network)
path("/v1/timelines/{shipment_id}", parameters=[idp("shipment_id")], get=op("Data Network", "timelines.retrieve", "End-to-end timeline", ok=R("Timeline"), errors=STD + ("404",), scopes=["data:read"]))
path("/v1/timelines/{shipment_id}/events", parameters=[idp("shipment_id")], get=op("Data Network", "timelines.events", "Merged events with provenance",
     ok=obj({"object": enum("list"), "data": arr(obj({"event": R("TrackingEvent"), "producer": STR, "record": STR, "via": nullable(IDENT_REF)})), "has_more": BOOL}), params=LISTP, errors=STD + ("404",)))
path("/v1/timelines/resolve", post=op("Data Network", "timelines.resolve", "Resolve an identifier to shipments", body=obj({"identifier": IDENT_REF}, ["identifier"]),
     ok=obj({"object": enum("list"), "data": arr(obj({"shipment": STR, "path": arr(IDENT_REF)}))})))
path("/v1/identifier_links", post=op("Data Network", "identifier_links.create", "Link identifiers", body=R("IdentifierLinkInput"), ok=R("IdentifierLink"), scopes=["data:write"]))
path("/v1/milestone_definitions", get=op("Data Network", "milestone_definitions.retrieve", "Milestone definition set", ok=R("MilestoneDefinitions")))

# Discovery
path("/.well-known/shipping-configuration", get={"tags": ["Discovery"], "operationId": "discovery.configuration", "summary": "Shipping configuration document",
     "security": [], "servers": [{"url": "https://api.example.com"}], "responses": {"200": {"description": "OK", "content": {"application/json": {"schema": obj({}, additionalProperties=True)}}}}})

# ---------- components ----------
def errresp(desc): return {"description": desc, "content": {"application/json": {"schema": R("Error")}}}
# ---------- surfaces: GraphQL operations leave the REST document ----------
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import graphql_surface as GS
import copy as _copy
ALL_SCHEMAS = _copy.deepcopy(schemas)
GQL_OPS = GS.partition(paths)

doc = {
  "openapi": "3.1.0",
  "info": {
    "title": "Open Logistics Specs", "version": "0.1.0-draft",
    "summary": "An open, carrier-agnostic shipping API specification.",
    "description": "Draft 0.1 (2026-10-06). See README.md and spec/*.md for normative text; this document is the machine-readable reference. "
                   "Operations marked `x-spends-money: true` purchase labels or services and MUST be confirmed by a human when invoked by an agent.",
    "license": {"name": "Apache-2.0", "identifier": "Apache-2.0"},
    "contact": {"name": "Shipping Internals", "url": "https://shippinginternals.dev"},
  },
  "servers": [{"url": "https://api.example.com", "description": "Replace with implementer host"}],
  "security": [{"apiKey": []}, {"oauth2": []}],
  "tags": [{"name": t} for t in ["Rates", "Shipments", "Pickups", "Manifests", "Files", "Document Uploads", "Tracking", "Webhooks", "Events", "Inbound", "Carriers", "Connections", "Apps", "Batches", "Test Helpers", "Pickup Schedules", "Trade", "Catalog", "Pricing", "Routes", "Fleet", "Injection", "Accounts", "Products", "Network", "IoT", "Data Network", "Consolidation", "Templates", "Integrations", "Jobs", "Billing", "Inventory", "Discovery"]],
  "paths": paths,
  "webhooks": {
    "event": {"post": {"summary": "Event delivery to a webhook endpoint",
      "parameters": [{"name": "Shipping-Signature", "in": "header", "required": True, "schema": STR, "description": "t=<unix>,v1=<hex hmac-sha256 of '{t}.{raw_body}'>[,v1a=<ed25519>]"},
                     {"name": "Shipping-Event-Id", "in": "header", "required": True, "schema": STR},
                     {"name": "Shipping-Event-Type", "in": "header", "required": True, "schema": STR},
                     {"name": "Shipping-Delivery-Id", "in": "header", "required": True, "schema": STR}],
      "requestBody": {"content": {"application/json": {"schema": R("Event")}}},
      "responses": {"2XX": {"description": "Acknowledged"}}}}},
  "components": {
    "securitySchemes": {
      "apiKey": {"type": "http", "scheme": "bearer", "description": "sk_test_ / sk_live_ / rk_test_ / rk_live_ keys"},
      "oauth2": {"type": "oauth2", "flows": {
        "authorizationCode": {"authorizationUrl": "https://api.example.com/oauth/authorize", "tokenUrl": "https://api.example.com/oauth/token", "refreshUrl": "https://api.example.com/oauth/token", "scopes": {
          s: s for s in ["rates:read", "shipments:read", "shipments:write", "pickups:read", "pickups:write", "manifests:read", "manifests:write", "documents:read", "documents:write",
                         "trackers:read", "trackers:write", "webhooks:read", "webhooks:write", "connections:read", "connections:write", "inbound:read", "inbound:write", "trade:read", "trade:write", "catalog:read", "catalog:write", "pricing:read", "pricing:write", "routes:read", "routes:write", "fleet:read", "fleet:write", "injection:read", "injection:write", "accounts:read", "accounts:write", "products:read", "products:write", "network:read", "network:write", "iot:read", "iot:write", "data:read", "data:write", "consolidation:read", "consolidation:write", "templates:read", "templates:write", "integrations:read", "integrations:write", "jobs:read", "jobs:write", "billing:read", "billing:write", "inventory:read", "inventory:write", "openid", "profile", "email"]}},
        "clientCredentials": {"tokenUrl": "https://api.example.com/oauth/token", "scopes": {}},
        "deviceAuthorization": None}},
      "oidc": {"type": "openIdConnect", "openIdConnectUrl": "https://api.example.com/.well-known/openid-configuration"},
    },
    "parameters": P,
    "responses": {
      "BadRequest": errresp("invalid_request_error"), "Unauthorized": errresp("authentication_error"), "Forbidden": errresp("permission_error"),
      "NotFound": errresp("resource_missing"), "Conflict": errresp("idempotency_error or state_error"), "CarrierError": errresp("carrier_error"),
      "RateLimited": errresp("rate_limit_error"), "CarrierUnavailable": errresp("carrier_unavailable"),
    },
    "schemas": schemas,
  },
}
# OpenAPI 3.1 has no device flow object; drop the placeholder
del doc["components"]["securitySchemes"]["oauth2"]["flows"]["deviceAuthorization"]

class D(yaml.SafeDumper):
    def ignore_aliases(self, data): return True
used_tags = {op["tags"][0] for it in paths.values() for k, op in it.items() if k in ("get", "post", "delete")}
doc["tags"] = [t for t in doc["tags"] if t["name"] in used_tags]
GS.prune_schemas(doc)
yaml.dump(doc, open(sys.argv[1], "w"), Dumper=D, sort_keys=False, width=140, allow_unicode=True)
import openapi_modes
print("per-mode REST operations:", openapi_modes.emit(doc, GS.ROOT / "openapi", D))
openapi_modes.write_nav(GS.ROOT)
print("REST paths:", len(paths), "operations:", sum(1 for p in paths.values() for k in p if k in ("get", "post", "delete")), "schemas:", len(doc["components"]["schemas"]))
nq, nm, _ = GS.emit(GQL_OPS, ALL_SCHEMAS, GS.ROOT / "graphql" / "schema.graphql", GS.ROOT / "spec" / "graphql.md")
print("GraphQL queries:", nq, "mutations:", nm)
