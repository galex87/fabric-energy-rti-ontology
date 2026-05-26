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
    "Give me a real-time operational snapshot: total active plants, current generation in MW, vessels in transit, and any critical open maintenance orders.",
    "What is the current renewable share of our total generation right now versus our installed renewable capacity? Show me both numbers and the gap.",
    "Which wind turbine has the highest vibration right now, and is its plant tied to an active grid? Show its latest power output.",
    "Are any island grids currently deviating from 50 Hz by more than 0.3 Hz? Show grid name, current frequency, current load, and current generation.",
    "Which wind turbines have a Critical Open maintenance order, and is a service vessel currently dispatched to their plant? Show turbine, plant, technician, order description, vessel name, vessel current speed, and ETA.",
    "For every plant in the Cyclades islands, show the assets it contains, the substation feeding it, the grid it sits on, and whether any of its assets have open maintenance orders.",
    "Rank our gas plants by CO2 emissions year-to-date in 2026. Show plant name, total tonnes emitted, ETS allowance used, and current compliance status.",
    "How much CO2 are our renewable plants displacing right now compared to a baseline where we'd generate the same MW from natural gas at 0.35 tCO2/MWh?",
    "List solar inverters whose current efficiency is below 90% and whose last completed maintenance was over 90 days ago. Show inverter name, current efficiency, manufacturer, and last completed maintenance date.",
    "Tell me about Naxos Wind Farm right now: how many turbines are active, what is their combined live generation, what is the latest grid frequency on the Naxos grid, what open maintenance orders exist, and is the Poseidon Service vessel responding to any of them?",
]

def ask(question, idx):
    print(f"\n{'=' * 80}\nQ{idx:02d}: {question}\n{'-' * 80}")
    t0 = time.time()
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=client.get_assistant_id())
    while run.status in ("queued", "in_progress"):
        time.sleep(2)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    dt = time.time() - t0
    if run.status != "completed":
        print(f"  STATUS = {run.status} ({dt:.1f}s)")
        return
    msgs = client.beta.threads.messages.list(thread_id=thread.id, order="asc")
    answer = ""
    for m in msgs.data:
        if m.role == "assistant":
            for c in m.content:
                if hasattr(c, "text"):
                    answer = c.text.value
    print(f"  ({dt:.1f}s)")
    print(answer)

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
