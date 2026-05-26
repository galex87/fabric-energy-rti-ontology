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
    "How many wind turbines do we have per manufacturer?",
    "Show all power plants in the Cyclades prefecture, with type, fuel, capacity and grid.",
    "List vessels that are dispatched or en route, with their destination and the plant they supply.",
    "Which plants have both an open critical maintenance order AND a vessel currently dispatched to supply them?",
    "Naxos Wind Farm: show every turbine, the grid it sits on, the substation feeding it, any vessels supplying it, and any open maintenance orders against its turbines.",
    "Show CO2 emissions for our natural-gas plants in March 2026, with ETS allowances and compliance status.",
    "Who has the most open maintenance orders right now, and which ones are they?",
    "Compare total installed capacity of renewable plants (wind + solar) vs natural-gas plants.",
    "Give me a live snapshot: which turbines are below 30% of their nameplate capacity right now, and which plants do they belong to?",
    "Give me a fleet master list: every turbine and inverter with its plant name, prefecture, grid, and capacity.",
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
