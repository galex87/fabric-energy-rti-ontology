# Demo Prompts — AegeanPowerDataAgent

Prompts to send to **`AegeanPowerDataAgent`**. The agent is grounded in `AegeanPowerOntology` over the clean `AegeanPowerLH` Delta tables.

> **Demo split.** The Data Agent answers **structured / multi-entity questions** against the ontology (Lakehouse). The **live "wow" moments** (real-time vessel positions, turbine telemetry, forced-failure cascade) are shown on the **Real-Time Dashboard** which reads KQL directly. Don't ask the Data Agent for live streaming numbers — use the dashboard for those.

---

## The ten demo prompts (use these)

These ten play to the ontology's strengths: single-entity listings, categorical filters, foreign-key joins, and grouped counts/sums. They avoid the known limitation of mixing aggregation across `properties` and `timeseriesProperties` in a single query.

1. **List all wind turbines grouped by plant, with manufacturer and capacity.**
2. **Show all power plants in the Cyclades prefecture, with type, fuel, capacity and grid.**
3. **How many wind turbines do we have per manufacturer?**
4. **Show CO₂ emissions for our natural-gas plants in March 2026, with ETS allowances and compliance status.**
5. **Which wind turbines currently have a Critical open maintenance order? Include turbine, plant, technician and description.**
6. **List vessels that are dispatched or en route, with destination and the plant they supply.**
7. **Show all substations with voltage, grid and the plant they feed.**
8. **List the solar inverters at Crete Solar Park with manufacturer, panel type and capacity.**
9. **Compare total installed capacity of renewable plants (wind + solar) vs natural-gas plants.**
10. **Naxos Wind Farm: show every turbine and any open maintenance orders against them.** *(mic-drop multi-entity)*

---

## Why these ten work

- **#1, #3, #7, #8** — single-entity listings with FK joins. Reliable.
- **#2** — exercises the geography mapping (Cyclades is a prefecture, not a region; agent instructions hard-code the plant→prefecture table).
- **#4** — categorical filter on `plant_type = "GasPlant"` joined to monthly `emissions` by the `period` string (`YYYY-MM`).
- **#5, #10** — join `maintenance_orders` (status `Open`, priority `Critical`) to turbines and plants.
- **#6** — vessel status enum (`Dispatched`, `EnRoute`) joined via `supply_plant_id`.
- **#9** — grouped sum over a static categorical column.

---

## What NOT to ask the Data Agent

Use the **Real-Time Dashboard** for these:

- Current power output of turbines / inverters
- Live vessel ETA or position
- Real-time grid frequency / load
- Any aggregation that mixes streaming time-series columns with entity properties (known engine limitation)

---

## Running the prompts

Open `Test_Demo_Prompts.Notebook` in the Fabric workspace and **Run all**. It iterates over the ten prompts above using `fabric.dataagent.client.FabricOpenAI` and prints each answer.

> The SDK depends on `synapse.ml.fabric` and only runs inside the Fabric runtime — it cannot execute from a local Python install. Programmatic testing must be done from within Fabric.
