# Demo flight — 10 prompts, full entity coverage

Run via `Test_Demo_Prompts.Notebook`. Each prompt is tagged with what it exercises.

| # | Prompt | Entity / pattern |
|---|---|---|
| 1 | Show every power plant with its type, fuel, capacity, region and prefecture. | **PowerPlant** — static inventory |
| 2 | List all wind turbines grouped by plant, with manufacturer, model and rated capacity. | **WindTurbine** — static, grouped by FK |
| 3 | List the solar inverters at Crete Solar Park with manufacturer, panel type and capacity. | **SolarInverter** — static, focused filter |
| 4 | For every island grid, show its installed capacity alongside its current frequency, load and generation. | **IslandGrid** — static + live colocated |
| 5 | For every vessel, show its type and the plant it is assigned to supply, alongside its current position, speed and destination. | **Vessel** — static + live colocated |
| 6 | Show every substation with its voltage, the grid it belongs to, and the plant it feeds. | **Substation** — multi-entity FK join |
| 7 | List every open or in-progress maintenance order with the affected asset, its plant, the priority and the technician. | **MaintenanceOrder** — multi-entity join |
| 8 | For each gas plant, show total CO2 emitted across all available 2026 periods and the latest compliance status. | **EmissionsRecord** — `period` string filter + aggregate |
| 9 | Naxos Wind Farm: every turbine with manufacturer and capacity, the grid it sits on, the substation feeding it, the vessel assigned to supply it, and any open maintenance orders against its turbines. | **Mic-drop** — 5-entity drilldown around one plant |
| 10 | For each wind farm, show total nameplate capacity and the sum of current power output across its turbines. | **Fleet snapshot** — static + live aggregate |

All 8 entity types touched; prompts 4, 5 and 10 force the agent to fetch live timeseriesProperties alongside static fields.
