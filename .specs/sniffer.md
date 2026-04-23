# Sniffer / Listener Mode

## Goal

Discover and capture UART messages sent by the hardware device for property IDs that have no registered listener, so unknown properties can be identified and mapped for future use.

---

## Behaviour

### Passive capture

When a message arrives for a property ID that no component has registered interest in, it is captured and recorded. Registered components (e.g. fan controls) are unaffected and continue to work normally.

### Active scan mode

An optional mode that can be toggled on and off by the user.

**When turned on:**
- Regular polling stops completely. Any tasks that were already queued (e.g. pending fan SET commands) are discarded at this point.
- Registered component listeners stop receiving updates.
- The sniffer iterates through a configured range of property IDs, querying them one at a time. The next query is only issued after a response (or timeout) for the previous one has been processed.
- Property IDs that already have registered listeners are silently skipped — they are not queried and do not appear in the output.

**When turned off:**
- Scanning stops immediately. The last queried ID is saved.
- Regular polling resumes at once, without waiting for the next scheduled poll cycle.

**Resume behaviour:** turning scan mode back on continues from the saved position. If the previous scan completed the full range, the next run restarts from the beginning.

---

## Recorded data

For each discovered property ID the sniffer stores:
- The property ID.
- The command type of the message (so responses to read requests can be distinguished from write notifications).
- The last seen value.
- The timestamp of the last update.

The timestamp uses the real-time clock when available; otherwise it falls back to device uptime.

---

## Outputs

- **Text sensor**: publishes the recorded entries as a comma-separated string in `id=value` format (e.g. `1=23, 2=13, 5=100`). The command type and timestamp are omitted from the sensor value but are still logged at `[I]` level for every discovery.
  - **During active scan**: the sensor is not updated while the scan is running. A single publish happens when the scan finishes (normally or when manually stopped mid-scan).
  - **In passive mode**: the sensor is updated on every new or changed entry, as before.
  - Duplicate messages that carry no new information never trigger a publish. The output is capped at 2048 characters (`MAX_STATE_LEN` in `sec_touch_sniffer.h`); entries beyond the cap are replaced with `...`.
- **Switch** (optional): reflects whether scan mode is currently active and can be toggled from Home Assistant.

---

## Configuration

- The scan range (start and end ID) is configurable. `scan_start` must be ≤ `scan_end`; an invalid range is rejected at config validation time. If no range is configured, active scan mode is disabled and only passive capture is available.
- The real-time clock source is optional.
- The switch for scan state is optional.

---

## User interaction

A toggle switch switches scan mode on or off. No other interaction is required; the sniffer advances through IDs automatically and exits scan mode on its own when the range is exhausted.

---

## Implementation notes

### GET response protocol
The SEC-Touch device responds to a GET request with two separate messages:
1. `[STX][ACK][ETX]` — confirms receipt of the request
2. `[STX]32[TAB]property_id[TAB]value[TAB]crc[ETX]` — the actual data

For unknown or unsupported property IDs the device sends `[STX][NAK][ETX]` instead of the data message. The component treats NAK as a failed task and advances the scan to the next ID.

Some property values are space-padded to a fixed width (e.g. `"00               "`). This makes the data message longer than the typical case and may cause it to arrive split across multiple UART read cycles. The `loop()` function handles this by buffering partial messages across calls and only processing once ETX is received.

The component keeps the task in `GET_DATA` state after receiving the ACK so that the queue-empty callback (which drives scan advancement) cannot fire before the data/NAK message arrives.

### Scan timeout and retry
When a scan task receives no response within `TASK_TIMEOUT_MS` (2 s), the watchdog fires and the sniffer waits **5 seconds** before retrying that property ID once. If the retry also times out, the ID is logged as unresponsive and the scan advances to the next one immediately (no further wait).

The watchdog check runs regardless of whether the task queue is empty. Tasks are popped from the queue when dispatched, so the queue is empty while waiting for a response — the check must happen unconditionally in `loop()`, not inside the queue-empty guard.

If the user stops the scan during the 5-second retry wait, the pending retry is cancelled and normal polling resumes immediately.

### Text sensor state and MQTT
The text sensor publishes a compact `id=value` list on scan completion (or manual stop). With a full scan (200+ IDs) the state string can exceed 1600 characters. If MQTT is used instead of the native API, the broker's `max_packet_size` must be set to at least 4096 bytes — Mosquitto defaults to 256 bytes and will silently drop larger publishes, causing HA to show "unknown". The ESPHome native API has no such limit.

Note: discovered state is held in RAM only. After a device restart or firmware flash the state is lost and the scan must be re-run.

### Memory on constrained hardware
`discovered_ids_` is an `std::map` that grows with the number of responsive property IDs found. Each entry takes ~80–100 bytes on the heap (red-black tree node + `SniffedEntry`). A scan that discovers 200 IDs uses roughly 20 KB — safe on ESP32 (~300 KB free heap) but **not recommended on ESP8266** (~40 KB usable heap). Keep scan ranges very modest on ESP8266, or avoid active scan entirely.


1. With scan mode disabled, captured unknown IDs appear in the text sensor output and do not interfere with existing controls.
2. Turning scan mode on stops normal polling and listener updates; the text sensor populates with discovered IDs across the configured range.
3. Turning scan mode off mid-scan resumes normal polling immediately; the saved position is used when scan mode is turned on again.
4. When scan mode runs to completion, polling resumes automatically and the binary sensor reflects the off state.
5. IDs with registered listeners do not appear in passive capture output, but do appear in scan mode output.
