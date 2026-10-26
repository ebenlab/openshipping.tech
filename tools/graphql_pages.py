"""Generate one reference page per GraphQL field (graphql-reference/<module>/<field>.mdx), Shopify-dev style:
description, scopes, arguments, input fields, return fields, and request/variables/response examples
built from the schema. Also writes the GraphQL tab navigation into docs.json.
"""
import json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "graphql-reference"
SCALARS = {"String", "Int", "Float", "Boolean", "ID"}


def base(t):
    return re.sub(r"[\[\]!]", "", t)


def is_list(t):
    return t.strip("!").startswith("[")


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def kebab(n):
    return re.sub(r"(?<!^)(?=[A-Z])", "-", n).lower()


def pascal(s):
    return s[:1].upper() + s[1:]


STR_SAMPLES = {
    "currency": "usd", "country": "GB", "origin_country": "PT", "postal_code": "SW1A 2AA", "city": "London", "state": None,
    "line1": "Downing St", "street_number": "10", "line2": None, "email": "ops@example.com", "phone": "+447700900123",
    "timezone": "Europe/London", "reference": "ORDER-1001", "sku": "TS-RED-M", "carrier": "dhl_express", "connection": "conn_9f8e",
    "shipment": "shp_1Q2w3E4r5T6y", "facility": "fac_lon_hub", "route": "rte_lax_lhr_daily", "vehicle": "veh_van07", "driver": "drv_ama",
    "account": "acct_ada", "owner": "acct_ada", "product": "prod_ts_red_m", "service": "dhl_express_worldwide", "template": "dtpl_packslip_v2",
    "file": "file_6Yu8", "invoice": "invc_7Ff2", "partner": "acct_dpd_intl", "consolidation": "csl_gay_7781", "conveyance": "cnv_sw123_20261008",
    "location": "loc_lon_a12_03_b", "zone": "zone_gb_mainland", "issuer": "https://ada.okta.com/oauth2/default", "client_id": "0oa1b2c3",
    "key": "signature", "code": "dhl_express_worldwide", "name": "Example", "label": "Example", "title": "Example", "description": "Example description",
    "did": "did:web:swiftair.example", "hs_code": "6109100010", "barcode": "LOC-A12-03-B", "plate": "LX26 ABC", "flight_number": "SW123",
    "source": "api", "format": "pdf", "size": "4x6", "slug": "example", "group": "dock-a", "close_group": "dock-a", "local_time": "15:00",
    "ready_at": "15:00", "close_at": "18:00", "number": "SEAL-00918", "value": "example", "url": "https://example.com/resource",
    "seal_number": "SEAL-00918", "registration": "AB12 CDE", "tracking_number": "1Z999AA10123456784", "unit": "kg",
}


def sample_scalar(field, t, sdl, owner=""):
    b = base(t)
    f = field.lower()
    if b in sdl.enums:
        return sdl.enums[b][0].lstrip("_")
    if b == "ID":
        return STR_SAMPLES.get(f, "obj_1a2B3c")
    if b == "Boolean":
        return True
    if b == "Int":
        if "amount" in f or f in ("total", "subtotal"):
            return 1299
        if f.endswith("_at") or f in ("created", "updated", "expires_at"):
            return 1791302400
        if f in ("version",):
            return 3
        if f == "priority":
            return 100
        if f == "limit":
            return 10
        return 2
    if b == "Float":
        return {"latitude": 51.5074, "longitude": -0.1278, "confidence": 0.94, "rate": 0.145}.get(f, 1.5)
    if b == "String":
        if f in STR_SAMPLES and STR_SAMPLES[f] is not None:
            return STR_SAMPLES[f]
        if f.endswith("_zone") or f == "zone":
            return "zone_gb_mainland"
        if f.endswith("_facility") or f in ("handoff_point", "depot", "home_facility"):
            return "fac_lon_hub"
        if f.endswith("_code") and f != "carrier_code":
            return "GB"
        if f == "carrier_code":
            return "EXPRESS_WORLDWIDE"
        if f.endswith("_url") or f == "url":
            return "https://example.com/" + f.replace("_url", "")
        if f.endswith("_at"):
            return "2026-10-07T09:00:00Z"
        if f in ("date", "ship_date") or f.endswith("_on") or f.startswith("effective_") or f in ("from", "to", "until", "starts_on", "ends_on", "due_by"):
            return "2026-10-07"
        if f.endswith("country"):
            return "GB"
        return "example"
    if b == "JSON":
        if f == "user_metadata":
            return {"order_id": "1001"}
        if f == "system_metadata":
            return {"source": "api"}
        return {}
    return None


class Builder:
    def __init__(self, sdl, prefixes):
        self.sdl, self.prefixes = sdl, prefixes

    def fields(self, tname):
        return self.sdl.out_types.get(tname) or []

    def selection(self, tname, depth=0):
        fs = self.fields(tname)
        if not fs:
            return None
        if tname.endswith("List") and fs and fs[0][0] == "data":
            item = base(fs[0][1])
            return [("data", self.selection(item, depth) or [], fs[0][1]), ("has_more", None, "Boolean")]
        cap = {0: 16, 1: 6, 2: 4}.get(depth, 3)
        order = sorted(fs, key=lambda x: (x[0] not in ("id", "object", "status", "type", "code", "name"),))
        sel = []
        for f, t, _ in order:
            b = base(t)
            if b in SCALARS or b in self.sdl.enums:
                sel.append((f, None, t))
            elif b == "JSON":
                if depth == 0 and f in ("user_metadata",):
                    sel.append((f, None, t))
            elif b in self.sdl.out_types and depth < 2:
                sub = self.selection(b, depth + 1)
                if sub:
                    sel.append((f, sub, t))
            if len(sel) >= cap:
                break
        return sel

    def render_sel(self, sel, ind):
        lines = []
        for f, sub, _ in sel:
            if sub is None:
                lines.append(" " * ind + f)
            else:
                lines.append(" " * ind + f + " {")
                lines += self.render_sel(sub, ind + 2)
                lines.append(" " * ind + "}")
        return lines

    def sample_obj(self, tname, sel, depth=0):
        out = {}
        for f, sub, t in sel:
            if sub is None:
                v = sample_scalar(f, t, self.sdl, tname)
                if f == "id":
                    v = self.prefixes.get(tname, "obj_") + "1a2B3c"
                if f == "object":
                    v = re.sub(r"(?<!^)(?=[A-Z])", "_", tname.replace("Catalog", "")).lower().replace("_spec", "")
                out[f] = [v] if is_list(t) and not isinstance(v, (dict, list)) else v
            else:
                b = base(t)
                obj = self.sample_obj(b, sub, depth + 1) if not (b.endswith("List") and sub and sub[0][0] == "data") else None
                if obj is None:
                    item = base(self.fields(b)[0][1])
                    obj = {"data": [self.sample_obj(item, sub[0][1], depth + 1)], "has_more": False}
                out[f] = [obj] if is_list(t) else obj
        return out

    def sample_input(self, tname, depth=0):
        fs = self.sdl.in_types.get(tname) or []
        out, objs = {}, 0
        for f, t, _ in fs:
            b = base(t)
            if b in SCALARS or b in self.sdl.enums or b == "JSON":
                if b == "JSON" and f != "user_metadata" and depth > 0:
                    continue
                v = sample_scalar(f, t, self.sdl, tname)
                out[f] = [v] if is_list(t) and not isinstance(v, (dict, list)) else v
            elif b in self.sdl.in_types and depth < 2 and objs < 3:
                v = self.sample_input(b, depth + 1)
                if v:
                    out[f] = [v] if is_list(t) else v
                    objs += 1
            if len(out) >= (8 if depth == 0 else 4):
                break
        return out


def write_pages(recs, sdl, schemas):
    prefixes = {}
    for n, sch in schemas.items():
        idd = (sch.get("properties") or {}).get("id") or {}
        m = re.search(r"Prefixed `([a-z_]+_)`", idd.get("description", "") if isinstance(idd, dict) else "")
        if m:
            prefixes[n] = m.group(1)
            prefixes[re.sub(r"(Input|Create|Update|Request)$", "Spec", n)] = m.group(1)
    B = Builder(sdl, prefixes)
    if OUT.exists():
        shutil.rmtree(OUT)
    nav = {}
    for r in recs:
        tag, field = r["tag"], r["field"]
        rtype = r["returns"]
        rbase = base(rtype)
        sel = B.selection(rbase) or []
        # operation text
        var_defs, call_args, variables = [], [], {}
        for name, t, _ in r["args"]:
            if name == "input" and r["input"]:
                var_defs.append(f"$input: {t}!"); call_args.append("input: $input")
                variables["input"] = B.sample_input(r["input"])
            elif t == "ID!":
                var_defs.append(f"${name}: ID!"); call_args.append(f"{name}: ${name}")
                variables[name] = prefixes.get(rbase, "obj_") + "1a2B3c" if name == "id" else STR_SAMPLES.get(name, "example_id")
            elif name == "limit":
                var_defs.append("$limit: Int"); call_args.append("limit: $limit"); variables["limit"] = 10
        op_name = pascal(field)
        head = f"{r['kind']} {op_name}" + (f"({', '.join(var_defs)})" if var_defs else "")
        call = f"  {field}" + (f"({', '.join(call_args)})" if call_args else "")
        body_lines = [head + " {", call + (" {" if sel else "")]
        if sel:
            body_lines += B.render_sel(sel, 4) + ["  }"]
        body_lines.append("}")
        if sel:
            data = B.sample_obj(rbase, sel)
        elif rbase == "DeletedObject":
            data = {"id": variables.get("id", "obj_1a2B3c"), "object": "deleted", "deleted": True}
        else:
            data = {}
        response = {"data": {field: data}}
        # tables
        badges = [f"`{r['kind']}`", f"Module: **{tag}**"]
        if r["scopes"]:
            badges.append("Requires " + ", ".join(f"`{s}`" for s in r["scopes"]))
        if r["idem"]:
            badges.append("`Idempotency-Key` header required")
        if r["money"]:
            badges.append("**Spends money**: confirm before calling")
        lines = ["---", f'title: "{field}"', f'description: "{r["summary"].replace(chr(34), chr(39))}"', "---", "",
                 " · ".join(badges), ""]
        if r["description"]:
            lines += [r["description"], ""]
        lines += ["## Arguments", ""]
        if r["args"]:
            lines += ["| Argument | Type | Description |", "|---|---|---|"]
            lines += [f"| `{n}` | `{t}` | {d} |" for n, t, d in r["args"]]
        else:
            lines.append("None.")
        lines.append("")
        if r["input"] and sdl.in_types.get(r["input"]):
            lines += [f"### `{r['input']}` fields", "", "| Field | Type |", "|---|---|"]
            lines += [f"| `{f}` | `{t}` |" for f, t, _ in sdl.in_types[r["input"]]]
            lines.append("")
        lines += ["## Returns", "", f"`{rtype}`", ""]
        rf = B.fields(rbase)
        if rf:
            lines += ["| Field | Type |", "|---|---|"] + [f"| `{f}` | `{t}{'' if nul else '!'}` |" for f, t, nul in rf] + [""]
        lines += ["## Errors", "",
                  "Errors are returned in `errors[]`, with the REST error object in `extensions` (`type`, `code`, `param`, `request_id`), using the codes in [Conventions §9](/spec/00-conventions).", ""]
        lines += ["<RequestExample>", "", "```graphql Request", *body_lines, "```", "",
                  "```json Variables", json.dumps(variables, indent=2), "```", "", "</RequestExample>", "",
                  "<ResponseExample>", "", "```json Response", json.dumps(response, indent=2), "```", "", "</ResponseExample>", ""]
        path = OUT / slug(tag) / f"{kebab(field)}.mdx"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines))
        nav.setdefault(tag, []).append(f"graphql-reference/{slug(tag)}/{kebab(field)}")
    # docs.json GraphQL tab
    dj = ROOT / "docs.json"
    d = json.loads(dj.read_text())
    tabs = d["navigation"]["tabs"]
    groups = [{"group": "Overview", "pages": ["spec/graphql"]}] + [{"group": t, "pages": sorted(set(p))} for t, p in sorted(nav.items())]
    for t in tabs:
        if t["tab"] == "GraphQL Interface":
            t["groups"] = groups
    dj.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    print("GraphQL reference pages:", sum(len(v) for v in nav.values()))
