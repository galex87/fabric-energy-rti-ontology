# Demo prompts (30) — pass/fail from latest run

All 30 prompts are in `Test_Demo_Prompts.Notebook`. Run them, pick what you like.

Legend: ✅ works · ❌ fails (agent confused itself, see notes) · ⚠️ partially correct

## Static single-entity

| # | Prompt | Status |
|---|---|---|
| 1 | Show every power plant with its type, fuel, capacity, region and prefecture. | ✅ |
| 2 | List all wind turbines grouped by plant, with manufacturer, model and rated capacity. | ✅ |
| 3 | List the solar inverters at Crete Solar Park with manufacturer, panel type and capacity. | ✅ |
| 4 | List all 6 grids with their island, region, installed capacity and peak demand. | ✅ |
| 5 | Show every substation with its voltage, the grid it belongs to, and the plant it feeds. | ✅ |
| 6 | List every vessel with its name, type, flag, cargo capacity and the plant it is assigned to supply. | ✅ |
| 7 | List every maintenance order with its priority, status, asset id, plant id, technician and created date. | ✅ |
| 8 | List every emissions record with plant name, period, CO2 tonnes, ETS allowance and compliance status. | ✅ |

## Static joins

| # | Prompt | Status |
|---|---|---|
| 9 | For each wind farm, list its turbines with manufacturer and capacity, and the total nameplate capacity of the plant. | ✅ |
| 10 | For each power plant, show the substation feeding it and the grid it sits on. | ✅ |
| 11 | For each gas plant, list its emissions records (all periods) with CO2 tonnes and compliance status. | ❌ Agent filters `fuel_type = "gas"` instead of `"Natural Gas"`. |
| 12 | List every wind turbine alongside its plant name, region and prefecture. | ✅ |
| 13 | Show every solar inverter with its plant name and the grid that plant is connected to. | ✅ |

## Static + live (single entity, no aggregation)

| # | Prompt | Status |
|---|---|---|
| 14 | For every vessel, show its type and the plant it is assigned to supply, alongside its current position, speed and destination. | ✅ |
| 15 | Show every wind turbine with its plant, manufacturer, nameplate capacity, and current power output. | ✅ |
| 16 | Show every solar inverter with its plant, manufacturer, nameplate capacity, and current power output. | ✅ |
| 17 | For every vessel, list its name, the plant it is assigned to supply, its current speed and current heading. | ✅ |
| 18 | For every wind turbine, show its current wind speed and current power output alongside its nameplate capacity. | ✅ |
| 19 | For every solar inverter, show its current irradiance and current power output alongside its nameplate capacity. | ✅ |
| 20 | Show every grid with its installed capacity and its current frequency, load and generation. | ✅ |

## Geography / categorical filters

| # | Prompt | Status |
|---|---|---|
| 21 | List the plants located in the Cyclades prefecture, with type, fuel and capacity. | ✅ |
| 22 | List every plant in the South Aegean region, with type, fuel and grid id. | ✅ |
| 23 | List every gas power plant with capacity, region and prefecture. | ❌ Agent filters `fuel_type = "gas"`. |
| 24 | List every wind farm with capacity, region, prefecture and grid id. | ⚠️ Returns all 7 plants instead of just wind farms — agent ignored the filter. |

## Maintenance angles

| # | Prompt | Status |
|---|---|---|
| 25 | List every maintenance order with status Open or In Progress, showing asset id, plant id, priority and technician. | ✅ |
| 26 | List every Critical maintenance order, regardless of status. | ✅ |
| 27 | List every maintenance order completed in 2026, with technician, asset id, plant id and cost in euros. | ✅ |

## Mic-drop cross-cuts

| # | Prompt | Status |
|---|---|---|
| 28 | Naxos Wind Farm: list every turbine with manufacturer and capacity, the grid it sits on, and the substation feeding it. | ✅ |
| 29 | For Lavrio Gas CCGT: show its capacity, region, the substation feeding it, and the vessel assigned to supply it. | ✅ |
| 30 | For each wind farm, list every turbine with its manufacturer, capacity, and current power output. | ✅ |

---

**Score: 27 ✅ · 2 ❌ · 1 ⚠️**

Live telemetry (turbines, inverters, vessels, grids) works end-to-end. The two hard failures are both about the agent shortening `"Natural Gas"` to `"gas"` despite the enum cheat sheet in agent instructions — rephrase the prompt to say *"Natural Gas plants"* if you need #11 or #23.
