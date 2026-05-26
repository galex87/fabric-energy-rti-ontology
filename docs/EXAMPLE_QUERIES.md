# Example queries (paste into Fabric UI, not into agent instructions)

These GQL templates are intentionally **outside** `aiInstructions` so the audience never sees them in the agent config.

Where to paste them: Data Agent → Settings → Data sources → `AegeanPowerOntology` → **Example queries** field (one per row). The agent retrieves the top-3 by vector similarity per user question; the audience never sees this surface.

> Currently the Example queries field is UI-only — it does not round-trip through git sync.

---

## 1. Critical open maintenance orders on turbines (avoid fan-out)

```
MATCH (mo:`MaintenanceOrder`), (wt:`WindTurbine`)
WHERE mo.`priority` = "Critical"
  AND mo.`status` IN ("Open","Scheduled","In Progress")
  AND mo.`asset_type` = "WindTurbine"
  AND mo.`asset_id` = wt.`turbine_id`
OPTIONAL MATCH (wt)-[:`belongs_to_plant`]->(pp:`PowerPlant`)
RETURN mo.`order_id`, wt.`turbine_id`, wt.`turbine_name`, pp.`plant_name`, mo.`technician`, mo.`description`
```

## 2. Emissions for natural-gas plants in a given month

```
MATCH (e:`EmissionsRecord`)
WHERE e.`period` = "2026-03"
RETURN e.`plant_id`, e.`plant_name`, e.`period`, e.`co2_tonnes`, e.`ets_allowance_tonnes`, e.`compliance_pct`, e.`compliance_status`
```

## 3. Vessels dispatched / en route with destination + plant they supply

```
MATCH (v:`Vessel`)-[:`supplies_plant`]->(p:`PowerPlant`)
WHERE v.`status` IN ("Dispatched","En Route","Sailing","Loading")
RETURN v.`vessel_id`, v.`vessel_name`, v.`vessel_type`, v.`status`, v.`destination`, v.`speed_knots`, p.`plant_name`
```

## 4. Plants under simultaneous stress (critical MO AND vessel dispatched)

```
MATCH (mo:`MaintenanceOrder`)
WHERE mo.`priority` = "Critical" AND mo.`status` IN ("Open","Scheduled","In Progress")
MATCH (v:`Vessel`)-[:`supplies_plant`]->(p:`PowerPlant`)
WHERE v.`status` IN ("Dispatched","En Route","Sailing")
  AND p.`plant_id` = mo.`plant_id`
RETURN p.`plant_name`, p.`plant_type`, mo.`order_id`, mo.`description`, v.`vessel_name`, v.`destination`, v.`speed_knots`
```

## 5. Naxos cross-cut (the mic-drop)

```
MATCH (p:`PowerPlant`) WHERE p.`plant_id` = "PP-NAX-01"
OPTIONAL MATCH (wt:`WindTurbine`)-[:`belongs_to_plant`]->(p)
OPTIONAL MATCH (s:`Substation`)-[:`fed_by_plant`]->(p)
OPTIONAL MATCH (v:`Vessel`)-[:`supplies_plant`]->(p)
OPTIONAL MATCH (mo:`MaintenanceOrder`) WHERE mo.`plant_id` = p.`plant_id` AND mo.`status` != "Completed"
RETURN p, wt, s, v, mo
```

## 6. Technician workload

```
MATCH (mo:`MaintenanceOrder`)
WHERE mo.`status` IN ("Open","Scheduled","In Progress")
RETURN mo.`technician`, count(mo) AS open_orders, collect(mo.`order_id`) AS order_ids
```

## 7. Cyclades plants with open MO posture

```
MATCH (p:`PowerPlant`) WHERE p.`prefecture` = "Cyclades"
OPTIONAL MATCH (mo:`MaintenanceOrder`) WHERE mo.`plant_id` = p.`plant_id` AND mo.`status` != "Completed"
RETURN p.`plant_name`, p.`plant_type`, p.`capacity_mw`, count(mo) AS open_mo_count, collect(mo.`priority`) AS priorities
```

## 8. Fleet master list

```
MATCH (wt:`WindTurbine`)-[:`belongs_to_plant`]->(p:`PowerPlant`)
RETURN "WindTurbine" AS kind, wt.`turbine_id` AS asset_id, wt.`turbine_name` AS asset_name, p.`plant_name`, p.`prefecture`, p.`grid_id`, wt.`capacity_mw`
UNION
MATCH (si:`SolarInverter`)-[:`belongs_to_plant`]->(p:`PowerPlant`)
RETURN "SolarInverter" AS kind, si.`inverter_id` AS asset_id, si.`inverter_name` AS asset_name, p.`plant_name`, p.`prefecture`, p.`grid_id`, si.`capacity_kw`/1000.0
```

## 9. Plants grouped by grid with total capacity

```
MATCH (p:`PowerPlant`)
RETURN p.`grid_id`, count(p) AS plant_count, sum(p.`capacity_mw`) AS total_capacity_mw
```

## 10. Substations with the plant they feed

```
MATCH (s:`Substation`)-[:`fed_by_plant`]->(p:`PowerPlant`)
RETURN s.`substation_id`, s.`voltage_kv`, s.`substation_type`, s.`connected_grid_id`, p.`plant_name`
```
