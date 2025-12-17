# HAStoker Home Assistant integration (custom component)

Connects to `stokercloud.dk` using a username and exposes pellet furnace values as sensors.

## What this integration does

- Logs in to StokerCloud using your **username only** (no password is required by StokerCloud for this API).
- Polls controller data and exposes the values as HA sensor entities.
- Polls the StokerCloud **event log** and stores the returned log entries in an entity attribute so you can use them in templates/automations.

## Data sources (StokerCloud endpoints)

This integration talks to the same endpoints as the StokerCloud web UI:

- Login/token: `https://stokercloud.dk/v2/dataout2/login.php?user=<username>`
- Controller data: `https://stokercloud.dk/v2/dataout2/controllerdata2.php?screen=<screen>&token=<token>`
- Event log: `https://stokercloud.dk/v2/dataout2/geteventdata.php?count=<count>&offset=<offset>&token=<token>`
- UI translations (used for optional event text mapping): `https://stokercloud.dk/v3/assets/json/translation/uk.json`

The token is kept in memory and refreshed automatically when it expires.

## Event log

The integration exposes an **Event log** sensor:

- **State**: number of events returned in the last poll.
- **Attributes**:
  - `events`: list of event objects (dictionaries) as returned by StokerCloud (may be truncated to fit Home Assistant attribute size limits).
  - `events_total`: total number of event objects before truncation.
  - `events_truncated`: `true` if the `events` list was shortened to stay under HA’s attribute size limits.
  - `count`: the requested count (default `100`).
  - `offset`: the requested offset (default `0`).
  - `translation_language`: translation language used for mapping (default `uk`).
  - `translations_loaded`: `true` if the translation file was successfully downloaded.

### Translation mapping

StokerCloud’s event payload sometimes contains string values that are actually translation keys (similar to the web UI). On each event object, if a string value matches a key in the downloaded translation JSON, this integration adds an extra field named `<original_field>_translated` with the translated text.

Example (conceptual):

- If an event contains `{ "message": "lng_info_1" }` and `uk.json` contains `"lng_info_1": "Info: Low boiler temperature, danger of freezing"`,
  the integration adds `{ "message_translated": "Info: Low boiler temperature, danger of freezing" }`.

### Update interval

- Controller data is updated every 30 seconds.
- Event log is updated every 5 minutes (to reduce API load; the log can be large and changes less frequently).

## Install (manual)

1. Copy `custom_components/stokercloud` into your Home Assistant `config/custom_components/`.
2. Restart Home Assistant.
3. Add **HAStoker** via **Settings → Devices & services → Add integration**.

## Install (HACS)

1. Ensure you have **HACS** installed in Home Assistant.
2. In **HACS → Integrations → (⋮) Custom repositories**, add this GitHub repo as type **Integration**.
3. Install **HAStoker** from HACS.
4. Restart Home Assistant.
5. Add **HAStoker** via **Settings → Devices & services → Add integration**.

## Using the event log in HA

In templates/automations/scripts, you can access the event list from the sensor attributes.

Examples:

- Number of events returned:
  - `{{ states('sensor.<your_device>_event_log') }}`
- Full events list:
  - `{{ state_attr('sensor.<your_device>_event_log', 'events') }}`
- First event (if any):
  - `{{ (state_attr('sensor.<your_device>_event_log', 'events') or [])[0] }}`

Tip: the exact `entity_id` depends on your HA naming, but the entity name shown in the UI is **Event log** under the StokerCloud device.

## Troubleshooting

- If you see “Token expired” errors, the integration should automatically re-login and recover.
- If the Event log sensor exists but has no attributes, check HA logs for connectivity issues.
- If `events_truncated` is `true`, reduce the amount of data you use in templates (use just the first N events) or rely on specific fields rather than the full list.
