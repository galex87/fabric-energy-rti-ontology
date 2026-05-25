# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "bd9c69ce-ee2b-45a9-854d-13696f476a96",
# META       "default_lakehouse_name": "AegeanPowerLH",
# META       "default_lakehouse_workspace_id": "21dbf808-03bb-44d9-a8f4-ac6166b1ce08"
# META     }
# META   }
# META }

# MARKDOWN ********************

# # 🚨 Demo Trigger Console
# 
# **One-click controls for the live Operations Agent demo.**
# 
# - Each button writes a tiny control file under `Files/control/` that the simulator polls every tick (~2 s).
# - Run a cell -> change reflected on the dashboard within a couple of seconds.


# MARKDOWN ********************

# ## SCENE 1 - Trigger turbine failure
# 
# Run this when you want **WT-NAX-04** (Naxos Wind Farm) to drop to 0 MW. The dashboard line will collapse within ~2 s, Activator will fire on `power_mw == 0`.

# CELL ********************

import os
CTRL = '/lakehouse/default/Files/control'
FAILED = f'{CTRL}/failed_turbines.txt'

if os.path.exists(FAILED) and open(FAILED).read().strip():
    print(f'SKIP: failure already active -> {open(FAILED).read().strip()!r}')
else:
    os.makedirs(CTRL, exist_ok=True)
    with open(FAILED, 'w') as f:
        f.write('WT-NAX-04\n')
    print('FAILED: WT-NAX-04')
    print('Watch the dashboard - power_mw will go to 0 within ~2 s.')

# Stop the PySpark session
mssparkutils.session.stop()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
