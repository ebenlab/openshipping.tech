"""Split operations between the REST surface (integrator-facing) and the GraphQL surface
(internal, back-office and LSP account self-management), and emit the GraphQL SDL and reference page.

Used by build_openapi.py. The classification rule lives in GRAPHQL_RESOURCES / GRAPHQL_OPS below.
"""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Whole resources managed through GraphQL (operationId prefix before the first dot).
GRAPHQL_RESOURCES = {
    "services", "options", "packagings", "zones", "rate_sheets", "surcharges", "pricing_rules",
    "facilities", "routes", "route_runs", "vehicles", "drivers", "optimizations",
    "apps", "identity_providers", "memberships", "invitations", "roles", "api_keys",
    "interline_agreements", "ledger_entries", "settlements", "service_levels",
    "devices", "access_policies", "consolidations", "conveyances", "document_templates",
    "job_schedules", "storage_locations", "waves", "inventory_counts", "stock_movements", "stock",
    "meters", "price_plans", "reconciliations", "payouts", "billing_profile",
}
# Individual operations managed through GraphQL.
GRAPHQL_OPS = {
    "accounts.member_list", "accounts.member_pause", "accounts.member_delist",
    "accounts.suspend", "accounts.reactivate", "accounts.close",
    "integrations.create", "payments.reconcile_statement", "payments.refund",
    "invoices.create", "invoices.update", "invoices.finalize", "invoices.send", "invoices.void",
    "invoices.mark_uncollectible", "invoices.import",
    "label_specs.create", "label_specs.update", "label_specs.publish",
    "fulfillment_orders.allocate", "fulfillment_orders.release_to_pick", "fulfillment_orders.pack", "fulfillment_orders.ship",
    "inventory.thresholds", "vehicles.position", "shipments.journey.replan", "storage_locations.import",
}


def is_graphql(op_id):
    return op_id.split(".")[0] in GRAPHQL_RESOURCES or op_id in GRAPHQL_OPS


CRUD_VERBS = {"list", "retrieve", "create", "update", "delete", "search"}
NO_DATA_TAGS = {"Discovery", "Test Helpers"}


def partition(paths):
    """Move back-office operations from `paths` to the GraphQL Interface (in place), and mirror the CRUD
    operations of every other domain resource onto the GraphQL Interface as well. Returns the GraphQL Interface ops."""
    import copy
    gql = []
    for p in list(paths):
        item = paths[p]
        shared = item.get("parameters", [])
        for m in ("get", "post", "delete"):
            op = item.get(m)
            if not op or is_graphql(op["operationId"]):
                continue
            verb = op["operationId"].split(".")[-1]
            if verb in CRUD_VERBS and op["tags"][0] not in NO_DATA_TAGS and not p.startswith("/v1/inbound/"):
                gql.append({"path": p, "method": m, "op": copy.deepcopy(op), "path_params": [x for x in shared if x.get("in") == "path"], "mirrored": True})
    for p in list(paths):
        item = paths[p]
        shared = item.get("parameters", [])
        for m in ("get", "post", "delete"):
            op = item.get(m)
            if op and is_graphql(op["operationId"]):
                gql.append({"path": p, "method": m, "op": op, "path_params": [x for x in shared if x.get("in") == "path"]})
                del item[m]
        if not any(k in item for k in ("get", "post", "delete")):
            del paths[p]
    return gql


def prune_schemas(doc):
    """Drop component schemas no longer referenced from the REST document."""
    import json
    schemas = doc["components"]["schemas"]
    keep, todo = set(), []
    body = json.dumps({k: v for k, v in doc.items() if k != "components"} | {"r": doc["components"].get("responses", {})})
    todo += re.findall(r"#/components/schemas/([A-Za-z0-9_]+)", body)
    while todo:
        n = todo.pop()
        if n in keep or n not in schemas:
            continue
        keep.add(n)
        todo += re.findall(r"#/components/schemas/([A-Za-z0-9_]+)", json.dumps(schemas[n]))
    for n in list(schemas):
        if n not in keep:
            del schemas[n]
    return len(schemas)


# ---------------- SDL emission ----------------
IRREG = {"facilities": "facility", "ledger_entries": "ledger_entry", "access_policies": "access_policy", "stock": "stock",
         "billing_profile": "billing_profile", "statuses": "status"}


def singular(word):
    if word in IRREG:
        return IRREG[word]
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("ses") and not word.endswith("uses"):
        return word[:-1]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def pascal(s):
    return "".join(w[:1].upper() + w[1:] for w in re.split(r"[^A-Za-z0-9]+", s) if w)


def camel(s):
    p = pascal(s)
    return p[:1].lower() + p[1:]


def field_name(op_id, method="post"):
    parts = op_id.split(".")
    verb, res = parts[-1], parts[:-1]
    if parts[0] == "accounts" and verb.startswith("member_"):
        return camel(verb.replace("member_", "") + "_member") if verb != "member_list" else "networkMembers"
    if verb == "list":
        return camel("_".join([singular(r) for r in res[:-1]] + [res[-1]]))
    if verb == "retrieve":
        return camel("_".join(singular(r) for r in res))
    if verb == "search":
        return camel("search_" + "_".join(res))
    if method == "get":
        return camel("_".join(singular(r) for r in res) + "_" + verb)
    return camel(verb + "_" + "_".join(singular(r) for r in res))


NAME_OK = re.compile(r"^[_A-Za-z][_0-9A-Za-z]*$")


class SDL:
    def __init__(self, schemas):
        self.schemas = schemas
        self.out_types, self.in_types, self.enums = {}, {}, {}
        self.pending_out, self.pending_in = [], []

    # --- helpers
    def enum_type(self, name, values):
        vals = []
        for v in values:
            if v is None:
                continue
            v = str(v)
            if not NAME_OK.match(v) or v in ("true", "false", "null"):
                v = "_" + re.sub(r"[^_0-9A-Za-z]", "_", v)
            vals.append(v)
        if not vals:
            return "String"
        key = tuple(vals)
        for n, vs in self.enums.items():
            if vs == key and n.startswith(name[:0]):
                if n == name:
                    return n
        if (name in self.schemas or name in self.out_types or name in self.in_types) and name not in self.enums:
            name = name + "Enum"
        base, i = name, 2
        while name in self.enums and self.enums[name] != key:
            name = f"{base}{i}"; i += 1
        self.enums[name] = key
        return name

    def resolve(self, sch, ctx, is_input):
        """Return (type_name, nullable) for a JSON-schema fragment."""
        if sch is None or sch == {}:
            return "JSON", True
        if "$ref" in sch:
            n = sch["$ref"].split("/")[-1]
            return self.named(n, is_input), True
        if "anyOf" in sch or "oneOf" in sch:
            alts = sch.get("anyOf") or sch.get("oneOf")
            non_null = [a for a in alts if a.get("type") != "null"]
            if len(non_null) == 1:
                t, _ = self.resolve(non_null[0], ctx, is_input)
                return t, True
            refs = [a for a in non_null if "$ref" in a]
            if refs and not is_input:
                return self.named(refs[0]["$ref"].split("/")[-1], False), True
            return "JSON", True
        t = sch.get("type")
        if "enum" in sch:
            vals = [v for v in sch["enum"] if v is not None]
            if vals == ["true"]:
                return "Boolean", True
            if t in (None, "string"):
                return self.enum_type(ctx, vals), True
        if t == "string":
            return "String", True
        if t == "integer":
            return "Int", True
        if t == "number":
            return "Float", True
        if t == "boolean":
            return "Boolean", True
        if t == "null":
            return "JSON", True
        if t == "array":
            inner, _ = self.resolve(sch.get("items"), ctx + "Item", is_input)
            return f"[{inner}!]", True
        if t == "object" or "properties" in sch:
            props = sch.get("properties") or {}
            ap = sch.get("additionalProperties", None)
            if not props or (ap not in (None, False)):
                return "JSON", True
            return self.inline_object(ctx, sch, is_input), True
        return "JSON", True

    def named(self, n, is_input):
        sch = self.schemas[n]
        if sch.get("type") != "object" and "properties" not in sch:
            return self.resolve(sch, n, is_input)[0]
        if is_input:
            name = n if n.endswith(("Input", "Create", "Update", "Request")) else n + "Input"
            if name not in self.in_types and name not in self.pending_in:
                self.pending_in.append(name)
                self.in_types[name] = None
                self.in_types[name] = self.object_body(name, sch, True)
            return name
        t, _ = (None, None)
        if sch.get("type") != "object" and "properties" not in sch:
            t, _ = self.resolve(sch, n, False)
            return t
        on = re.sub(r"(Input|Create|Update|Request)$", "Spec", n)
        if on not in self.out_types:
            self.out_types[on] = None
            self.out_types[on] = self.object_body(on, sch, False)
        return on

    def inline_object(self, name, sch, is_input):
        store = self.in_types if is_input else self.out_types
        name = name + ("Input" if is_input and not name.endswith("Input") else "")
        if not is_input and (name in self.schemas or name in self.enums) and name not in store:
            name = name + "Type"
        if name not in store:
            store[name] = None
            store[name] = self.object_body(name, sch, is_input)
        return name

    def object_body(self, name, sch, is_input):
        props = sch.get("properties") or {}
        req = set(sch.get("required") or [])
        if not props or sch.get("additionalProperties") not in (None, False):
            return [("value", "JSON", True)]
        fields = []
        READ_ONLY = {"id", "object", "livemode", "created", "updated", "carrier_metadata", "system_metadata"}
        for k, v in props.items():
            if not NAME_OK.match(k):
                continue
            if is_input and (k in READ_ONLY or (isinstance(v, dict) and v.get("readOnly"))):
                continue
            t, nullable = self.resolve(v, name + pascal(k), is_input)
            nn = (k in req) and not is_input and not (isinstance(v, dict) and "anyOf" in v)
            fields.append((k, t, not nn))
        return fields or [("value", "JSON", True)]

    def render(self, query_fields, mutation_fields):
        lines = ['"""Open Logistics Specs, GraphQL surface (back-office, internal and LSP account management).',
                 'Generated by tools/build_openapi.py. Objects are the same canonical objects as the REST surface."""',
                 "scalar JSON", "",
                 "type DeletedObject {\n  id: ID!\n  object: String!\n  deleted: Boolean!\n}", ""]
        for n, vs in sorted(self.enums.items()):
            lines.append(f"enum {n} {{\n" + "\n".join(f"  {v}" for v in vs) + "\n}\n")
        for n, fs in sorted(self.out_types.items()):
            lines.append(f"type {n} {{\n" + "\n".join(f"  {k}: {t}{'' if nul else '!'}" for k, t, nul in fs) + "\n}\n")
        for n, fs in sorted(self.in_types.items()):
            lines.append(f"input {n} {{\n" + "\n".join(f"  {k}: {t}" for k, t, nul in fs) + "\n}\n")
        lines.append("type Query {\n" + "\n".join(query_fields) + "\n}\n")
        lines.append("type Mutation {\n" + "\n".join(mutation_fields) + "\n}\n")
        return "\n".join(lines)


def arg_name(p):
    return camel(re.sub(r"[\[\]\.]", "_", p))


def emit(gql_ops, schemas, sdl_path, md_path):
    sdl = SDL(schemas)
    q_fields, m_fields, rows, recs = [], [], [], []
    seen = set()
    for g in gql_ops:
        op = g["op"]
        oid = op["operationId"]
        fname = field_name(oid, g["method"])
        if fname in seen:
            fname = fname + pascal(g["method"])
        seen.add(fname)
        args, sargs, input_type = [], [], None
        for prm in g["path_params"]:
            args.append(f"{arg_name(prm['name'])}: ID!")
            sargs.append((arg_name(prm['name']), "ID!", "The object's ID." if prm['name'] == 'id' else f"The {prm['name'].replace('_', ' ')}."))
        for prm in op.get("parameters", []):
            if "$ref" in prm or prm.get("in") != "query":
                continue
            t, _ = sdl.resolve(prm.get("schema"), pascal(fname) + pascal(prm["name"]), True)
            args.append(f"{arg_name(prm['name'])}: {t}")
            sargs.append((arg_name(prm['name']), t, prm.get('description') or f"Filter by {prm['name'].replace('_', ' ').replace('[', ' ').replace(']', '')}."))
        body = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
        if body:
            if "$ref" in body:
                t = sdl.named(body["$ref"].split("/")[-1], True)
            else:
                t, _ = sdl.resolve(body, pascal(fname) + "Input", True)
            if t != "JSON" or body.get("properties"):
                args.append(f"input: {t}")
                sargs.append(("input", t, "The fields for this operation."))
                input_type = t
        ok = None
        for code in ("200", "202"):
            r = op.get("responses", {}).get(code)
            if r and "content" in r:
                ok = next(iter(r["content"].values())).get("schema"); break
        if ok and ok.get("properties", {}).get("data") and ok["properties"].get("object", {}).get("enum") == ["list"]:
            item, _ = sdl.resolve(ok["properties"]["data"]["items"], pascal(fname) + "Item", False)
            lname = item + "List"
            sdl.out_types.setdefault(lname, [("data", f"[{item}!]", False), ("has_more", "Boolean", True)])
            if g["method"] == "get" and oid.endswith(".list"):
                args += ["limit: Int", "startingAfter: ID", "endingBefore: ID"]
                sargs += [("limit", "Int", "Page size, 1–100 (default 10)."), ("startingAfter", "ID", "Cursor: return objects after this ID."), ("endingBefore", "ID", "Cursor: return objects before this ID.")]
            rtype = lname + "!"
        elif ok:
            t, _ = sdl.resolve(ok, pascal(fname) + "Result", False)
            rtype = ("DeletedObject" if t == "Deleted" else t) + "!"
        else:
            rtype = "JSON"
        sig = f"  {fname}{'(' + ', '.join(args) + ')' if args else ''}: {rtype}"
        doc = op.get("summary", "").replace('"', "'")
        line = f'  "{doc}"\n{sig}'
        is_query = g["method"] == "get"
        (q_fields if is_query else m_fields).append(line)
        rows.append((op["tags"][0], "query" if is_query else "mutation", fname, op.get("summary", ""), f"{g['method'].upper()} {g['path']}"))
        scopes = [sc for sec in op.get("security", []) for sc in sec.get("oauth2", [])]
        recs.append({"tag": op["tags"][0], "kind": "query" if is_query else "mutation", "field": fname, "summary": op.get("summary", ""), "description": op.get("description", ""), "args": sargs, "input": input_type, "returns": rtype, "scopes": scopes, "money": bool(op.get("x-spends-money")), "idem": any(isinstance(x, dict) and x.get("$ref", "").endswith("IdempotencyKeyRequired") for x in op.get("parameters", []))})
    sdl.out_types.pop("Deleted", None)
    text = sdl.render(q_fields, m_fields)
    pathlib.Path(sdl_path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(sdl_path).write_text(text)
    write_reference(rows, md_path)
    import graphql_pages as _gp
    _gp.write_pages(recs, sdl, schemas)
    import json as _j
    (ROOT / "graphql" / "operations.json").write_text(_j.dumps([{"tag": r[0], "kind": r[1], "field": r[2], "summary": r[3], "rest": r[4]} for r in rows], indent=1))
    return len(q_fields), len(m_fields), text


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def kebab(n):
    return re.sub(r"(?<!^)(?=[A-Z])", "-", n).lower()


def write_reference(rows, md_path):
    groups = {}
    for tag, kind, name, summary, legacy in rows:
        groups.setdefault(tag, []).append((kind, name, summary))
    out = ['---', 'title: "GraphQL Interface"',
           'description: "Internal CRUD over every domain object (shipments, trackers, fleet, routes, catalog, billing…) plus the back-office operations, over GraphQL. Generated from the same object model as the REST Interface."',
           '---', '',
           'The specification has two interfaces over **one object model**:', '',
           '| Interface | For | Covers | Endpoint |', '|---|---|---|---|',
           '| **REST Interface** | Integrators: shippers, platforms, partners, devices and agents | Each module\'s public workflows and actions: rate, purchase, void, book, close, track, inject, generate, verify | `https://{host}/v1/…`, in the REST Interface tab |',
           '| **GraphQL Interface** | Internal tools: implementer dashboards, operations consoles, carrier and network member administration, data teams | CRUD over **every** domain object (shipments, trackers, pickups, manifests, products, fleet, routes, catalog, invoices…), plus the back-office operations that exist only here | `POST https://{host}/graphql` |', '',
           'Both interfaces return the same canonical objects with the same field names, IDs, enums and metadata namespaces. A `Shipment` from `query { shipment(id:) }` is the object `GET /v1/shipments/{id}` returns. CRUD operations available on both interfaces behave identically: same validation, same state rules, same events.', '',
           '## Conventions', '',
           '- **Authentication and scopes** are the same as REST (Conventions §3): `Authorization: Bearer …`, `Shipping-Version`, and `Shipping-Account` to act for a connected or member account. Each field requires the scope of its REST counterpart (`shipments:write` for `createShipment`, `catalog:write` for `createService`).',
           '- **Idempotency.** Mutations that create or act accept the `Idempotency-Key` header, with the same rules as Conventions §8. Fields that spend money are flagged on their page.',
           '- **Errors** use the standard GraphQL `errors[]`, and `extensions` carries the REST error object: `extensions.type`, `extensions.code` (the Conventions §9 registry), `extensions.param`, `extensions.request_id`.',
           '- **Lists** return `{ data, has_more }` with `limit`, `startingAfter` and `endingBefore` arguments, mirroring REST cursor pagination.',
           '- **Events.** Mutations emit the same webhook events as their REST counterparts. Subscribing over GraphQL (`subscription { events(types: […]) }`) is an optional capability (`graphql.subscriptions`).',
           '- **Schema.** The full SDL is published at [`graphql/schema.graphql`](/graphql/schema.graphql), and implementers SHOULD serve introspection to authenticated clients.', '',
           'Every field below has its own page with arguments, return fields and request, variables and response examples. Module chapters describe the behavior.', '']
    for tag in sorted(groups):
        out.append(f"## {tag}\n")
        out.append("| Field | Kind | What it does |")
        out.append("|---|---|---|")
        for kind, name, summary in groups[tag]:
            out.append(f"| [`{name}`](/graphql-reference/{slug(tag)}/{kebab(name)}) | {kind} | {summary} |")
        out.append("")
    pathlib.Path(md_path).write_text("\n".join(out))
