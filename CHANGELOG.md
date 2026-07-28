# Changelog

## 2.2.1

- Redesigned the live performance area with larger gauges and clearer status hierarchy.
- Moved power imbalance into a dedicated full-width diagnostic panel.
- Redesigned today's energy metrics with larger icons, values, spacing and click affordances.
- Added container-responsive layouts for narrow, standard and wide Home Assistant cards.
- Improved mobile spacing and readability without changing entity discovery or energy calculations.

## 2.2.0

- Bundled the new `custom:deyecloud-energy-flow-card` frontend card.
- Automatically serves and loads the card through the DeyeCloud integration.
- Added animated PV, battery, grid, inverter and load power-flow visualization.
- Added automatic entity discovery by `station_id` and `metric_key`.
- Added visual card editor, multi-station selection and Home Assistant 2026.6 entity suggestions.
- Added daily energy summary and live efficiency diagnostics.
- Added Vietnamese/English labels, responsive layout and light/dark theme support.
- Added normalized sensor attributes (`sensor_type`, `metric_key`, station metadata) for reliable frontend discovery.
