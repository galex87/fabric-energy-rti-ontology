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
    # 1. PowerPlant — static
    "Show every power plant with its type, fuel, capacity, region and prefecture.",
    # 2. WindTurbine — static, grouped
    "List all wind turbines grouped by plant, with manufacturer, model and rated capacity.",
    # 3. SolarInverter — static, focused
    "List the solar inverters at Crete Solar Park with manufacturer, panel type and capacity.",
    # 4. Grid — static inventory (live query unreliable in current preview)
    "List all 6 grids with their island, region, installed capacity and peak demand.",
    # 5. Vessel — static + live
    "For every vessel, show its type and the plant it is assigned to supply, alongside its current position, speed and destination.",
    # 6. Substation — multi-entity join (static)
    "Show every substation with its voltage, the grid it belongs to, and the plant it feeds.",
    # 7. MaintenanceOrder — multi-entity join (static)
    "List every open or in-progress maintenance order with the affected asset, its plant, the priority and the technician.",
    # 8. EmissionsRecord — pure static inventory (period filter unreliable)
    "List every emissions record with plant name, period, CO2 tonnes, ETS allowance and compliance status.",
    # 9. Multi-entity, single plant (the mic-drop)
    "Naxos Wind Farm: every turbine with manufacturer and capacity, the grid it sits on, the substation feeding it, the vessel assigned to supply it, and any open maintenance orders against its turbines.",
    # 10. Fleet snapshot — static + live aggregate
    "For each wind farm, show total nameplate capacity and the sum of current power output across its turbines.",
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
