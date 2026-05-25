# Troubleshooting

Common pitfalls when running this demo. In order of how often they bite.

---

## Eventstream destination shows empty fields after restart

**Symptom:** After deactivating/reactivating the eventstream, only numeric fields (lat/lon) land in the destination tables. All string fields are empty.

**Cause:** Eventstream restart can lose the JSON-to-column field mapping for derived streams whose filter operators had a stale `inputSchema`.

**Fix:**
1. Open `AegeanPowerStream` → for each destination → **Edit** → re-save (don't change anything, just re-bind).
2. **Publish**.
3. If still broken, drop and recreate the destination tables in `AegeanPowerEH` with explicit columns + JSON ingestion mapping, then re-bind the eventstream destination.

---

## Activator fires once but not again

**Symptom:** The first time you trigger `WT-NAX-04`, Activator fires and the notebook runs. Subsequent triggers do nothing — even after deleting `failed_turbines.txt`.

**Cause:** Activator keeps a per-object-instance memory of the last value of `fault_type`. The rule is `Changes to DEMO_FORCED_FAILURE`. If Activator's last memory is already `DEMO_FORCED_FAILURE`, your new trigger doesn't look like a change.

**Fix:**
1. Delete `failed_turbines.txt` (simulator stops forcing the failure).
2. **Wait 15 seconds** while the simulator is still running. During this window the simulator emits `fault_type=NONE` for that turbine. Activator's memory flips to `NONE`.
3. Re-run the trigger cell. Now Activator sees `NONE → DEMO_FORCED_FAILURE` = real transition → fires.

> The wait must happen with the simulator running. If you stop the simulator, no `NONE` events flow, and Activator's memory stays stale.

---

## `fault_type` column appears empty in events (Activator never fires)

**Symptom:** KQL shows `fault_type == ""` for non-failure events. Activator chart shows dots only when a real failure occurs; never reports a transition.

**Cause:** Simulator was emitting `None` / empty string for `fault_type` when no fault was present. Activator's "Changes to X" doesn't trigger on `"" → X` because empty isn't a value.

**Fix:** the simulator notebook already has the patched line:
```python
fault_type = scripted_fault or anomaly_fault or "NONE"
```
If you forked an older version, ensure this exact line is in `gen_wind`.

---

## Lakehouse tables are empty after first sync

**Cause:** Fabric Git syncs item *metadata*, not table data. Lakehouses arrive empty.

**Fix:** Follow steps 4–5 of the [README](../README.md#quickstart): upload CSVs from `data/`, run `Load_CSVs_to_Delta`.

---

## Eventstream connection string is invalid

**Symptom:** Simulator runs but no data lands in Eventhouse.

**Cause:** The committed simulator notebook has a placeholder `REPLACE_ME_…` value. Each workspace gets its own connection string.

**Fix:** Follow steps 6–7 of the README. Connection string lives at `AegeanPowerStream` → Source → CustomApp → **Sample code** → copy primary key.

---

## Activator action says "Notebook not found"

**Cause:** The Activator rule's action references the original workspace's notebook GUID, not yours.

**Fix:** Open the rule → **Action** → re-pick `Dispatch_Maintenance_Crew` from *your* workspace → **Save**.

---

## Data Agent says "No data sources"

**Cause:** Data Agent's data source bindings reference the original Lakehouse GUID, which doesn't exist in your workspace.

**Fix:** Open `AegeanPowerDataAgent` → **+ Data source** → select your local `AegeanPowerLH` and tick all tables → **Publish**.

---

## Dashboard tiles are empty

**Cause:** KQL queries in the dashboard target the original `AegeanPowerEH` GUID.

**Fix:** Open the dashboard → top-right **Manage data sources** → edit → re-bind to your local `AegeanPowerEH` → **Save**.

---

## Git push fails with "Push cannot contain secrets"

**Symptom:** When committing changes that include a real Event Hub connection string, GitHub Push Protection blocks the push.

**Fix:** Never commit a real `Endpoint=sb://…` connection string. Use the placeholder `REPLACE_ME_…` in the simulator notebook. If you accidentally committed one, you must `git reset` or use the "allow secret" link GitHub provides in the error to override.

---

## Vessel doesn't move after dispatch

**Symptom:** Activator fired, dispatch notebook ran, but the vessel `VE-SVC-01` stays on its original route.

**Cause:** Simulator polls `Files/control/dispatch_poseidon.txt` only when the lakehouse binding is intact. If the simulator was started before the lakehouse was bound, it can't read the file.

**Fix:**
1. Confirm `AegeanPower_Simulator` notebook has `AegeanPowerLH` set as default lakehouse (Lakehouses sidebar).
2. Stop and restart the simulator.

---

## Fabric Git: "Update all" fails with "Item depends on missing item"

**Cause:** Items are pulled in parallel; some have dependencies (Eventstream → Eventhouse, Activator → Eventstream + Notebook) that aren't resolved yet.

**Fix:** Click **Update all** a second time. The second pass resolves the dependencies. If still failing, sync items in waves: Lakehouse + Eventhouse first → notebooks → Eventstream → Activator → Dashboard → Data Agent.
