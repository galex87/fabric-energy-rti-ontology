# Activator rules for energy demo

Use `energy_realtime` as the data source.

## Rule: Critical grid stress

- Trigger when `alert_level == "critical"`
- Recommended action: Teams/Email notification to grid operations
- Suggested message:
  `Critical energy event at {site_id}: demand={grid_demand_mw}MW, renewable_ratio={renewable_ratio}, co2={co2_intensity_g_kwh}g/kWh`

## Rule: Warning trend

- Trigger when `alert_level == "warning"` for 3 consecutive events in 10 minutes for the same `site_id`
- Recommended action: create incident/ticket for operator review
