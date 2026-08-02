# DeyeCloud Home Assistant Integration

## Repository layout

- `custom_components/deyecloud/` is the installable HACS integration.
- `__init__.py` owns config-entry setup and registration of the bundled frontend module.
- `config_flow.py` owns initial configuration and options validation. The integration stores API settings in `ConfigEntry.data`; `sensor.py` and `button.py` read from there.
- `api.py` contains API calls shared outside the sensor coordinator. `sensor.py` also contains coordinator-specific API helpers and all sensor entity creation.
- `data.py` contains Home Assistant-independent data helpers. Keep pure logic here when it can be tested without importing Home Assistant.
- `frontend/deyecloud-energy-flow-card.js` is the current Lovelace card. Versioned copies are served to bypass browser caching; the filename selected by `CARD_MODULE_URL` in `__init__.py` is the runtime artifact.
- `translations/en.json` and `translations/vi.json` must expose matching config and options keys.
- `tests/` uses the standard-library `unittest` runner and currently loads pure modules directly so Home Assistant does not need to be installed.
- `deyecloud-card.yaml` is the dashboard example. `brand/` and `custom_components/deyecloud/brand/` contain repository and integration branding.

## Development guidelines

- Preserve compatibility with the minimum Home Assistant version declared in `manifest.json` unless a release intentionally raises it.
- Use Home Assistant async APIs. Reuse `async_get_clientsession`; do not perform blocking network or file I/O in the event loop.
- Treat DeyeCloud responses as inconsistent across regions: collection fields may be `null`, IDs may use alternate keys, and dates may be strings, components, or epochs. Follow the existing normalization helpers instead of assuming one response shape.
- Keep all cloud requests bounded by a timeout. Preserve pagination and the `/device/latest` limit of ten serial numbers per request.
- Do not log access tokens, passwords, app secrets, or full credential payloads. Tests must not call the live DeyeCloud API or require real credentials.
- A failure in monthly history, daily history, station-latest data, or one station should not unnecessarily discard usable cached data from the other paths. Keep coordinator updates resilient and raise `UpdateFailed` when no meaningful refresh can be produced.
- Daily and monthly energy semantics are deliberate. In particular, do not map an undated or stale previous-day bucket into Today, and do not change `state_class`, `last_reset`, unique IDs, entity attributes, or device identifiers without considering existing Home Assistant statistics and dashboards.
- The frontend discovers sensors through `sensor_type`, `metric_key`, and `station_id` attributes. Coordinate backend attribute changes with the card.
- Keep English and Vietnamese translation structures in sync when changing config or options fields.

## Bundled frontend and releases

- The frontend has no package manager or build pipeline in this repository; it is committed as plain JavaScript.
- When changing the card, update `deyecloud-energy-flow-card.js` and the versioned file actually served by `__init__.py`. Keep those files byte-identical unless a documented release process requires otherwise.
- Frontend releases may require coordinated updates to `CARD_VERSION`, `CARD_MODULE_URL`, the frontend `CARD_VERSION`, `custom_components/deyecloud/manifest.json`, `CHANGELOG.md`, `README.md`, and `deyecloud-card.yaml`. Do not bump versions for unrelated backend-only work.
- Preserve the legacy `custom:deyecloud-energy-flow-card` custom element when introducing a new cache-busting card tag. Mutate `window.customCards` in place because Home Assistant retains a reference to that array.
- Never hand-edit binary brand assets. Replace them only from an intentional source asset.

## Validation

Run the narrowest checks relevant to the change from the repository root:

```bash
python -m unittest discover -s tests -v
python -m compileall -q custom_components/deyecloud tests
```

For frontend release changes, also confirm that the editable and served files match, substituting the filename configured in `__init__.py`:

```bash
cmp custom_components/deyecloud/frontend/deyecloud-energy-flow-card.js \
  custom_components/deyecloud/frontend/deyecloud-energy-flow-card-v225.js
```

There is no committed full Home Assistant test harness or JavaScript lint/build configuration. If a change depends on Home Assistant lifecycle behavior or card rendering, report the manual Home Assistant/browser validation still required rather than claiming local unit coverage.

## Scope and hygiene

- Keep changes focused; do not commit credentials, local Home Assistant configuration, API captures, caches, or generated Python bytecode.
- Update regression tests when changing pure data behavior, especially date selection, midnight rollover handling, stale-bucket rejection, or device batching.
- Keep user-facing setup instructions and the example card configuration aligned with behavior changes.
