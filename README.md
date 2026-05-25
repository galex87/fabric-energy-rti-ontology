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
                      │  AegeanPowerStream2     │  Eventstream (5 filters)
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

> Prereqs: Fabric capacity (F2+ or P SKU). Trial may not support Git integration in all regions. Contributor or higher on a workspace.

### 1 · Fork this repo

Click **Fork** (top-right on GitHub) → owner = your account → **untick** "Copy main branch only" → **Create fork**.

You now own `https://github.com/<you>/fabric-energy-rti-ontology` with branches `main` and `EnergyDemo`.

### 2 · Create an empty Fabric workspace

Fabric portal → **Workspaces** → **+ New** → assign your capacity. Name it whatever you like (e.g. `Energy-Demo-<you>`).

### 3 · Connect your workspace to your fork

In the workspace: **Workspace settings → Git integration → Connect**:

- Provider: **GitHub**
- Authorize (PAT with `Contents: read/write` on your fork)
- Repository URL: `https://github.com/<you>/fabric-energy-rti-ontology`
- Branch: **`EnergyDemo`**
- Git folder: *(blank)*
- **Connect and sync** → **Update all**

Fabric pulls every item into your workspace.

### 4 · Upload seed data to the Lakehouse

1. Open **`AegeanPowerLH`** in the workspace.
2. **Files** → **Upload** → **Upload folder** → select your local clone's `data/` folder.
3. Confirm `Files/data/*.csv` shows 8 files.

### 5 · Load CSVs to Delta tables

Open **`Load_CSVs_to_Delta`** notebook → **Run all**.

You should now see 8 Delta tables under `Tables/`:
`power_plants`, `wind_turbines`, `solar_inverters`, `maintenance_orders`, `vessels`, `substations`, `emissions_ledger`, `island_grids`.

### 6 · Wire the Eventstream

The Eventstream `AegeanPowerStream2` synced with destinations pointing to the **original** workspace's Eventhouse GUID. You need to re-bind:

1. Open **`AegeanPowerStream2`** → **Edit**.
2. For each of the 5 destinations (`destwindturbinetelemetry`, `destsolarinvertertelemetry`, `destgridtelemetry`, `destvesselpositions`, `destemissionsstream`):
   - Click the destination → **Edit** → set Eventhouse to *your* `AegeanPowerEH` → table = matching name → save.
3. Click **Publish**.
4. Click the **CustomApp source** → **Sample code** tab → copy the **primary connection string**.

### 7 · Paste the connection string into the simulator

Open **`AegeanPower_Simulator`** notebook → find this line (around line 100):

```python
EVENTHUB_CONNECTION_STRING = "REPLACE_ME_WITH_EVENTSTREAM_CUSTOM_ENDPOINT_CONNECTION_STRING"
```

Replace the placeholder with the connection string from step 6.

### 8 · Run the simulator

**`AegeanPower_Simulator`** → **Run all**. After ~30 s, verify data is flowing in a KQL query window:

```kql
WindTurbineTelemetry | where timestamp > ago(2m) | summarize n=count()
```

Expect `n > 0`.

### 9 · Re-bind the Activator

Open **`WT-Failures-Activator`** → **WT-Failures-Rule**:

- **Event stream**: confirm it points to *your* `AegeanPowerStream2 → derivedwindturbinetelemetry`.
- **Action → Run Notebook**: re-pick *your* `Dispatch_Maintenance_Crew` notebook.
- **Parameters**: ensure `turbine_id` maps to the event's `turbine_id`.
- **Save** → **Start**.

### 10 · Add data sources to the Data Agent

Open **`AegeanPowerDataAgent`** → **+ Data source**:
- Type: **Lakehouse** → **AegeanPowerLH** → tick all 8 tables.
- (Optional) Add KQL DB source → **AegeanPowerEH** → tick all 5 tables.

Click **Publish**.

### 11 · Open the dashboard

Open **`AegeanPower_Live_Operations`**. If tiles are empty, click each query → re-bind data source to your `AegeanPowerEH` → **Save**.

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
