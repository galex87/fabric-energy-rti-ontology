# Demo Prompts — AegeanPowerDataAgent

The 10 prompts in the demo flight (run from `Test_Demo_Prompts.Notebook`).

> **Demo split**: Data Agent for cross-entity reasoning; Real-Time Dashboard for live numbers, the map, and the forced-failure cascade.

---

## The flight

1. **How many wind turbines do we have per manufacturer?** — warmup, grouping.
2. **Show all power plants in the Cyclades prefecture, with type, fuel, capacity and grid.** — geography: prefecture vs region.
3. **Show all substations with their voltage, type, and the plant they feed.** — entity + FK join.
4. **Which plants have both an open critical maintenance order AND a vessel currently dispatched to supply them?** — multi-entity intersection (mic-drop #1).
5. **Naxos Wind Farm: show every turbine, the grid it sits on, the substation feeding it, any vessels supplying it, and any open maintenance orders against its turbines.** — five entity types around one plant (mic-drop #2).
6. **List all maintenance orders that are open or in progress, with the asset, plant, priority and technician.** — open-MO inventory.
7. **List the solar inverters at Crete Solar Park with manufacturer, panel type and capacity.** — focused filter on one plant.
8. **Compare total installed capacity of renewable plants (wind + solar) vs natural-gas plants.** — two aggregates, narrative compare.
9. **Show every power plant with its type, fuel, region, prefecture, capacity and grid.** — full plant inventory.
10. **Give me a fleet master list: every turbine and inverter with its plant name, prefecture, grid, and capacity.** — closer, 42-row master list.

---

## What lives on the dashboard, not the agent

- Live turbine MW, inverter MW, grid frequency.
- Live vessel position + ETA on a map.
- Forced-failure cascade (force a turbine offline → KQL event → MO materializes live).
- Anything that requires aggregating streaming columns over a time window.

---

## Backup prompts (if a primary fails live)

- *"How many power plants do we have in total, and what types?"*
- *"Show all wind turbines with their plant name, manufacturer and capacity."*
- *"Which power plants are in the South Aegean region?"*
- *"How many maintenance orders have been completed this year?"*
