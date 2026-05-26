# Data source instructions (paste into Fabric UI)

The agent-level `aiInstructions` (in `stage_config.json`) is intentionally short per Microsoft best practices §7-§8. The **detailed schema / join / example-query guidance goes on each datasource**, in the Fabric UI:

> Data Agent → Settings → Data sources → \[datasource\] → **Instructions** field.

Paste the blocks below into the matching datasource. Then **Publish**.

---

## 1. `AegeanPowerOntology` (Ontology — primary)

```
## General instructions
This ontology models AegeanPower's portfolio as a graph. Use it for any question about plants, turbines, inverters, grids, vessels, substations, maintenance orders, or emissions records.

## Entities and primary keys
- PowerPlant.plant_id        (e.g. PP-NAX-01)
- WindTurbine.turbine_id     (e.g. WT-NAX-03)        belongs_to_plant -> PowerPlant
- SolarInverter.inverter_id  (e.g. SI-CRE-02)        belongs_to_plant -> PowerPlant
- IslandGrid.grid_id         (e.g. GR-NAX)           connects PowerPlant via plant.grid_id
- Vessel.vessel_id           (e.g. VE-LNG-01)        supply_plant_id -> PowerPlant
- Substation.substation_id   (e.g. SUB-NAX-01)       fed_by_plant_id -> PowerPlant
- MaintenanceOrder.order_id  (e.g. MO-2026-007)      asset_id -> WindTurbine | SolarInverter ; plant_id -> PowerPlant
- EmissionsRecord.record_id                          plant_id -> PowerPlant ; period STRING "YYYY-MM"

## Always include in responses (when available)
- For plants: plant_id, plant_name, plant_type, fuel_type, capacity_mw, region, prefecture, grid_id
- For turbines: turbine_id, turbine_name, plant_id, manufacturer, model, capacity_mw, status
- For inverters: inverter_id, inverter_name, plant_id, manufacturer, panel_type, capacity_kw
- For maintenance orders: order_id, asset_id, plant_id, priority, status, technician, description, created_date
- For vessels: vessel_id, vessel_name, vessel_type, status, destination, supply_plant_id, speed_knots
- For emissions: plant_id, period, co2_tonnes, ets_allowance_tonnes, compliance_status

## Value formats (the agent cannot see row values — these examples are required)
- plant_type: "Wind Farm", "Solar Park", "Gas Power Plant"        (exact case)
- fuel_type: "Wind", "Solar", "Natural Gas"
- status (entities): "Active"
- maintenance priority: "Critical", "High", "Medium", "Low"
- maintenance status: "Open", "Scheduled", "In Progress", "Completed"
- vessel status (live): "Sailing", "Loading", "Docked", "EnRoute", "Dispatched"
- emissions period: STRING "YYYY-MM"   (e.g. "2026-03") — NOT a datetime
- region: "Eastern Macedonia and Thrace", "South Aegean", "Thessaly", "Crete", "Attica", "Peloponnese"
- prefecture: "Evros", "Cyclades", "Larissa", "Heraklion", "East Attica", "Arcadia"

## Join logic
- Turbines/inverters to plant: via belongs_to_plant edge (or plant_id FK).
- Vessels to plant they supply: Vessel.supply_plant_id = PowerPlant.plant_id.
- Substations to plant they feed: Substation.fed_by_plant_id = PowerPlant.plant_id.
- Maintenance orders to asset: MaintenanceOrder.asset_id = WindTurbine.turbine_id OR SolarInverter.inverter_id (use asset_type to disambiguate).
- Emissions to plant: EmissionsRecord.plant_id = PowerPlant.plant_id.

## When asked about

### Wind turbines grouped by plant
Traverse PowerPlant -[has_turbine]-> WindTurbine. Return turbine_id, turbine_name, manufacturer, capacity_mw, grouped by plant_name. Filter `PowerPlant.plant_type = "Wind Farm"`.

### Plants in the Cyclades
Filter `PowerPlant.prefecture = "Cyclades"` (NOT region). Return plant_id, plant_name, plant_type, fuel_type, capacity_mw, grid_id.

### Wind turbines per manufacturer (count)
GROUP BY WindTurbine.manufacturer, COUNT(*). Sort descending.

### Emissions for natural-gas plants in a given month
JOIN EmissionsRecord -> PowerPlant where `plant_type = "Gas Power Plant"` AND `period = "YYYY-MM"`. Return plant_name, period, co2_tonnes, ets_allowance_tonnes, compliance_status.

### Critical open maintenance orders on turbines
Filter `MaintenanceOrder.priority = "Critical"` AND `status IN ("Open","Scheduled","In Progress")` AND `asset_type = "WindTurbine"`. Join to WindTurbine for turbine_name and to PowerPlant for plant_name. Return order_id, turbine_name, plant_name, technician, description.

### Vessels dispatched or en route
Filter `Vessel.status IN ("Dispatched","EnRoute","Sailing")`. Join to PowerPlant via supply_plant_id. Return vessel_name, vessel_type, status, destination, plant_name.

### Substations with the plant they feed
JOIN Substation -> PowerPlant via fed_by_plant_id. Return substation_id, voltage_kv, substation_type, grid_id, plant_name.

### Solar inverters at a specific plant
Filter `SolarInverter.plant_id = "PP-CRE-01"` (Crete Solar Park). Return inverter_id, manufacturer, panel_type, capacity_kw.

### Installed capacity: renewables vs gas
SUM(PowerPlant.capacity_mw) GROUP BY (plant_type IN ("Wind Farm","Solar Park") ? "Renewable" : "Gas").

### "Right now" / "live" / "current" output
Use the timeseriesProperties on the entity (power_mw / power_kw / generation_mw / frequency_hz / etc.) — they resolve to the latest KQL reading automatically.
```

---

## 2. `AegeanPowerKQL` (Eventhouse — live telemetry)

```
## General instructions
Use this Eventhouse only when the question explicitly requires aggregation or time-window analysis over live telemetry that the ontology cannot express. For single-entity "what is happening right now" the ontology timeseriesProperties already cover it.

## Tables and key columns
- WindTurbineEvents    : Timestamp, turbine_id, plant_id, power_mw, wind_speed_ms, vibration_mm_s, rotor_rpm, nacelle_temp_c, fault_type, latitude, longitude
- SolarInverterEvents  : Timestamp, inverter_id, plant_id, power_kw, irradiance_wm2, panel_temp_c, efficiency_pct, fault_type
- GridEvents           : Timestamp, grid_id, frequency_hz, load_mw, generation_mw, voltage_kv, balance_mw
- VesselPositions      : Timestamp, vessel_id, latitude, longitude, heading_deg, eta_hours, speed_knots, destination, cargo_status (-> status)
- EmissionsStream      : Timestamp, plant_id, power_output_mw, co2_kg_per_hour, cumulative_co2_tonnes_today, compliance_pct

## Required patterns
- ALWAYS include a time filter:                where Timestamp > ago(2m)
- For "latest per entity":                     summarize arg_max(Timestamp, *) by turbine_id
- Prefer `has` over `contains` on indexed string columns.

## Leading-word example queries

### Q: What is the current total wind generation?
```
WindTurbineEvents
| where Timestamp > ago(2m)
| summarize arg_max(Timestamp, power_mw) by turbine_id
| summarize total_mw = sum(power_mw)
```

### Q: Which grids deviate from 50 Hz by more than 0.3 Hz right now?
```
GridEvents
| where Timestamp > ago(2m)
| summarize arg_max(Timestamp, *) by grid_id
| where abs(frequency_hz - 50) > 0.3
| project grid_id, frequency_hz, load_mw, generation_mw
```

### Q: Latest vessel positions for vessels en route
```
VesselPositions
| where Timestamp > ago(5m)
| summarize arg_max(Timestamp, *) by vessel_id
| where cargo_status in ("EnRoute","Dispatched","Sailing")
| project vessel_id, latitude, longitude, speed_knots, destination, eta_hours
```
```

---

## 3. `AegeanPowerLH` (Lakehouse SQL endpoint — fallback)

```
## General instructions
Only used when the ontology cannot express the query. Static metadata only — never use for "current" / "live" / "right now" questions.

## Tables
- power_plants, wind_turbines, solar_inverters, island_grids, vessels, substations, maintenance_orders, emissions_records

## Example queries

### Q: Plants in the Cyclades with grid info
```
SELECT p.plant_id, p.plant_name, p.plant_type, p.fuel_type, p.capacity_mw, p.grid_id, g.island
FROM power_plants p
LEFT JOIN island_grids g ON g.grid_id = p.grid_id
WHERE p.prefecture = 'Cyclades'
```

### Q: Renewables vs gas installed capacity
```
SELECT
  CASE WHEN plant_type IN ('Wind Farm','Solar Park') THEN 'Renewable' ELSE 'Gas' END AS category,
  SUM(capacity_mw) AS total_capacity_mw
FROM power_plants
GROUP BY 1
```
```

---

## Why this split

Per Microsoft best practices (https://learn.microsoft.com/en-us/fabric/data-science/data-agent-configuration-best-practices):

- §7-§8 — agent instructions stay **short, role/tone/routing only**.
- §9 — each datasource carries its **own** schema, join logic, value formats.
- §10 — example queries are the **highest-leverage** knob (top-3 vector-matched into every prompt).
- §6 — use leading-word fragments (`LIKE '%...%'`, `where Timestamp > ago(...)`) so the model knows the target syntax.

After pasting the three blocks above, click **Publish** and re-run `Test_Demo_Prompts.Notebook`.
