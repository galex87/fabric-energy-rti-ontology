# Demo Prompts

Prompts to send to **`AegeanPowerDataAgent`**. The agent is grounded in `AegeanPowerOntology` over the clean `AegeanPowerLH` Delta tables.

---

## Top 3 (the demo flight)

Run these in order during the live demo:

1. Show me all wind turbines.
2. Which wind turbines are at plants in the Cyclades islands?
3. Which plants have both open maintenance orders and vessels en route?

**Why these:** #1 warms up. #2 demonstrates the region vs prefecture distinction the ontology resolves automatically. #3 is the mic-drop — a triple-FK join (`plant_id`, `vessels.supply_plant_id`, `maintenance_orders.plant_id`) that only ontology-aware schemas can answer.

---

## Full prompt pool (14)

### Single-table lookups

- Show me all wind turbines.
- List all solar installations.
- How many power plants are there?
- Show me all active wind turbines.

### Filtering

- Which power plants are in the Cyclades region?
- What is the total installed capacity across all island grids?
- Which wind turbines are at plants in the Cyclades islands?

### Cross-table joins

- Show me the wind turbines at each power plant.
- List all maintenance orders for the Milos Solar Park.
- Show vessels heading to wind farm plants.
- What substations are connected to plant P003?

### Multi-table analytics

- For each island grid, show the total number of power plants and their combined wind and solar capacity.
- Show the total CO₂ emissions per power plant, along with the plant name and region.
- Which plants have both open maintenance orders and vessels en route?

---

## Emissions deep-dive (optional extension)

If your demo time allows, the emissions angle is rich:

- Show me total CO₂ emissions per plant this year, ranked highest to lowest.
- How much CO₂ did our renewable wind and solar generation displace this year compared to our conventional plants — and what's our overall carbon intensity in tonnes per MWh?
- Which plants are exceeding their emissions targets AND have open critical maintenance orders — and rank them by combined risk.

---

## Operations Agent prompts (after triggering a fault)

Once a turbine is in `DEMO_FORCED_FAILURE`:

- What is happening right now at Naxos Wind Farm, and is anyone responding?
- Which turbines are offline right now and why?
- Has a vessel been dispatched for the Naxos failure? When does it arrive?
