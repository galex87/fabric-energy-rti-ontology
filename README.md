# fabric-energy-rti-ontology

End-to-end Microsoft Fabric energy demo that combines:

- **Live wind / solar / grid simulator**
- **Real-Time Intelligence Eventstream**
- **Eventhouse ingestion + KQL**
- **Activator alert conditions**
- **Real-Time Dashboard query set**
- **Ontology-driven Data Agent prompt**

## Demo architecture

```text
live_energy_simulator.py (JSON events)
        -> Fabric Eventstream
        -> Eventhouse table: energy_realtime
        -> Activator rules + dashboard queries
        -> Ontology-driven Data Agent responses
```

## 1) Run the live simulator

```bash
python simulator/live_energy_simulator.py --interval-seconds 2
```

Options:

- `--events N` emit a fixed number of events (good for tests/demos)
- `--seed N` deterministic stream for repeatable runs
- `--pretty` pretty-print JSON

Each event includes timestamp, site id, wind/solar production, demand, renewable ratio, estimated CO2 intensity, and a computed `alert_level` (`normal`, `warning`, `critical`).

## 2) Fabric Eventstream

Use `fabric/eventstream/schema.json` as the event contract when configuring the Eventstream source and destination mapping.

## 3) Eventhouse setup

Run KQL in `fabric/eventhouse/setup.kql` to create and map table `energy_realtime`.

Use `fabric/eventhouse/queries.kql` for:

- Latest telemetry
- 5-minute renewable performance
- Critical alert feed for Activator
- Dashboard visuals

## 4) Activator

Create Activator items with conditions from `fabric/activator/rules.md`:

- `critical` when renewable ratio < 25% and demand > 160 MW
- `warning` when renewable ratio < 40% or CO2 intensity > 380

## 5) Ontology-driven Data Agent

- Ontology file: `fabric/ontology/energy_ontology.ttl`
- Data agent system prompt: `fabric/data-agent/system-prompt.md`

The prompt constrains responses to ontology concepts and Eventhouse-backed metrics.

## Local validation

```bash
python -m unittest discover -s tests -p "test_*.py"
python simulator/live_energy_simulator.py --events 3 --seed 7 --pretty
```
