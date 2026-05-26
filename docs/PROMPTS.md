# Demo Prompts — AegeanPowerDataAgent

The Data Agent is grounded on **AegeanPowerOntology**, a graph over the Lakehouse + KQL Eventhouse. The impressive prompts below traverse multiple entities at once — the kind of question only an ontology over RTI can answer cleanly.

> **Demo split**: Use the **Data Agent** for cross-entity reasoning. Use the **Real-Time Dashboard** for second-by-second numbers, the live map, and the forced-failure cascade.

---

## The wow flight (run in this order)

### 1. Open with scope-setting
> *"How many wind turbines do we have per manufacturer?"*

Warmup. One line, clean grouping. Sets the agent's credibility.

### 2. Geography that beats keyword search
> *"Show all power plants in the Cyclades prefecture, with type, fuel, capacity and grid."*

Cyclades is a **prefecture**, not a region. The agent gets it right because the ontology + instructions encode Greek administrative geography.

### 3. The first multi-entity traversal
> *"List vessels that are dispatched or en route, with their destination and the plant they supply."*

Joins Vessel → PowerPlant via the `supplies_plant` edge. **`destination` is live from KQL** — the ontology resolves it inline. (Show the dashboard map at the same time for the wow.)

### 4. Cross-cutting risk view (the first mic-drop)
> *"Which plants have both an open critical maintenance order AND a vessel currently dispatched to supply them?"*

This is the ontology earning its keep: MaintenanceOrder × Vessel × PowerPlant joined in one question. No SQL human writes this fast.

### 5. Naxos master view (the bigger mic-drop)
> *"Naxos Wind Farm: show every turbine, the grid it sits on, the substation feeding it, any vessels supplying it, and any open maintenance orders against its turbines."*

Five entity types joined around one plant. This is the answer no dashboard tile can give you.

### 6. ETS / carbon angle
> *"Show CO₂ emissions for our natural-gas plants in March 2026, with ETS allowances and compliance status."*

EmissionsRecord has 2 rows for 2026-03 (Lavrio, Megalopoli). Demonstrates the agent handles a `period` STRING ("YYYY-MM") correctly.

### 7. Technician workload
> *"Who has the most open maintenance orders right now, and which ones are they?"*

GROUP BY technician, collect order IDs. A people-centric question over the same data.

### 8. Capacity comparison (no live data)
> *"Compare total installed capacity of renewable plants (wind + solar) vs natural-gas plants."*

Two-aggregate pattern — gas plants almost double renewables on paper. Sets up the next prompt's punchline.

### 9. The live counterpoint
> *"Give me a live snapshot: which turbines are below 30% of their nameplate capacity right now, and which plants do they belong to?"*

Compares timeseries `power_mw` against static `capacity_mw`. Punchline: at any moment renewables are bottlenecked by wind/sun while the gas plants are running closer to nameplate.

### 10. Closer — the cross-cut master list
> *"Give me a fleet master list: every turbine and inverter with its plant name, prefecture, grid, and capacity."*

42-row table that ties the entire ontology together. Hand-off line: *"This is what an AI agent over an ontology over real-time data buys you — every relationship, queryable in English."*

---

## Backup prompts (if a primary fails live)

- *"Show all substations with voltage, the grid they belong to, and the plant they feed."*
- *"List the solar inverters at Crete Solar Park with manufacturer, panel type and capacity."*
- *"List all wind turbines grouped by plant, with manufacturer and capacity."*
- *"For each gas plant, total YTD CO₂ emissions through April 2026."*

---

## What NOT to ask the Data Agent

These hit ontology-engine limits — use the **Real-Time Dashboard** instead:

- Aggregations over time windows on streaming columns (e.g. "average power over the last 5 minutes").
- Conditional `CASE WHEN` GROUP BY in a single question.
- Filtering on a `timeseriesProperty` (e.g. `WHERE destination = "Naxos"`). You can RETURN them; you cannot filter on them in GQL.

---

## Running the test harness

`Test_Demo_Prompts.Notebook` in the Fabric workspace iterates over the 10 prompts above and prints each answer. **Run all** before every demo so you know which prompts are warm.
