# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {}
# META   }
# META }

# MARKDOWN ********************

# # Test the 10 demo prompts against AegeanPowerDataAgent
#
# This notebook calls the published Data Agent endpoint via `fabric_data_agent_sdk` and prints each answer.
#
# Prereqs:
# - `AegeanPowerDataAgent` is published (Publish button in the agent's editor).
# - The agent has at least one data source (e.g. `AegeanPowerOntology`).
# - The simulator is running so live KQL questions have data to find.
#
# Run all → copy the output → share with the maintainer to grade and refine instructions.

# CELL ********************

# Install + import the SDK
%pip install -q fabric-data-agent-sdk

import time
from fabric.dataagent.client import FabricOpenAI

DATA_AGENT_NAME = "AegeanPowerDataAgent"
client = FabricOpenAI(artifact_name=DATA_AGENT_NAME)
print("Connected to", DATA_AGENT_NAME)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

PROMPTS = [
    # ---- Static single-entity (8) ----
    "Show every power plant with its type, fuel, capacity, region and prefecture.",
    "List all wind turbines grouped by plant, with manufacturer, model and rated capacity.",
    "List the solar inverters at Crete Solar Park with manufacturer, panel type and capacity.",
    "List all 6 grids with their island, region, installed capacity and peak demand.",
    "Show every substation with its voltage, the grid it belongs to, and the plant it feeds.",
    "List every vessel with its name, type, flag, cargo capacity and the plant it is assigned to supply.",
    "List every maintenance order with its priority, status, asset id, plant id, technician and created date.",
    "List every emissions record with plant name, period, CO2 tonnes, ETS allowance and compliance status.",

    # ---- Static joins (4) ----
    "For each wind farm, list its turbines with manufacturer and capacity, and the total nameplate capacity of the plant.",
    "For each power plant, show the substation feeding it and the grid it sits on.",
    "List every wind turbine alongside its plant name, region and prefecture.",
    "Show every solar inverter with its plant name and the grid that plant is connected to.",

    # ---- Static + live (single entity, no aggregation) (7) ----
    "For every vessel, show its type and the plant it is assigned to supply, alongside its current position, speed and destination.",
    "Show every wind turbine with its plant, manufacturer, nameplate capacity, and current power output.",
    "Show every solar inverter with its plant, manufacturer, nameplate capacity, and current power output.",
    "For every vessel, list its name, the plant it is assigned to supply, its current speed and current heading.",
    "For every wind turbine, show its current wind speed and current power output alongside its nameplate capacity.",
    "For every solar inverter, show its current irradiance and current power output alongside its nameplate capacity.",
    "Show every grid with its installed capacity and its current frequency, load and generation.",

    # ---- Geography / categorical filters (2) ----
    "List the plants located in the Cyclades prefecture, with type, fuel and capacity.",
    "List every plant in the South Aegean region, with type, fuel and grid id.",

    # ---- Maintenance angles (3) ----
    "List every maintenance order with status Open or In Progress, showing asset id, plant id, priority and technician.",
    "List every Critical maintenance order, regardless of status.",
    "List every maintenance order completed in 2026, with technician, asset id, plant id and cost in euros.",

    # ---- Mic-drop cross-cuts (3) ----
    "Naxos Wind Farm: list every turbine with manufacturer and capacity, the grid it sits on, and the substation feeding it.",
    "For Lavrio Gas CCGT: show its capacity, region, the substation feeding it, and the vessel assigned to supply it.",
    "For each wind farm, list every turbine with its manufacturer, capacity, and current power output.",
]

assistant = client.beta.assistants.create(model="not-used")

def _dump_steps(thread_id, run_id):
    """Dump tool-call steps so we can root-cause failures: GQL query + raw output."""
    try:
        steps = client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run_id, order="asc")
    except Exception as e:
        print(f"  [steps unavailable: {e}]")
        return
    for s in steps.data:
        sd = getattr(s, "step_details", None)
        if not sd or getattr(sd, "type", None) != "tool_calls":
            continue
        for tc in getattr(sd, "tool_calls", []) or []:
            fn = getattr(tc, "function", None) or getattr(tc, "code_interpreter", None) or tc
            name = getattr(fn, "name", getattr(tc, "type", "tool"))
            args = getattr(fn, "arguments", getattr(fn, "input", ""))
            out = getattr(fn, "output", "")
            if args:
                print(f"  -- {name} args --")
                print("    " + str(args)[:2000].replace("\n","\n    "))
            if out:
                print(f"  -- {name} output (first 1200 chars) --")
                print("    " + str(out)[:1200].replace("\n","\n    "))

def ask(question, idx):
    print(f"\n{'=' * 80}\nQ{idx:02d}: {question}\n{'-' * 80}")
    t0 = time.time()
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)
    run = client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=assistant.id)
    dt = time.time() - t0
    print(f"  status={run.status}  ({dt:.1f}s)")
    _dump_steps(thread.id, run.id)
    if run.status != "completed":
        return
    msgs = client.beta.threads.messages.list(thread_id=thread.id)
    answers = [m for m in msgs.data if m.run_id == run.id and m.role == "assistant"]
    answers = sorted(answers, key=lambda m: (m.created_at, m.id))
    print("  -- final answer --")
    for m in answers:
        for c in m.content:
            if hasattr(c, "text"):
                print("    " + c.text.value.replace("\n","\n    "))

for i, q in enumerate(PROMPTS, 1):
    try:
        ask(q, i)
    except Exception as e:
        print(f"  EXCEPTION: {e}")
print("\n" + "=" * 80 + "\nDone.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
