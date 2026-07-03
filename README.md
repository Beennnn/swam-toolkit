# swam-toolkit

Unofficial tooling and reverse-engineered knowledge for automating the MIDI
mapping of **SWAM instruments** (Audio Modeling) from the host side — no GUI
clicking, no per-instance MIDI-Learn.

Born from wiring a live keyboard rig (Ableton Live 12 + SWAM Solo Brass /
Woodwinds / Strings + breath controller + Stream Deck) where every finding
below was verified empirically. Python 3 standard library only.

> **Not affiliated with Audio Modeling.** Everything here was obtained by
> inspecting files installed on my own machine. No factory content is
> redistributed — the tools read *your* installed presets at runtime.

## The findings

### 1. Host parameter IDs are just a string hash

SWAM plugins are JUCE-based. The VST3 parameter ID of any SWAM parameter is
the **Java-style `String.hashCode()` of its internal name** (signed 32-bit):

```
expression        -290107779      growl              98629305
vibratoDepth      1547058706      flutterTongue    1408862784
vibratoRate       1436977715      flutter           -760334308
mainVolume        -484302104      tremoloParam     1781921569
sustain            390049837      bowPositionParam -1134376134
portamentoCtrl    1417577692      sordinoParam      -810649007
```

(regenerate anytime: `python3 param_id.py`)

Verified against the `ParameterId` values a DAW stores once the parameter is
exposed (Ableton Live 12, SWAM Trumpet 3.5.0: `growl → 98629305`,
`flutterTongue → 1408862784`). This means you can address **any** SWAM
parameter from project-file generators, controller integrations or automation
tooling without ever touching the plugin GUI. AU note: JUCE derives AU
parameter addresses from the same hash — expected identical, not yet
independently verified.

### 2. The factory MIDI map is identical across the whole SWAM Solo range

Extracted from the factory presets of 33 installed instruments
(see [docs/default-mappings.md](docs/default-mappings.md) for the full table):

| Parameter | CC | | Parameter | CC |
|---|---|---|---|---|
| Expression | **CC11** | | Pan | CC10 |
| Vibrato Depth | **CC1** | | Sustain | CC64 |
| Vibrato Rate | **CC19** | | Reverb Mix | CC90 |
| Volume | CC7 | | *(receive channel)* | **Omni** |

Only the pitch-bend range differs by family (Brass ±12, Strings ±2,
flutes ±1, reeds/saxes ±2-3). **Growl, flutter, tremolo, bow position,
portamento… are NOT factory-mapped** — that's precisely what this toolkit
lets you automate, either plugin-side (`.swamec`) or host-side (parameter
IDs above).

### 3. The state containers are all the same XML

SWAM's full state — sound-engine values, MIDI mapping, micro-tuning — is one
plain XML document (`<swam …> … </swam>`) wrapped in different containers:
raw inside factory `.nksf` presets, JUCE-custom-base64 inside
`~/Library/Application Support/SWAM *.settings`, hex inside DAW project
plugin-state blobs. `decode_state.py` unwraps all of them.

### 4. `.swamec` files are plain XML too — and one file covers a family

The *External Controller Mapping* export/import format is the `<midimapping>`
section of that same XML. One file imports into any instrument of the same
family (per Audio Modeling), so **three generated files cover an entire SWAM
Solo collection** — 1-click import per instance instead of MIDI-Learn per
parameter. Import path in the plugin: main menu **… → Controller Mapping →
Import**. Verified on SWAM Trumpet v3.5.0 / Ableton Live 12.

## The tools

| Script | What it does |
|---|---|
| `param_id.py` | internal parameter name → host (VST3) parameter ID |
| `extract_mappings.py` | sweep installed factory presets → full default-mapping table (Markdown/JSON) |
| `decode_state.py` | extract the state XML from `.settings` / `.nksf` / raw blobs |
| `gen_swamec.py` | generate per-family `.swamec` files: factory table + your extra CCs |

```bash
# what does my installed collection map by default?
python3 extract_mappings.py

# what's the VST3 param ID of the sax growl?
python3 param_id.py growl

# build Brass/Woodwinds/Strings .swamec adding growl→CC12, flutter→CC13, …
python3 gen_swamec.py --out ./swamec
```

Default factory path is the macOS one
(`/Library/Application Support/Audio Modeling`) — use `--factory-dir` on
Windows (untested there; reports welcome).

## Verification status

| Claim | Status |
|---|---|
| param-name hash = VST3 ParameterId | ✅ verified (Live 12 + SWAM Trumpet 3.5.0, 2 params) |
| factory map identical across 33 instruments | ✅ verified by extraction on my install |
| `.swamec` import accepts generated files | ✅ verified (Trumpet 3.5.0, "Import Succeeded" + table inspected) |
| same hash for AU parameter addresses | ⚠️ expected (JUCE), not yet verified |
| Windows factory paths | ⚠️ untested |

## Discussion

Announcement thread (feedback / AU + Windows reports welcome):
[KVR Audio — Instruments forum](https://www.kvraudio.com/forum/viewtopic.php?t=631399).

## Credits

Built by Benoît Besson in an AI-assisted workflow: a substantial part of the
reverse engineering, tooling and documentation was produced together with
[Claude](https://claude.com/claude-code) (Anthropic). All empirical
verification ran against real installs and a real live rig.

## License

MIT — see [LICENSE](LICENSE). Provided as-is; SWAM and the `.swamec`/`.nksf`
formats belong to Audio Modeling and are undocumented, so any update may
change them.

## See also

* [als-wire](https://github.com/Beennnn/als-wire) — companion project: batch-wire
  plugin parameters (by these very IDs) to Ableton rack macros and MIDI
  mappings directly in `.als` files.
