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
# After Git sync, **run this notebook once** and (almost) everything is configured.
# Idempotent — safe to re-run.
#
# After this notebook succeeds, you only need to:
# 1. Run **`AegeanPower_Simulator`** (Run all)
# 2. Add **`AegeanPowerOntology`** as a data source to **`AegeanPowerDataAgent`** (UI, 1 click)
#

# MARKDOWN ********************

# ## 1 · Discover workspace and items

# CELL ********************

import json, base64, time, requests, re
import notebookutils

GITHUB_REPO = "galex87/fabric-energy-rti-ontology"
GITHUB_BRANCH = "main"

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

def fab_lro(method, path, body=None, max_wait=240):
    r = fab(method, path, body, raise_on_error=False)
    if r.status_code in (200, 201):
        return r.json() if r.text else None
    if r.status_code != 202:
        raise RuntimeError(f"{method} {path} -> {r.status_code} {r.text[:500]}")
    loc = r.headers.get("Location")
    if not loc: return None
    tok = fab_token()
    waited = 0
    while waited < max_wait:
        time.sleep(3); waited += 3
        p = requests.get(loc, headers={"Authorization": f"Bearer {tok}"}, timeout=30)
        if p.status_code != 200: continue
        data = p.json()
        if data.get("status") == "Succeeded":
            res = requests.get(loc + "/result", headers={"Authorization": f"Bearer {tok}"}, timeout=30)
            if res.ok and res.text:
                return res.json()
            return data
        if data.get("status") == "Failed":
            raise RuntimeError(f"LRO failed: {json.dumps(data, indent=2)[:500]}")
    raise RuntimeError(f"LRO timeout after {max_wait}s")

items = fab("GET", f"/workspaces/{WS_ID}/items").json().get("value", [])
by_name = {(i["type"], i["displayName"]): i["id"] for i in items}

def find(t, name, required=True):
    iid = by_name.get((t, name))
    if iid:
        print(f"  found {t:18s} {name:35s} {iid}")
    elif required:
        raise RuntimeError(f"missing item: type={t} name={name}")
    else:
        print(f"  (skip) no {t}/{name}")
    return iid

LAKEHOUSE_ID = find("Lakehouse",   "AegeanPowerLH")
EH_ID        = find("Eventhouse",  "AegeanPowerEH")
ES_ID        = find("Eventstream", "AegeanPowerStream")
SIM_NB_ID    = find("Notebook",    "AegeanPower_Simulator")
DT_NB_ID     = find("Notebook",    "Demo_Trigger_Console")
DC_NB_ID     = find("Notebook",    "Dispatch_Maintenance_Crew")
LD_NB_ID     = find("Notebook",    "Load_CSVs_to_Delta")
DASH_ID      = find("KQLDashboard","AegeanPower_Live_Operations", required=False)
ONTO_ID      = find("Ontology",    "AegeanPowerOntology",         required=False)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 2 · KQL: schema + ingestion mappings + streaming policy

# CELL ********************

eh = fab("GET", f"/workspaces/{WS_ID}/eventhouses/{EH_ID}").json()
CLUSTER_URI = eh["properties"]["queryServiceUri"]
DB_NAME = "AegeanPowerEH"
print(f"Cluster: {CLUSTER_URI}")

def kql(csl, op="mgmt"):
    tok = notebookutils.credentials.getToken("https://kusto.kusto.windows.net")
    r = requests.post(f"{CLUSTER_URI}/v1/rest/{op}",
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                      json={"db": DB_NAME, "csl": csl}, timeout=60)
    r.raise_for_status()
    return r.json()

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
    print(f"  ok  {tbl}")
print("\nKQL setup complete.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 3 · Bind AegeanPowerLH as default lakehouse on the 4 notebooks

# CELL ********************

LAKEHOUSE_DEPENDENCY = {
    "lakehouse": {
        "default_lakehouse": LAKEHOUSE_ID,
        "default_lakehouse_name": "AegeanPowerLH",
        "default_lakehouse_workspace_id": WS_ID,
        "known_lakehouses": [{"id": LAKEHOUSE_ID}],
    }
}

def bind_lakehouse(nb_id, name):
    defn = fab_lro("POST", f"/workspaces/{WS_ID}/notebooks/{nb_id}/getDefinition?format=ipynb")
    parts = defn["definition"]["parts"]
    for p in parts:
        if p["path"].endswith(".ipynb"):
            raw = base64.b64decode(p["payload"]).decode("utf-8")
            nb = json.loads(raw)
            nb.setdefault("metadata", {})
            nb["metadata"]["dependencies"] = LAKEHOUSE_DEPENDENCY
            new = json.dumps(nb, separators=(",", ":"))
            p["payload"] = base64.b64encode(new.encode("utf-8")).decode("ascii")
            p["payloadType"] = "InlineBase64"
            break
    fab_lro("POST", f"/workspaces/{WS_ID}/notebooks/{nb_id}/updateDefinition",
            body={"definition": {"format": "ipynb", "parts": parts}})
    print(f"  ok  {name}")

for nb_id, name in [(SIM_NB_ID,"AegeanPower_Simulator"),
                    (DT_NB_ID,"Demo_Trigger_Console"),
                    (DC_NB_ID,"Dispatch_Maintenance_Crew"),
                    (LD_NB_ID,"Load_CSVs_to_Delta")]:
    bind_lakehouse(nb_id, name)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 4 · Patch simulator notebook with Eventstream connection string

# CELL ********************

topo = fab("GET", f"/workspaces/{WS_ID}/eventstreams/{ES_ID}/topology").json()
src = next(s for s in topo["sources"] if s["type"] == "CustomEndpoint")
SRC_ID = src["id"]
conn = fab("GET", f"/workspaces/{WS_ID}/eventstreams/{ES_ID}/sources/{SRC_ID}/connection").json()
PRIMARY = conn["accessKeys"]["primaryConnectionString"]
print(f"Connection string: {PRIMARY[:60]}...[REDACTED]")

defn = fab_lro("POST", f"/workspaces/{WS_ID}/notebooks/{SIM_NB_ID}/getDefinition?format=ipynb")
parts = defn["definition"]["parts"]
for p in parts:
    if p["path"].endswith(".ipynb"):
        raw = base64.b64decode(p["payload"]).decode("utf-8")
        nb = json.loads(raw)
        pattern = re.compile(r'EVENTHUB_CONNECTION_STRING\s*=\s*"[^"]*"')
        replacement = f'EVENTHUB_CONNECTION_STRING = "{PRIMARY}"'
        replaced = 0
        for c in nb.get("cells", []):
            if c.get("cell_type") != "code": continue
            new_src = []
            for line in c.get("source", []):
                if pattern.search(line):
                    line = pattern.sub(replacement, line); replaced += 1
                new_src.append(line)
            c["source"] = new_src
        if replaced == 0: raise RuntimeError("EVENTHUB_CONNECTION_STRING line not found")
        print(f"  patched {replaced} line(s)")
        new = json.dumps(nb, separators=(",", ":"))
        p["payload"] = base64.b64encode(new.encode("utf-8")).decode("ascii")
        break
fab_lro("POST", f"/workspaces/{WS_ID}/notebooks/{SIM_NB_ID}/updateDefinition",
        body={"definition": {"format": "ipynb", "parts": parts}})
print("ok simulator updated")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 5 · Rebind Real-Time Dashboard cluster URI

# CELL ********************

if not DASH_ID:
    print("  skip (no dashboard)")
else:
    defn = fab_lro("POST", f"/workspaces/{WS_ID}/kqlDashboards/{DASH_ID}/getDefinition")
    parts = defn["definition"]["parts"]
    for p in parts:
        if p["path"].endswith(".json") and "Dashboard" in p["path"]:
            raw = base64.b64decode(p["payload"]).decode("utf-8")
            dash = json.loads(raw)
            for ds in dash.get("dataSources", []):
                if ds.get("name") == "AegeanPowerEH":
                    ds["clusterUri"] = CLUSTER_URI; ds["database"] = DB_NAME
                    print(f"  ok  data source rebound")
            new = json.dumps(dash, separators=(",", ":"))
            p["payload"] = base64.b64encode(new.encode("utf-8")).decode("ascii")
            break
    fab_lro("POST", f"/workspaces/{WS_ID}/kqlDashboards/{DASH_ID}/updateDefinition",
            body={"definition": {"parts": parts}})
    print("ok dashboard updated")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 6 · Download seed CSVs from GitHub into Lakehouse Files/data/

# CELL ********************

ONELAKE = "https://onelake.dfs.fabric.microsoft.com"

def upload_to_lakehouse(blob_bytes, relative_path):
    tok = notebookutils.credentials.getToken("https://storage.azure.com")
    base = f"{ONELAKE}/{WS_ID}/{LAKEHOUSE_ID}/Files/{relative_path}"
    h = {"Authorization": f"Bearer {tok}", "x-ms-version": "2021-08-06"}
    r = requests.put(f"{base}?resource=file", headers=h, timeout=30)
    if r.status_code not in (200, 201): raise RuntimeError(f"create: {r.status_code} {r.text[:200]}")
    h2 = {**h, "Content-Type": "application/octet-stream", "Content-Length": str(len(blob_bytes))}
    r = requests.patch(f"{base}?action=append&position=0", data=blob_bytes, headers=h2, timeout=60)
    if r.status_code not in (200, 202): raise RuntimeError(f"append: {r.status_code} {r.text[:200]}")
    r = requests.patch(f"{base}?action=flush&position={len(blob_bytes)}", headers=h, timeout=30)
    if r.status_code not in (200, 201): raise RuntimeError(f"flush: {r.status_code} {r.text[:200]}")

CSV_FILES = ["power_plants.csv","wind_turbines.csv","solar_inverters.csv","substations.csv",
             "island_grids.csv","vessels.csv","maintenance_orders.csv","emissions_ledger.csv"]
for csv_file in CSV_FILES:
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/data/{csv_file}"
    r = requests.get(url, timeout=30); r.raise_for_status()
    upload_to_lakehouse(r.content, f"data/{csv_file}")
    print(f"  ok  Files/data/{csv_file}  ({len(r.content)} bytes)")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 7 · Load CSVs to Delta tables

# CELL ********************

ABFSS = f"abfss://{WS_ID}@onelake.dfs.fabric.microsoft.com/{LAKEHOUSE_ID}"
CSV_DIR = f"{ABFSS}/Files/data"
from pyspark.sql.functions import col

TABLE_DEFS = [
    ('power_plants.csv','power_plants', {'capacity_mw':'double','latitude':'double','longitude':'double','commissioning_year':'int'}),
    ('wind_turbines.csv','wind_turbines', {'capacity_mw':'double','hub_height_m':'double','rotor_diameter_m':'double','cut_in_speed_ms':'double','rated_speed_ms':'double','cut_out_speed_ms':'double','latitude':'double','longitude':'double'}),
    ('solar_inverters.csv','solar_inverters', {'capacity_kw':'double','panel_tilt_deg':'double','panel_azimuth_deg':'double','latitude':'double','longitude':'double'}),
    ('substations.csv','substations', {'voltage_kv':'double','latitude':'double','longitude':'double'}),
    ('island_grids.csv','island_grids', {'population':'int','peak_demand_mw':'double','installed_capacity_mw':'double','nominal_frequency_hz':'double','latitude':'double','longitude':'double'}),
    ('vessels.csv','vessels', {'capacity_m3':'double','current_cargo_m3':'double','speed_knots':'double'}),
    ('maintenance_orders.csv','maintenance_orders', {'cost_eur':'double'}),
    ('emissions_ledger.csv','emissions_ledger', {'co2_tonnes':'double','ets_allowance_tonnes':'double','fuel_consumed_mwh':'double','emission_factor_tco2_per_mwh':'double','compliance_pct':'double'}),
]
for csv_file, tbl, overrides in TABLE_DEFS:
    df = spark.read.option('header', True).option('inferSchema', True).csv(f"{CSV_DIR}/{csv_file}")
    for c, dtype in overrides.items():
        df = df.withColumn(c, col(c).cast(dtype))
    df.write.mode('overwrite').format('delta').save(f"{ABFSS}/Tables/{tbl}")
    print(f"  ok  {tbl} {df.count()} rows")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 8 · Rebind Ontology data bindings

# CELL ********************

if not ONTO_ID:
    print("  skip (no ontology)")
else:
    kdbs = fab("GET", f"/workspaces/{WS_ID}/kqlDatabases").json().get("value", [])
    KQL_DB_ID = next((k["id"] for k in kdbs if k["displayName"] == "AegeanPowerEH"), None)
    print(f"  KQL DB itemId: {KQL_DB_ID}")
    print(f"  Lakehouse itemId: {LAKEHOUSE_ID}")

    defn = fab_lro("POST", f"/workspaces/{WS_ID}/ontologies/{ONTO_ID}/getDefinition")
    parts = defn["definition"]["parts"]
    patched = 0
    for p in parts:
        if "DataBindings" in p["path"] and p["path"].endswith(".json"):
            raw = base64.b64decode(p["payload"]).decode("utf-8")
            b = json.loads(raw)
            src = b.get("dataBindingConfiguration", {}).get("sourceTableProperties", {})
            stype = src.get("sourceType")
            if stype == "LakehouseTable":
                src["workspaceId"] = WS_ID; src["itemId"] = LAKEHOUSE_ID
            elif stype == "KustoTable":
                src["workspaceId"] = WS_ID
                if KQL_DB_ID: src["itemId"] = KQL_DB_ID
                if "clusterUri" in src: src["clusterUri"] = CLUSTER_URI
                if "database" in src: src["database"] = DB_NAME
            new = json.dumps(b, separators=(",", ":"))
            p["payload"] = base64.b64encode(new.encode("utf-8")).decode("ascii")
            patched += 1
            print(f"  ok  {stype} -> {src.get('sourceTableName')}")
    if patched:
        fab_lro("POST", f"/workspaces/{WS_ID}/ontologies/{ONTO_ID}/updateDefinition",
                body={"definition": {"parts": parts}})
        print(f"\nok ontology updated ({patched} bindings)")
        print("   (this also triggers graph ingestion — same as clicking Save in the editor)")

        # The graph ingestion runs on a separate auto-created Graph item
        # (item type "GraphModel" or similar). Find it by type.
        import time as _t
        print("\nWaiting for graph ingestion to complete...")
        graph_item = None
        deadline = _t.time() + 600
        last_status = None
        while _t.time() < deadline:
            try:
                if graph_item is None:
                    all_items = fab("GET", f"/workspaces/{WS_ID}/items").json().get("value", [])
                    # Prefer items whose type mentions "graph" (Graph, GraphModel, etc.)
                    candidates = [i for i in all_items if "graph" in (i.get("type","").lower())]
                    if not candidates:
                        # Fallback: items whose name references the ontology
                        candidates = [i for i in all_items if "ontology" in i.get("displayName","").lower() and i.get("id") != ONTO_ID]
                    if candidates:
                        graph_item = candidates[0]
                        print(f"  found graph item: {graph_item['displayName']}  type={graph_item.get('type')}  id={graph_item['id']}")
                    else:
                        print("  (no Graph item yet, waiting...)"); _t.sleep(5); continue

                jobs = fab("GET",
                    f"/workspaces/{WS_ID}/items/{graph_item['id']}/jobs/instances?$top=5",
                    raise_on_error=False)
                if not jobs.ok:
                    print(f"  poll error: HTTP {jobs.status_code} {jobs.text[:120]}")
                    _t.sleep(10); continue
                arr = jobs.json().get("value", [])
                arr.sort(key=lambda j: j.get("startTimeUtc",""), reverse=True)
                if not arr:
                    print("  no job yet, waiting..."); _t.sleep(5); continue
                j = arr[0]
                status = j.get("status","?")
                jtype  = j.get("jobType","?")
                if status != last_status:
                    print(f"  [{jtype}] status={status}")
                    last_status = status
                if status in ("Completed", "Succeeded"):
                    print(f"\nok graph ingestion finished ({jtype})")
                    break
                if status in ("Failed", "Cancelled"):
                    print(f"\n!! graph ingestion {status}: {j.get('failureReason',{}).get('message','')}")
                    break
                _t.sleep(5)
            except Exception as e:
                print(f"  poll exception: {e}"); _t.sleep(10)
        else:
            print("\n!! timed out waiting for graph ingestion (still running in background)")
    else:
        print("  no DataBindings parts found")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## DONE
#
# What's left to do manually:
# 1. Open **AegeanPowerStream** -> Edit -> Publish (1 click, top toolbar).
# 2. Open **AegeanPower_Simulator** -> Run all (starts live data flow).
# 3. Open **AegeanPowerDataAgent** -> + Data source -> Ontology -> pick AegeanPowerOntology -> Publish.
#
# Then run the demo from docs/DEMO_SCRIPT.md.
#
