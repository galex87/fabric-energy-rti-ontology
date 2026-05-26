# Fabric Energy RTI + Ontology Demo

End-to-end Microsoft Fabric demo for the energy sector: **Real-Time Intelligence** + **Ontology-driven Data Agents**.

A fictional Greek energy company — **Aegean Power S.A.** — operates wind farms, solar parks, gas plants, an island grid, and a logistics fleet. This demo shows how Microsoft Fabric ties operational telemetry, business data, and AI agents into a single closed-loop story.

---

## What's in the demo

```
                         ┌──────────────────────┐
                         │  AegeanPower_Simulator│  (notebook → Event Hub)
                         └──────────┬───────────┘
                                    │
                                    ▼
                      ┌─────────────────────────┐
                      │  AegeanPowerStream     │  Eventstream (5 filters)
                      └─────────────┬───────────┘
                                    │
              ┌────────┬────────┬───┴────┬────────┬─────────┐
              ▼        ▼        ▼        ▼        ▼         │
            Wind    Solar    Grid    Vessel   Emissions     │
              │        │        │        │        │         │
              ▼        ▼        ▼        ▼        ▼         │
           ┌────────────────────────────────────────┐       │
           │           AegeanPowerEH (KQL DB)       │◀──────┘
           └────────────┬───────────────────────────┘
                        │
        ┌───────────────┼────────────────────┐
        ▼               ▼                    ▼
  Real-Time      WT-Failures-Activator   AnomalyDetector
  Dashboard         │                    (ML model)
                    ▼
            Dispatch_Maintenance_Crew (notebook)
                    │
                    ▼
            Vessel routing change in simulator
```

Plus the **Ontology + Data Agent** side:

```
   ┌───────────────────┐      ┌──────────────────────┐
   │  AegeanPowerLH    │◀────│  AegeanPowerOntology │
   │  (Delta tables)   │      └──────────────────────┘
   └────────┬──────────┘                │
            │                           ▼
            │              ┌──────────────────────┐
            └─────────────▶│  AegeanPowerDataAgent │   (NL → answers)
                           └──────────────────────┘
```

---

## Repo layout

| Folder | What it is |
|---|---|
| `*.Notebook/`, `*.Lakehouse/`, `*.Eventhouse/`, … | Fabric items in Git format. Sync to your workspace via **Update all**. |
| `data/` | 8 seed CSVs for the Lakehouse (power plants, wind turbines, solar inverters, vessels, etc.). |
| `docs/` | Demo script, prompts, troubleshooting. |

---

## Quickstart

### 0 · Prerequisites

**Personal:**
- Fabric capacity (F2+ or P SKU). Trial may not support Git integration in all regions.
- **Contributor** or higher on the workspace you create.
- A GitHub account.

**Tenant admin settings** — make sure your Fabric admin has enabled the tenant settings required for:

- **Git integration** — to sync the workspace with this GitHub repo
- **Fabric Data Agent** — see [Configure Fabric data agent tenant settings](https://learn.microsoft.com/en-us/fabric/data-science/data-agent-tenant-settings)
- **Ontology + Graph** — see [Required tenant settings for ontology](https://learn.microsoft.com/en-us/fabric/iq/ontology/overview-tenant-settings)
- **Anomaly Detector (preview)** — see [Anomaly detection in Real-Time Intelligence](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/anomaly-detection?tabs=eventhouse).

Settings can take up to one hour to take effect after the admin toggles them.

---

### 1 · Fork this repo

Click **Fork** (top-right on GitHub) → owner = your account → **Create fork**.

You now own `https://github.com/<you>/fabric-energy-rti-ontology` with the `main` branch.

### 2 · Create an empty Fabric workspace

Fabric portal → **Workspaces** → **+ New** → assign your capacity. Name it whatever you like (e.g. `Energy-Demo-<you>`).

### 3 · Connect your workspace to your fork

In the workspace: **Workspace settings → Git integration → Connect**:

- Provider: **GitHub**
- Authorize (PAT with `Contents: read/write` on your fork)
- Repository URL: `https://github.com/<you>/fabric-energy-rti-ontology`
- Branch: **`main`**
- Git folder: *(blank)*
- **Connect and sync** → **Update all**

Fabric pulls every item into your workspace.

### 4 · Run the one-shot setup notebook

Open **`01_Post_Sync_Setup`** → **Run all**.

This notebook auto-configures everything that doesn't survive Git sync:

- Creates JSON ingestion mappings + enables streaming ingestion on the 5 KQL tables
- Binds `AegeanPowerLH` as the default Lakehouse on the 4 working notebooks
- Pulls the Eventstream connection string and patches `AegeanPower_Simulator`
- Rebinds the Real-Time Dashboard cluster URI to your local Eventhouse

It's idempotent — safe to re-run.

### 5 · Publish the Eventstream

Open **`AegeanPowerStream`** → **Edit** → **Publish** in the top toolbar. Destinations already point to your local Eventhouse (Git auto-remapped them) and the ingestion mappings created in step 4 are now active.

> If a destination shows "Add a mapper…", step 4 didn't run cleanly — rerun `01_Post_Sync_Setup` and republish.

### 6 · Upload seed data to the Lakehouse

1. Open **`AegeanPowerLH`** in the workspace.
2. **Files** → **Upload** → **Upload folder** → select your local clone's `data/` folder.
3. Confirm `Files/data/*.csv` shows 8 files.

### 7 · Load CSVs to Delta tables

Open **`Load_CSVs_to_Delta`** notebook → **Run all**.

You should now see 8 Delta tables under `Tables/`:
`power_plants`, `wind_turbines`, `solar_inverters`, `maintenance_orders`, `vessels`, `substations`, `emissions_ledger`, `island_grids`.

### 8 · Run the simulator

Open **`AegeanPower_Simulator`** → **Run all**. The connection string was already injected in step 4. After ~30 s, verify data is flowing in a KQL query window:

```kql
WindTurbineTelemetry | where timestamp > ago(2m) | summarize n=count(), nonzero=countif(power_mw > 0)
```

Expect `n > 0` and `nonzero > 0`.

### 9 · Open the Real-Time Dashboard

Open **`AegeanPower_Live_Operations`**. Tiles populate within ~30 s. The dashboard's cluster URI was already rebound in step 4 — no manual rebind needed.

> If tiles still show `0` / `NaN`: open the right-side **Data sources** panel → **⚙️** next to `AegeanPowerEH` → verify the cluster URI matches your Eventhouse → re-save.

### 10 · Re-bind Ontology data bindings *(manual — UI only)*

The Ontology's entity data bindings can't be auto-rebound via REST (yet). Open **`AegeanPowerOntology`** → for each entity (PowerPlant, WindTurbine, SolarInverter, IslandGrid, Vessel, MaintenanceOrder, Substation, EmissionsRecord):

- Click the entity → **Data bindings** tab
- Re-pick the source: your `AegeanPowerEH` (KQL DB) or `AegeanPowerLH` (Lakehouse) → matching table
- **Save**

### 11 · Add data sources to the Data Agent *(manual — UI only)*

Open **`AegeanPowerDataAgent`** → **+ Data source**:
- Type: **Ontology** → **AegeanPowerOntology** (recommended — gives the agent semantic context)
- *Or* Type: **Lakehouse** → **AegeanPowerLH** → tick all 8 tables
- *Optional:* KQL DB source → **AegeanPowerEH** → tick all 5 tables

Click **Publish**.

### 12 · You're ready

Walk through [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md). Try a prompt from [docs/PROMPTS.md](docs/PROMPTS.md). Trigger a failure from `Demo_Trigger_Console`.

---

## Demo highlights

- **Real-time pipeline**: 51 entities emit ~17 events/s through Eventstream → Eventhouse → Dashboard.
- **Autonomous remediation**: Activator detects a turbine fault → triggers a notebook → a vessel re-routes on the live map.
- **Ontology-aware AI**: Data Agent answers business questions (Cyclades wind output? Open maintenance + vessel intersection?) grounded in a clean semantic model.

---

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for the most common gotchas (Activator state, eventstream schema, empty `fault_type`, etc.).

---

## License

MIT — see [LICENSE](LICENSE).
