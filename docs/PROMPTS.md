# Demo flight — 10 prompts

Run via `Test_Demo_Prompts.Notebook`.

| # | Prompt | Entity / pattern |
|---|---|---|
| 1 | Show every power plant with its type, fuel, capacity, region and prefecture. | **PowerPlant** — static |
| 2 | List all wind turbines grouped by plant, with manufacturer, model and rated capacity. | **WindTurbine** — static, grouped |
| 3 | List the solar inverters at Crete Solar Park with manufacturer, panel type and capacity. | **SolarInverter** — static, focused |
| 4 | List all 6 grids with their island, region, installed capacity and peak demand. | **Grid** — static inventory |
| 5 | For every vessel, show its type and the plant it is assigned to supply, alongside its current position, speed and destination. | **Vessel** — static + **live** |
| 6 | Show every substation with its voltage, the grid it belongs to, and the plant it feeds. | **Substation** — multi-entity join |
| 7 | List every open or in-progress maintenance order with the affected asset, its plant, the priority and the technician. | **MaintenanceOrder** — multi-entity join |
| 8 | List every emissions record with plant name, period, CO2 tonnes, ETS allowance and compliance status. | **EmissionsRecord** — static inventory |
| 9 | Naxos Wind Farm: every turbine with manufacturer and capacity, the grid it sits on, the substation feeding it, the vessel assigned to supply it, and any open maintenance orders against its turbines. | **Mic-drop** — 5-entity drilldown |
| 10 | For each wind farm, show total nameplate capacity and the sum of current power output across its turbines. | **Fleet snapshot** — static + **live** aggregate |

All 8 entity types covered. #5 and #10 exercise live timeseries data.
