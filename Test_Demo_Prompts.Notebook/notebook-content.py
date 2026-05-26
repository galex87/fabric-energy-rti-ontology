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
    "List all wind turbines grouped by plant, with manufacturer and capacity.",
    "Show all power plants in the Cyclades prefecture, with type, fuel, capacity and grid.",
    "How many wind turbines do we have per manufacturer?",
    "Show CO2 emissions for our natural-gas plants in March 2026, with ETS allowances and compliance status.",
    "Which wind turbines currently have a Critical open maintenance order? Include turbine, plant, technician and description.",
    "List vessels that are dispatched or en route, with destination and the plant they supply.",
    "Show all substations with voltage, grid and the plant they feed.",
    "List the solar inverters at Crete Solar Park with manufacturer, panel type and capacity.",
    "Compare total installed capacity of renewable plants (wind + solar) vs natural-gas plants.",
    "Naxos Wind Farm: show every turbine and any open maintenance orders against them.",
]

assistant = client.beta.assistants.create(model="not-used")

def ask(question, idx):
    print(f"\n{'=' * 80}\nQ{idx:02d}: {question}\n{'-' * 80}")
    t0 = time.time()
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)
    run = client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=assistant.id)
    dt = time.time() - t0
    if run.status != "completed":
        print(f"  STATUS = {run.status} ({dt:.1f}s)")
        return
    msgs = client.beta.threads.messages.list(thread_id=thread.id)
    answers = [m for m in msgs.data if m.run_id == run.id and m.role == "assistant"]
    answers = sorted(answers, key=lambda m: (m.created_at, m.id))
    print(f"  ({dt:.1f}s)")
    for m in answers:
        for c in m.content:
            if hasattr(c, "text"):
                print(c.text.value)

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
