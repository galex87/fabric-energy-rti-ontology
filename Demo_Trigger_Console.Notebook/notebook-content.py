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

import notebookutils
# Resolve AegeanPowerLH via ABFSS so we don't depend on /lakehouse/default/ mount.
_lh = notebookutils.lakehouse.get("AegeanPowerLH")
_ws = _lh.get('workspaceId') or notebookutils.runtime.context['currentWorkspaceId']
CTRL = f"abfss://{_ws}@onelake.dfs.fabric.microsoft.com/{_lh['id']}/Files/control"
FAILED = f'{CTRL}/failed_turbines.txt'

existing = ''
if notebookutils.fs.exists(FAILED):
    existing = notebookutils.fs.head(FAILED, 1024).strip()
if existing:
    print(f'SKIP: failure already active -> {existing!r}')
else:
    notebookutils.fs.mkdirs(CTRL)
    notebookutils.fs.put(FAILED, 'WT-NAX-04\n', True)
    print('FAILED: WT-NAX-04')
    print('Watch the dashboard - power_mw will go to 0 within ~2 s.')

# Stop the PySpark session
mssparkutils.session.stop()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
