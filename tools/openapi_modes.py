"""Split the REST document into one OpenAPI file per implementation mode.

Used by build_openapi.py. The mode profiles mirror the matrix in spec/12-modes.md §2:
a mode's file holds every module marked R (required) or O (optional) for it.
"""
import copy
import pathlib
import re
import shutil

import yaml

import graphql_surface as GS

# REST tag -> module (spec/12-modes.md §1)
TAG_MODULE = {
    "Rates": "core", "Shipments": "core", "Tracking": "core", "Events": "core", "Batches": "core",
    "Test Helpers": "core", "Carriers": "core", "Discovery": "core",
    "Pickups": "pickups", "Pickup Schedules": "pickups",
    "Manifests": "manifests",
    "Files": "documents", "Document Uploads": "documents",
    "Webhooks": "webhooks", "Inbound": "webhooks",
    "Connections": "connections", "Apps": "connections",
    "Accounts": "platform",
    "Trade": "trade", "Catalog": "catalog", "Pricing": "pricing", "Routes": "routes", "Fleet": "fleet",
    "Injection": "injection", "Products": "products", "Network": "network", "IoT": "iot",
    "Consolidation": "consolidation", "Templates": "templates", "Integrations": "integrations",
    "Jobs": "jobs", "Inventory": "inventory", "Billing": "billing", "Data Network": "data_network",
}

# spec/12-modes.md §2. R = required, O = optional, RO = read-only replica (GET operations only),
# RQ = required for reads only (the module's REST operations are all queries). Absent = not part of the mode.
MATRIX = {
    #                 universal carrier network 3pl  fleet  data
    "core":          ("R",      "R",    "R",    "R", "R",   "RO"),
    "webhooks":      ("R",      "R",    "R",    "R", "R",   "R"),
    "pickups":       ("O",      "R",    "R",    "O", "O",   None),
    "manifests":     ("O",      "O",    "O",    "O", None,  None),
    "documents":     ("O",      "O",    "O",    "O", None,  None),
    "connections":   ("R",      None,   "O",    "O", "O",   None),
    "platform":      ("O",      "R",    "R",    "O", "O",   "R"),
    "catalog":       ("RQ",     "R",    "R",    "R", "R",   None),
    "pricing":       ("O",      "R",    "R",    "R", "R",   None),
    "trade":         ("O",      "R",    "O",    "R", None,  None),
    "routes":        (None,     "R",    "R",    "R", "R",   None),
    "fleet":         (None,     "O",    "O",    "O", "R",   None),
    "injection":     (None,     "O",    "R",    "R", "O",   None),
    "products":      ("O",      "O",    "O",    "R", "O",   None),
    "network":       (None,     None,   "R",    None, None, None),
    "iot":           (None,     "O",    "O",    "O", "O",   None),
    "consolidation": (None,     "R",    "R",    "R", "O",   None),
    "templates":     ("O",      "O",    "O",    "R", "O",   None),
    "integrations":  ("R",      "O",    "R",    "O", "O",   None),
    "jobs":          ("R",      "R",    "R",    "R", "R",   "R"),
    "inventory":     ("O",      "O",    "O",    "R", None,  None),
    "billing":       ("O",      "R",    "R",    "R", "O",   None),
    "data_network":  ("O",      "O",    "O",    "O", "O",   "R"),
}

# (slug, column, title, who)
MODES = [
    ("universal", 0, "Universal", "multi-carrier platforms and aggregators that reach other carriers' networks through one API"),
    ("carrier", 1, "Carrier", "parcel carriers, postal operators and cross-border networks selling their own network"),
    ("network", 2, "Network", "carrier and LSP networks, marketplaces and alliances whose members serve first, middle or last mile"),
    ("3pl", 3, "3PL", "third-party logistics and fulfillment providers shipping on behalf of many merchants"),
    ("fleet", 4, "Fleet", "operators running their own vans, trucks, aircraft, drones or vessels"),
    ("data-network", 5, "Data Network", "nodes of the shared, verifiable logistics data network"),
]
LEVEL = {"R": "Required", "O": "Optional", "RO": "Required, read-only", "RQ": "Required, read-only"}
METHODS = ("get", "post", "put", "patch", "delete")


def mode_doc(doc, col, title, who):
    out = copy.deepcopy(doc)
    levels = {m: row[col] for m, row in MATRIX.items() if row[col]}
    paths = {}
    for p, item in out["paths"].items():
        kept = {}
        for k, v in item.items():
            if k not in METHODS:
                continue
            level = levels.get(TAG_MODULE[v["tags"][0]])
            if level and (level != "RO" or k == "get"):
                kept[k] = v
        if kept:
            paths[p] = {k: v for k, v in item.items() if k not in METHODS} | kept
    out["paths"] = paths
    used = {op["tags"][0] for it in paths.values() for k, op in it.items() if k in METHODS}
    out["tags"] = [dict(t, description=f"Module `{TAG_MODULE[t['name']]}`: {LEVEL[levels[TAG_MODULE[t['name']]]].lower()} in {title} mode.")
                   for t in out["tags"] if t["name"] in used]
    rows = "\n".join(f"| `{m}` | {LEVEL[l]} |" for m, l in levels.items())
    out["info"]["title"] = f"Open Logistics Specs: {title} mode"
    out["info"]["description"] = (
        f"The REST Interface as implemented in **{title} mode**, for {who}. "
        "It contains only the modules this mode supports (spec/12-modes.md §2); the complete document is `/openapi.yaml`.\n\n"
        "| Module | In this mode |\n|---|---|\n" + rows + "\n\n" + doc["info"]["description"])
    out["info"]["x-mode"] = title
    GS.prune_schemas(out)
    return out, sum(1 for it in paths.values() for k in it if k in METHODS)


def emit(doc, outdir, dumper):
    outdir = pathlib.Path(outdir)
    outdir.mkdir(exist_ok=True)
    counts = {}
    for slug, col, title, who in MODES:
        d, n = mode_doc(doc, col, title, who)
        yaml.dump(d, open(outdir / f"{slug}.yaml", "w"), Dumper=dumper, sort_keys=False, width=140, allow_unicode=True)
        counts[slug] = n
    return counts


def kebab(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _group(title, tags, ops_by_tag):
    return {"group": title, "pages": [{"group": t, "pages": ops_by_tag[t]} for t in tags]}


def write_nav(root):
    """Write one overview page per mode and the REST Interface tab (a mode dropdown) into docs.json."""
    import json
    root = pathlib.Path(root)
    menu = []
    for slug, col, title, who in MODES:
        d = yaml.safe_load(open(root / "openapi" / f"{slug}.yaml"))
        levels = {m: row[col] for m, row in MATRIX.items() if row[col]}
        # One stub page per operation; `mint export` cannot resolve inline "METHOD /path" navigation entries.
        out = root / "api-reference" / slug
        if out.exists():
            shutil.rmtree(out)
        ops_by_tag, mods = {}, {}
        for p, item in d["paths"].items():
            for k, v in item.items():
                if k in METHODS:
                    t = v["tags"][0]
                    page = f"api-reference/{slug}/{kebab(t)}/{kebab(v['summary'])}"
                    (root / page).parent.mkdir(parents=True, exist_ok=True)
                    (root / f"{page}.mdx").write_text(f'---\nopenapi: "openapi/{slug}.yaml {k.upper()} {p}"\n---\n')
                    ops_by_tag.setdefault(t, []).append(page)
                    mods.setdefault(TAG_MODULE[t], []).append(t)
        tags = [t["name"] for t in d["tags"]]
        req = [t for t in tags if levels[TAG_MODULE[t]] != "O"]
        opt = [t for t in tags if levels[TAG_MODULE[t]] == "O"]
        page = f"api-reference/{slug}/overview"
        rows = []
        for m, l in levels.items():
            ts = sorted(set(mods.get(m, [])), key=tags.index)
            n = sum(len(ops_by_tag[t]) for t in ts)
            rows.append(f"| `{m}` | {LEVEL[l]} | {', '.join(ts) if ts else 'GraphQL Interface only'} | {n or '—'} |")
        absent = [m for m, row in MATRIX.items() if not row[col]]
        total = sum(len(v) for v in ops_by_tag.values())
        body = f"""---
title: "{title} mode"
description: "The REST operations a {title} implementation exposes: {total} operations across {len(levels)} modules."
---

**{title} mode** is for {who}. This reference lists only the operations a {title} implementation exposes, following the mode profile in [Modes §2](/spec/12-modes). Switch modes from the **REST Interface** tab menu at the top of the page.

| Module | In this mode | Operations | Count |
|---|---|---|---|
{chr(10).join(rows)}

Required modules are grouped first in the sidebar, optional ones after. {('Not part of this mode: ' + ', '.join(f'`{m}`' for m in absent) + '.') if absent else 'Every module is part of this mode.'}{' Core objects are a read-only replica in this mode, so only their read operations appear.' if levels.get('core') == 'RO' else ''}

The machine-readable file for this mode is [`/openapi/{slug}.yaml`](/openapi/{slug}.yaml). The complete document, with every module, is [`/openapi.yaml`](/openapi.yaml).
"""
        (root / f"{page}.mdx").write_text(body)
        groups = [{"group": "Overview", "pages": [page]}, _group("Required modules", req, ops_by_tag)]
        if opt:
            groups.append(_group("Optional modules", opt, ops_by_tag))
        menu.append({"item": title, "description": f"{total} operations", "groups": groups})
    dj = root / "docs.json"
    cfg = json.loads(dj.read_text())
    for i, t in enumerate(cfg["navigation"]["tabs"]):
        if t["tab"] == "REST Interface":
            cfg["navigation"]["tabs"][i] = {"tab": "REST Interface", "menu": menu}
    dj.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
