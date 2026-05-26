# Demo prompts

Try these against **AegeanPowerDataAgent** in your Fabric workspace.

## Inventory

- Show every power plant with its type, fuel, capacity, region and prefecture.
- List all wind turbines grouped by plant, with manufacturer, model and rated capacity.
- List the solar inverters at Crete Solar Park with manufacturer, panel type and capacity.
- List all 6 grids with their island, region, installed capacity and peak demand.
- Show every substation with its voltage, the grid it belongs to, and the plant it feeds.
- List every vessel with its name, type, flag, cargo capacity and the plant it is assigned to supply.
- List every maintenance order with its priority, status, asset id, plant id, technician and created date.
- List every emissions record with plant name, period, CO2 tonnes, ETS allowance and compliance status.

## Joins across entities

- For each wind farm, list its turbines with manufacturer and capacity, and the total nameplate capacity of the plant.
- For each power plant, show the substation feeding it and the grid it sits on.
- List every wind turbine alongside its plant name, region and prefecture.
- Show every solar inverter with its plant name and the grid that plant is connected to.

## Live telemetry (real-time)

- For every vessel, show its type and the plant it is assigned to supply, alongside its current position, speed and destination.
- Show every wind turbine with its plant, manufacturer, nameplate capacity, and current power output.
- Show every solar inverter with its plant, manufacturer, nameplate capacity, and current power output.
- For every vessel, list its name, the plant it is assigned to supply, its current speed and current heading.
- For every wind turbine, show its current wind speed and current power output alongside its nameplate capacity.
- For every solar inverter, show its current irradiance and current power output alongside its nameplate capacity.
- Show every grid with its installed capacity and its current frequency, load and generation.

## Geography

- List the plants located in the Cyclades prefecture, with type, fuel and capacity.
- List every plant in the South Aegean region, with type, fuel and grid id.

## Maintenance

- List every maintenance order with status Open or In Progress, showing asset id, plant id, priority and technician.
- List every Critical maintenance order, regardless of status.
- List every maintenance order completed in 2026, with technician, asset id, plant id and cost in euros.

## Drilldowns

- Naxos Wind Farm: list every turbine with manufacturer and capacity, the grid it sits on, and the substation feeding it.
- For Lavrio Gas CCGT: show its capacity, region, the substation feeding it, and the vessel assigned to supply it.
- For each wind farm, list every turbine with its manufacturer, capacity, and current power output.
