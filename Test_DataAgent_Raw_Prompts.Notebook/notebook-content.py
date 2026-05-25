# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "74b1118c-ad81-44e8-bcc6-c16465e827ef",
# META       "default_lakehouse_name": "AegeanPowerLH_Raw",
# META       "default_lakehouse_workspace_id": "21dbf808-03bb-44d9-a8f4-ac6166b1ce08",
# META       "known_lakehouses": [
# META         {
# META           "id": "74b1118c-ad81-44e8-bcc6-c16465e827ef"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

import subprocess, sys
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'fabric-data-agent-sdk', '-q'])
print('SDK installed')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

%pip install "typing_extensions>=4.8.0" -q

from fabric.dataagent.client import FabricDataAgentManagement, create_data_agent, FabricOpenAI
import time

AGENT_NAME = 'AegeanPower_Raw_Agent'
LAKEHOUSE_NAME = 'AegeanPowerLH_Raw'

# Connect to existing agent
try:
    data_agent = FabricDataAgentManagement(AGENT_NAME)
    print(f'Connected to: {AGENT_NAME}')
except Exception as e:
    # If the agent does not exist yet, create it
    print(f'Could not connect to existing agent (reason: {e}). Creating a new one...')
    data_agent = create_data_agent(AGENT_NAME)
    print(f'Created: {AGENT_NAME}')

# Add lakehouse as datasource
existing = data_agent.get_datasources()
if existing:
    datasource = existing[0]
    print('Datasource already connected')
else:
    datasource = data_agent.add_datasource(LAKEHOUSE_NAME, type='lakehouse')
    print(f'Added: {LAKEHOUSE_NAME}')

# Select all relevant tables from dbo schema
for t in ['wt_master','pv_master','gen_sites','net_config','vsl_tracking','srv_activity','node_infra','env_reporting']:
    try:
        datasource.select('dbo', t)
        print(f'Selected table: dbo.{t}')
    except Exception as e:
        # Ignore missing tables but log the reason for transparency
        print(f'Could not select table dbo.{t}: {e}')

# Publish changes to the data agent
data_agent.publish()
print('Published')

# Pretty print datasource details for verification
datasource.pretty_print()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Create client and run all 13 prompts
fabric_client = FabricOpenAI(artifact_name=AGENT_NAME)
assistant = fabric_client.beta.assistants.create(model='gpt-4o')
print(f'Assistant: {assistant.id}')

PROMPTS = [
    'Show me all wind turbines',
    'List all solar installations',
    'How many power plants are there?',
    'Which power plants are in the Cyclades region?',
    'Show me all active wind turbines',
    'What is the total installed capacity across all island grids?',
    'Show me the wind turbines at each power plant',
    'List all maintenance orders for the Milos Solar Park',
    'Show vessels heading to wind farm plants',
    'What substations are connected to plant P003?',
    'For each island grid, show the total number of power plants and their combined wind and solar capacity',
    'Show the total CO2 emissions per power plant, along with the plant name and region',
    'Which plants have both open maintenance orders and vessels en route?',
]

LEVELS = ['L1','L1','L1','L2','L2','L2','L3','L3','L3','L3','L4','L4','L4']

def ask(prompt, timeout=120):
    thread = fabric_client.beta.threads.create()
    fabric_client.beta.threads.messages.create(thread_id=thread.id, role='user', content=prompt)
    run = fabric_client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    elapsed = 0
    while run.status in ('queued','in_progress') and elapsed < timeout:
        run = fabric_client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        time.sleep(3)
        elapsed += 3
    if run.status != 'completed':
        return f'[STATUS: {run.status} after {elapsed}s]'
    msgs = fabric_client.beta.threads.messages.list(thread_id=thread.id, order='asc')
    resp = ''
    for m in msgs:
        if m.role == 'assistant':
            resp = m.content[0].text.value
    try:
        fabric_client.beta.threads.delete(thread.id)
    except:
        pass
    return resp

results = []
for i, prompt in enumerate(PROMPTS):
    print(f'\n{"="*70}')
    print(f'Prompt {i+1}/13 [{LEVELS[i]}]: {prompt}')
    print('-'*70)
    r = ask(prompt)
    results.append(r)
    print(r[:600])

print(f'\n{"="*70}')
print('ALL 13 PROMPTS COMPLETED')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Full results
for i, prompt in enumerate(PROMPTS):
    print(f'\n{"#"*70}')
    print(f'## Prompt {i+1} [{LEVELS[i]}]')
    print(f'Q: {prompt}')
    print(f'A: {results[i]}')
    print()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
