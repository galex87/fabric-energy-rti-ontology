# Full prompt coverage — every entity, static and live

A broader test set than the demo flight. Use it to validate the agent across the full ontology, or as a stretch pool to swap into demos. Grouped by what they exercise.

---

## A. Single-entity, static only

1. **PowerPlant** — *Show every power plant with type, fuel, capacity, region and prefecture.*
2. **WindTurbine** — *List all wind turbines grouped by plant with manufacturer, model and rated capacity.*
3. **SolarInverter** — *List all solar inverters with manufacturer, panel type, rated capacity, and the plant they belong to.*
4. **IslandGrid** — *List every island grid with its island name, region, installed capacity, peak demand and nominal frequency.*
5. **Vessel** — *List every vessel with its type, flag, cargo capacity, and the plant it is assigned to supply.*
6. **Substation** — *List every substation with its voltage, type, the grid it belongs to and the plant it feeds.*
7. **MaintenanceOrder** — *List every maintenance order with priority, status, asset id, plant id, technician and created date.*
8. **EmissionsRecord** — *List every emissions record with plant, period, CO2 tonnes, ETS allowance and compliance status.*

## B. Single-entity, live only

9. **WindTurbine** — *Show current power output, wind speed and vibration for every wind turbine.*
10. **SolarInverter** — *Show current power output, irradiance and panel temperature for every solar inverter.*
11. **IslandGrid** — *Show current frequency, load and generation for every island grid.*
12. **Vessel** — *Show current position, speed, heading and ETA for every vessel.*

## C. Single-entity, static **and** live combined

13. **WindTurbine** — *For every wind turbine, show manufacturer and rated capacity alongside current power output.*
14. **SolarInverter** — *For every solar inverter, show manufacturer and rated capacity alongside current power output and efficiency.*
15. **IslandGrid** — *For every island grid, show installed capacity alongside current frequency, load and generation.*
16. **Vessel** — *For every vessel, show its assigned plant alongside its current position, speed and destination.*

## D. Two-entity joins (static)

17. **Plant + Turbine** — *For each wind farm, list its turbines, manufacturers and the plant's total nameplate capacity.*
18. **Plant + Substation** — *For each power plant, show the substation feeding it and the grid it sits on.*
19. **Plant + Vessel** — *Which plants currently have a vessel assigned to supply them, and what type of vessel?*
20. **Plant + Emissions** — *For each gas plant, total CO2 emitted year-to-date and the latest compliance status.*
21. **MO + Turbine + Plant** — *List every open or in-progress maintenance order with the affected turbine or inverter, its plant, the priority and the technician.*
22. **Grid + Plant + Substation** — *For each island grid, list every plant on that grid and the substation feeding each one.*

## E. Multi-entity, static **and** live

23. **Plant fleet snapshot** — *For each wind farm, show total nameplate capacity and the sum of current power output across its turbines.*
24. **Naxos drilldown** — *Naxos Wind Farm: every turbine with manufacturer, capacity, current power output, and any open maintenance orders against it.*
25. **Cyclades live posture** — *For each plant in the Cyclades, show current total generation and the grid it sits on.*

## F. Geography-aware

26. **By region** — *List every power plant in the South Aegean region.*
27. **By prefecture** — *Which plants are in the Larissa prefecture?*
28. **Mainland vs islands** — *How many plants are on mainland Greece versus on islands?*

## G. Time-bounded (period column)

29. **Emissions month** — *Show emissions for every gas plant for the month "2026-04".*
30. **Emissions year** — *Total CO2 emissions for each gas plant across all periods in 2026.*

## H. Maintenance angles

31. **Open by priority** — *How many maintenance orders are currently open, grouped by priority?*
32. **Completed in 2026** — *How many maintenance orders have been completed in 2026, and by which technician?*
33. **Costly fixes** — *List the five most expensive completed maintenance orders.*

## I. Status overview

34. **Plant fleet** — *How many plants do we have by type (wind farm, solar park, gas)?*
35. **Asset fleet** — *Total count of turbines + inverters per plant.*

---

## How to use

- Copy any prompt into the Data Agent chat or add to `Test_Demo_Prompts.Notebook`.
- The prompts in **C** and **E** exercise the dual static + live colocation — if those fail, it tells you the agent isn't generating `timeSeriesSelector`.
- The prompts in **D** and **E** exercise multi-entity joins — if those fan out or fail, the join model needs work.
- The prompts in **G** verify the `period` string handling.
