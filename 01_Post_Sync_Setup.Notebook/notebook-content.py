# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {}
# META   }
# META }

# MARKDOWN ********************

# # 01 · Post-Sync Setup (one-shot)
#
# After your workspace is connected to Git and items are synced, **run this notebook once**. It auto-configures:
#
# 1. **KQL ingestion mappings** + streaming ingestion policy on the 5 Eventhouse tables (so Eventstream destinations land data in all columns, not just `stream_type`).
# 2. **Default Lakehouse binding** on the 4 notebooks (`AegeanPower_Simulator`, `Demo_Trigger_Console`, `Dispatch_Maintenance_Crew`, `Load_CSVs_to_Delta`).
# 3. **Eventstream connection string** auto-inserted into `AegeanPower_Simulator` (replaces the `REPLACE_ME_…` placeholder).
# 4. **Real-Time Dashboard** cluster URI rebind to your local Eventhouse.
#
# After this notebook succeeds, the remaining steps are:
# - Upload CSVs to `AegeanPowerLH/Files/data` (Step 5 in README).
# - Run `Load_CSVs_to_Delta` (Step 6).
# - Re-bind the Ontology data bindings (UI — Step 11).
# - Add a data source to `AegeanPowerDataAgent` (UI — Step 12).
#
# > No external SDK; uses `notebookutils.credentials.getToken` for Fabric and Kusto APIs.
#

# MARKDOWN ********************

# ## 1 · Discover the workspace and items

# CELL ********************

import json, base64, time, requests, re
import notebookutils

WS_ID = notebookutils.runtime.context.get("currentWorkspaceId") or notebookutils.runtime.context.get("workspaceId")
print(f"Workspace ID: {WS_ID}")

def fab_token():
    return notebookutils.credentials.getToken("https://api.fabric.microsoft.com")

def fab(method, path, body=None, raise_on_error=True):
    tok = fab_token()
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    url = f"https://api.fabric.microsoft.com/v1{path}"
    r = requests.request(method, url, headers=h, json=body, timeout=60)
    if raise_on_error and not r.ok and r.status_code != 202:
        raise RuntimeError(f"{method} {path} -> {r.status_code} {r.text[:500]}")
    return r

def fab_lro(method, path, body=None, max_wait=180):
    r = fab(method, path, body, raise_on_error=False)
    if r.status_code in (200, 201):
        return r.json() if r.text else None
    if r.status_code != 202:
        raise RuntimeError(f"{method} {path} -> {r.status_code} {r.text[:500]}")
    loc = r.headers.get("Location")
    if not loc:
        return None
    tok = fab_token()
    waited = 0
    while waited < max_wait:
        time.sleep(3); waited += 3
        p = requests.get(loc, headers={"Authorization": f"Bearer {tok}"}, timeout=30)
        if p.status_code != 200:
            continue
        data = p.json()
        if data.get("status") == "Succeeded":
            res = requests.get(loc + "/result", headers={"Authorization": f"Bearer {tok}"}, timeout=30)
            if res.ok and res.text:
                return res.json()
            return data
        if data.get("status") == "Failed":
            raise RuntimeError(f"LRO failed: {json.dumps(data, indent=2)[:500]}")
    raise RuntimeError(f"LRO timeout after {max_wait}s")

# Discover items by displayName
items = fab("GET", f"/workspaces/{WS_ID}/items").json().get("value", [])
by_name = {(i["type"], i["displayName"]): i["id"] for i in items}

def find(t, name, required=True):
    iid = by_name.get((t, name))
    if iid:
        print(f"  found {t:18s} {name:35s} {iid}")
    elif required:
        raise RuntimeError(f"missing item: type={t} name={name}")
    else:
        print(f"  (skip) no {t}/{name} in workspace")
    return iid

print("\nDiscovered items:")
LAKEHOUSE_ID = find("Lakehouse",  "AegeanPowerLH")
EH_ID        = find("Eventhouse", "AegeanPowerEH")
ES_ID        = find("Eventstream","AegeanPowerStream")
SIM_NB_ID    = find("Notebook",   "AegeanPower_Simulator")
DT_NB_ID     = find("Notebook",   "Demo_Trigger_Console")
DC_NB_ID     = find("Notebook",   "Dispatch_Maintenance_Crew")
LD_NB_ID     = find("Notebook",   "Load_CSVs_to_Delta")
DASH_ID      = find("KQLDashboard","AegeanPower_Live_Operations", required=False)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 2 · Configure KQL: ingestion mappings + streaming policy

# CELL ********************

# Eventhouse query/ingestion endpoint
eh = fab("GET", f"/workspaces/{WS_ID}/eventhouses/{EH_ID}").json()
CLUSTER_URI = eh["properties"]["queryServiceUri"]
DB_NAME = "AegeanPowerEH"
print(f"Cluster: {CLUSTER_URI}")
print(f"DB:      {DB_NAME}")

def kql(csl, op="mgmt"):
    tok = notebookutils.credentials.getToken("https://kusto.kusto.windows.net")
    r = requests.post(f"{CLUSTER_URI}/v1/rest/{op}",
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                      json={"db": DB_NAME, "csl": csl}, timeout=60)
    r.raise_for_status()
    return r.json()

# Per-table schema + JSON mapping (must match the simulator output)
TABLES = {
    "WindTurbineTelemetry": [
        ("timestamp","datetime"),("stream_type","string"),("turbine_id","string"),("plant_id","string"),
        ("power_mw","real"),("wind_speed_ms","real"),("vibration_mm_s","real"),("rotor_rpm","real"),
        ("nacelle_temp_c","real"),("latitude","real"),("longitude","real"),("fault_type","string"),
    ],
    "SolarInverterTelemetry": [
        ("timestamp","datetime"),("stream_type","string"),("inverter_id","string"),("plant_id","string"),
        ("power_kw","real"),("irradiance_wm2","real"),("panel_temp_c","real"),("efficiency_pct","real"),
        ("latitude","real"),("longitude","real"),("fault_type","string"),
    ],
    "GridTelemetry": [
        ("timestamp","datetime"),("stream_type","string"),("grid_id","string"),("grid_name","string"),
        ("frequency_hz","real"),("load_mw","real"),("generation_mw","real"),("voltage_kv","real"),("balance_mw","real"),
    ],
    "VesselPositions": [
        ("timestamp","datetime"),("stream_type","string"),("vessel_id","string"),("vessel_name","string"),
        ("vessel_type","string"),("latitude","real"),("longitude","real"),("speed_knots","real"),
        ("heading_deg","real"),("destination","string"),("eta_hours","real"),("cargo_status","string"),
    ],
    "EmissionsStream": [
        ("timestamp","datetime"),("stream_type","string"),("plant_id","string"),("plant_name","string"),
        ("power_output_mw","real"),("co2_kg_per_hour","real"),("cumulative_co2_tonnes_today","real"),
        ("ets_daily_allowance_tonnes","real"),("compliance_pct","real"),("fuel_type","string"),("fault_type","string"),
    ],
}

for tbl, cols in TABLES.items():
    col_csl = ", ".join(f"{c}:{t}" for c, t in cols)
    kql(f".create-merge table {tbl} ({col_csl})")
    mapping = [{"column": c, "path": f"$.{c}"} for c, _ in cols]
    kql(f".create-or-alter table {tbl} ingestion json mapping 'AutoMapping' '" + json.dumps(mapping) + "'")
    kql(f".alter table {tbl} policy streamingingestion enable")
    print(f"  OK  {tbl}: schema + AutoMapping + streaming policy")

print("\nKQL setup complete.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 3 · Bind `AegeanPowerLH` as default Lakehouse on the 4 notebooks

# CELL ********************

LAKEHOUSE_DEPENDENCY = {
    "lakehouse": {
        "default_lakehouse": LAKEHOUSE_ID,
        "default_lakehouse_name": "AegeanPowerLH",
        "default_lakehouse_workspace_id": WS_ID,
        "known_lakehouses": [{"id": LAKEHOUSE_ID}],
    }
}

def bind_notebook_lakehouse(nb_id, display_name):
    print(f"  {display_name} ({nb_id}) ...")
    # 1. Get current definition
    defn = fab_lro("POST", f"/workspaces/{WS_ID}/notebooks/{nb_id}/getDefinition?format=ipynb")
    parts = defn["definition"]["parts"]
    # 2. Patch the notebook-content.ipynb metadata
    found = False
    for p in parts:
        if p["path"].endswith(".ipynb"):
            raw = base64.b64decode(p["payload"]).decode("utf-8")
            nb = json.loads(raw)
            nb.setdefault("metadata", {})
            nb["metadata"].setdefault("dependencies", {})
            nb["metadata"]["dependencies"] = LAKEHOUSE_DEPENDENCY
            new = json.dumps(nb, separators=(",", ":"))
            p["payload"] = base64.b64encode(new.encode("utf-8")).decode("ascii")
            p["payloadType"] = "InlineBase64"
            found = True
            break
    if not found:
        raise RuntimeError(f"no .ipynb part in {display_name}")
    # 3. Push back
    body = {"definition": {"format": "ipynb", "parts": parts}}
    fab_lro("POST", f"/workspaces/{WS_ID}/notebooks/{nb_id}/updateDefinition", body=body)
    print(f"     OK  default lakehouse bound")

for nb_id, name in [
    (SIM_NB_ID, "AegeanPower_Simulator"),
    (DT_NB_ID,  "Demo_Trigger_Console"),
    (DC_NB_ID,  "Dispatch_Maintenance_Crew"),
    (LD_NB_ID,  "Load_CSVs_to_Delta"),
]:
    bind_notebook_lakehouse(nb_id, name)

print("\nAll 4 notebooks now have AegeanPowerLH as default lakehouse.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 4 · Fetch Eventstream connection string + patch the simulator notebook

# CELL ********************

# 1. Get the Eventstream topology to find the CustomEndpoint source id
topo = fab("GET", f"/workspaces/{WS_ID}/eventstreams/{ES_ID}/topology").json()
src = next(s for s in topo["sources"] if s["type"] == "CustomEndpoint")
SRC_ID = src["id"]
print(f"CustomApp source: {SRC_ID}")

# 2. Get the primary connection string
conn = fab("GET", f"/workspaces/{WS_ID}/eventstreams/{ES_ID}/sources/{SRC_ID}/connection").json()
PRIMARY = conn["accessKeys"]["primaryConnectionString"]
masked = PRIMARY[:60] + "...[REDACTED]..." + PRIMARY[-30:]
print(f"Connection string: {masked}")

# 3. Patch the simulator notebook
defn = fab_lro("POST", f"/workspaces/{WS_ID}/notebooks/{SIM_NB_ID}/getDefinition?format=ipynb")
parts = defn["definition"]["parts"]
for p in parts:
    if p["path"].endswith(".ipynb"):
        raw = base64.b64decode(p["payload"]).decode("utf-8")
        nb = json.loads(raw)
        # Replace placeholder (or any prior connection string) in any cell source line
        pattern = re.compile(r'EVENTHUB_CONNECTION_STRING\s*=\s*"[^"]*"')
        replacement = f'EVENTHUB_CONNECTION_STRING = "{PRIMARY}"'
        replaced = 0
        for c in nb.get("cells", []):
            if c.get("cell_type") != "code":
                continue
            new_src = []
            for line in c.get("source", []):
                if pattern.search(line):
                    line = pattern.sub(replacement, line)
                    replaced += 1
                new_src.append(line)
            c["source"] = new_src
        if replaced == 0:
            raise RuntimeError("EVENTHUB_CONNECTION_STRING line not found in simulator notebook")
        print(f"  patched {replaced} line(s)")
        new = json.dumps(nb, separators=(",", ":"))
        p["payload"] = base64.b64encode(new.encode("utf-8")).decode("ascii")
        break

fab_lro("POST", f"/workspaces/{WS_ID}/notebooks/{SIM_NB_ID}/updateDefinition",
        body={"definition": {"format": "ipynb", "parts": parts}})
print("Simulator notebook updated with connection string.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 5 · Rebind Real-Time Dashboard cluster URI to your local Eventhouse

# CELL ********************

if not DASH_ID:
    print("  no dashboard in workspace, skipping")
else:
    defn = fab_lro("POST", f"/workspaces/{WS_ID}/kqlDashboards/{DASH_ID}/getDefinition")
    parts = defn["definition"]["parts"]
    for p in parts:
        if p["path"].endswith(".json") and "Dashboard" in p["path"]:
            raw = base64.b64decode(p["payload"]).decode("utf-8")
            dash = json.loads(raw)
            for ds in dash.get("dataSources", []):
                if ds.get("name") == "AegeanPowerEH":
                    ds["clusterUri"] = CLUSTER_URI
                    ds["database"] = DB_NAME
                    print(f"  rebound data source -> {CLUSTER_URI}")
            new = json.dumps(dash, separators=(",", ":"))
            p["payload"] = base64.b64encode(new.encode("utf-8")).decode("ascii")
            break

    fab_lro("POST", f"/workspaces/{WS_ID}/kqlDashboards/{DASH_ID}/updateDefinition",
            body={"definition": {"parts": parts}})
    print("Dashboard updated.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 6 · Summary
#
# ✅ Done automatically:
#
# - KQL ingestion mappings (`AutoMapping`) + streaming ingestion policy on 5 tables
# - `AegeanPowerLH` bound as default on 4 notebooks
# - Simulator notebook patched with the live Eventstream connection string
# - Real-Time Dashboard cluster URI rebound
#
# 📝 Still to do (UI-only):
#
# 1. **Open `AegeanPowerStream` → Edit → Publish.** The destinations now have valid mappings; publish lights up streaming ingestion across all 5 tables.
# 2. **Upload `data/` CSVs** to `AegeanPowerLH/Files/data` → run `Load_CSVs_to_Delta`.
# 3. **Run `AegeanPower_Simulator`** → start the live data flow.
# 4. **`AegeanPowerOntology`** → open each entity → re-pick its KQL/Lakehouse data binding source (UI rebind, ~1 min).
# 5. **`AegeanPowerDataAgent`** → Add data source → pick `AegeanPowerOntology` (or `AegeanPowerLH` directly).
#
# Then you're ready to demo.
#
