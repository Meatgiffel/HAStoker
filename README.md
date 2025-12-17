# HAStoker (Home Assistant custom integration)

HAStoker connects Home Assistant to your StokerCloud account and exposes your pellet boiler/furnace values as sensors.

## Features

- Adds sensors for common controller values (temperatures, power, hopper content, etc.).
- Adds an **Event log** sensor that exposes recent StokerCloud log entries as attributes (useful for automations/templates).
- Login uses your **StokerCloud username only** (no password).

## Updates / polling

- Controller data: every **30 seconds**
- Event log: every **5 minutes**

## Install (HACS)

1. Install **HACS** if you don’t already have it.
2. Go to **HACS → Integrations → (⋮) Custom repositories**.
3. Add `Meatgiffel/HAStoker` as type **Integration**.
4. Install **HAStoker** from HACS and restart Home Assistant.

## Install (manual)

1. Copy `custom_components/stokercloud` into your Home Assistant config folder as `config/custom_components/stokercloud`.
2. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **HAStoker**.
3. Enter your StokerCloud **username**.

## Notes / disclaimers

- This is an **unofficial** community integration and is not affiliated with StokerCloud.
- StokerCloud can change their service/API at any time, which may break this integration.
- This project was created with the help of **AI tools** and should be treated as best-effort; verify behavior before relying on it for safety-critical automations.
