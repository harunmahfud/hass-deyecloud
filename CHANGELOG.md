# Changelog

## 2.2.4

- Fixed the generic Home Assistant `Configuration error` card.
- Made `setConfig()` tolerant of empty/incomplete card-picker configuration.
- Added cache-safe card type `custom:deyecloud-energy-flow-card-v2`.
- Added backward compatibility for `custom:deyecloud-energy-flow-card`.
- Added a uniquely versioned JavaScript filename so older Custom Elements cannot remain active after an update.
- Removed stale card-picker metadata from previous releases.

## 2.2.3

- Fixed the frontend resource cache key still using `v=2.2.1`.
- Disabled long-lived HTTP caching for the bundled development resource path.
- Disabled live card-picker preview to prevent `Custom element not found` race errors.
- Replaces stale `window.customCards` metadata entries when a newer card version loads.
- Registers the frontend resource from both integration setup paths for improved reliability.
- Added the exact registered module URL to the Home Assistant log.

## 2.2.2

- Redesigned the realtime diagram section with a cleaner, more spacious layout.
- Reduced visual crowding between Solar, Battery, Inverter, Grid and Home nodes.
- Made node cards larger and easier to read in narrow dashboard columns.
- Showed line power badges only when a power flow is active to reduce clutter.
- Fixed intermittent card render errors by hardening language detection and adding render error fallback.
- Replaced the `hass-more-info` event with `CustomEvent` for better compatibility.
- Added a safe in-card error state instead of a broken card when runtime issues occur.

# Changelog

## 2.2.0

- Bundled the new `custom:deyecloud-energy-flow-card` frontend card.
- Automatically serves and loads the card through the DeyeCloud integration.
- Added animated PV, battery, grid, inverter and load power-flow visualization.
- Added automatic entity discovery by `station_id` and `metric_key`.
- Added visual card editor, multi-station selection and Home Assistant 2026.6 entity suggestions.
- Added daily energy summary and live efficiency diagnostics.
- Added Vietnamese/English labels, responsive layout and light/dark theme support.
- Added normalized sensor attributes (`sensor_type`, `metric_key`, station metadata) for reliable frontend discovery.
