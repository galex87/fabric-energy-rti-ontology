# Fabric notebook source

# METADATA ********************

# META {
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "74b1118c-ad81-44e8-bcc6-c16465e827ef",
# META       "default_lakehouse_name": "AegeanPowerLH_Raw",
# META       "default_lakehouse_workspace_id": "21dbf808-03bb-44d9-a8f4-ac6166b1ce08"
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Create Data Agent for AegeanPowerLH_Raw
# This notebook creates a Fabric Data Agent connected to the obfuscated raw lakehouse.
# The agent has NO custom instructions - it must interpret the cryptic schema on its own.

# CELL ********************

%pip install fabric-data-agent-sdk --quiet

# CELL ********************

from fabric.dataagent.client import (
    FabricDataAgentManagement,
    create_data_agent,
    delete_data_agent,
)

AGENT_NAME = "AegeanPower_Raw_Agent"
LAKEHOUSE_NAME = "AegeanPowerLH_Raw"

# CELL ********************

# Create the Data Agent
data_agent = create_data_agent(AGENT_NAME)
print(f"Data Agent '{AGENT_NAME}' created successfully.")

# CELL ********************

# Add the raw lakehouse as a data source
ds = data_agent.add_datasource(LAKEHOUSE_NAME, type="lakehouse")
print(f"Datasource added: {ds}")

# CELL ********************

# Show available tables
datasource = data_agent.get_datasources()[0]
datasource.pretty_print()

# CELL ********************

# Select ALL 8 tables so the agent can see them
tables = [
    "wt_master", "pv_master", "gen_sites", "net_config",
    "vsl_tracking", "srv_activity", "node_infra", "env_reporting"
]
for t in tables:
    try:
        datasource.select("dbo", t)
        print(f"Selected: {t}")
    except Exception as e:
        print(f"Error selecting {t}: {e}")

# CELL ********************

# Verify selections
datasource.pretty_print()

# CELL ********************

# Publish the agent WITHOUT any custom instructions
# This is intentional - we want to see how it handles the cryptic schema
data_agent.publish()
print(f"Data Agent '{AGENT_NAME}' published successfully.")

# MARKDOWN ********************

# ## Sample Prompts to Test
# Try these in the Data Agent chat to see how it handles the obfuscated schema:
# 
# 1. **Show me all wind turbines** - Can it figure out `wt_master` = wind turbines?
# 2. **Which power plants are in the Cyclades region?** - Must map `gen_sites` + `rgn_cd`
# 3. **What is the total installed capacity per island grid?** - Needs `net_config.tot_cap`
# 4. **List maintenance orders for plant P001** - `srv_activity` + `parent_ref` FK
# 5. **Show vessels heading to the Milos Solar Park** - `vsl_tracking.dest_ref` = plant_id
# 6. **What are the CO2 emissions for each power plant in 2024?** - `env_reporting.entity_cd` = plant_id
# 7. **Join wind turbines with their power plant location** - `wt_master.loc_cd` = `gen_sites.loc_id`
# 8. **Show substations connected to plant P003** - `node_infra.link_src` = plant_id
