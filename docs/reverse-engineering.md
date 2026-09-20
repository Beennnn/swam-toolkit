# What was established about SWAM, and how

Unofficial, reverse-engineered knowledge about **SWAM instruments** (Audio Modeling),
obtained by inspecting files installed on my own machine. Born from wiring a live keyboard
rig (Ableton Live 12 + SWAM Solo Brass / Woodwinds / Strings + breath controller + Stream
Deck), where every finding below was verified empirically.

**Not affiliated with Audio Modeling.** No factory content is redistributed — the tools in
this repository read *your* installed presets at runtime.

## 1. Host parameter IDs are just a string hash

SWAM plugins are JUCE-based. The VST3 parameter ID of any SWAM parameter is the
**Java-style `String.hashCode()` of its internal name** (signed 32-bit). Run
`python3 param_id.py` with no argument for the table, or pass names of your own.

Verified against the `ParameterId` values a DAW stores once the parameter is exposed
(Ableton Live 12, SWAM Trumpet 3.5.0: `growl → 98629305`,
`flutterTongue → 1408862784`). This means you can address **any** SWAM parameter from
project-file generators, controller integrations or automation tooling without ever
touching the plugin GUI.

**AU note:** the AU builds use the **same scheme** — `AudioUnitParameterID` = the unsigned
hashCode of the internal name. Verified with `auval` (`auval -v aumu Svl3 AuMo`): 56
internal names matched their reported parameter IDs exactly (tremoloParam, portamentoCtrl,
bowForceParam, exprStrResParam, accStyle, harmonicsParam, …).

IDs are printed as **signed** 32-bit integers because that is how DAW project files (e.g.
Ableton `.als`) store them. The unsigned VST3 ParamID is the same bit pattern — add 2³² to
a negative value.

### Caveat — state names vs exposed-automation names

A parameter's id string in the `.nksf` / state XML is *usually* identical to the exposed
automation parameter's id, but not always. A few diverge: the state calls bow position
`bowPositionParam`, while the exposed automation parameter hashes from a different id
(auval "Bow/Pizz Position" = 1013107514, not `hash("bowPositionParam")`); same for
`sordinoParam` vs the exposed "Sordino" (1336834641).

For robust host wiring, derive IDs from the **exposed** parameter list (auval for AU) for
those few params, not from state names.

## 2. The factory MIDI map is identical across the whole SWAM Solo range

Extracted from the factory presets of 33 installed instruments — the full table is in
[default-mappings.md](default-mappings.md), and `extract_mappings.py` regenerates it from
your own install.

| Parameter | CC | | Parameter | CC |
|---|---|---|---|---|
| Expression | **CC11** | | Pan | CC10 |
| Vibrato Depth | **CC1** | | Sustain | CC64 |
| Vibrato Rate | **CC19** | | Reverb Mix | CC90 |
| Volume | CC7 | | *(receive channel)* | **Omni** |

Only the pitch-bend range differs by family (Brass ±12, Strings ±2, flutes ±1, reeds and
saxes ±2–3). **Growl, flutter, tremolo, bow position, portamento… are NOT factory-mapped**
— that is precisely what this toolkit lets you automate, either plugin-side (`.swamec`) or
host-side (parameter IDs above).

## 3. The state containers are all the same XML

SWAM's full state — sound-engine values, MIDI mapping, micro-tuning — is one plain XML
document (`<swam …> … </swam>`) wrapped in different containers: raw inside factory
`.nksf` presets, JUCE-custom-base64 inside `~/Library/Application Support/SWAM *.settings`,
hex inside DAW project plugin-state blobs. `decode_state.py` unwraps all of them.

## 4. `.swamec` files are plain XML too — and one file covers a family

The *External Controller Mapping* export/import format is the `<midimapping>` section of
that same XML. One file imports into any instrument of the same family (per Audio
Modeling), so **three generated files cover an entire SWAM Solo collection** — one import
click per instance instead of MIDI-Learn per parameter. Import path in the plugin: main
menu **… → Controller Mapping → Import**. Verified on SWAM Trumpet v3.5.0 / Ableton Live
12.

`gen_swamec.py` builds each family file from the factory mapping of an *anchor* instrument
you own (read from its `.nksf`), keeps the factory table intact, and appends the extra CC
assignments you configure. Two caveats it carries:

* The file also carries the anchor's MIDI options (transpose, pitch-bend range…). After
  importing into a *different* instrument of the family, play one note and check the
  octave; fix Transpose in the options if needed.
* Don't combine plugin-side CC mappings with host-side control of the **same** CCs —
  double-driving, since SWAM listens Omni.

## Verification status

| Claim | Status |
|---|---|
| param-name hash = VST3 ParameterId | ✅ verified (Live 12 + SWAM Trumpet 3.5.0, 2 params) |
| factory map identical across 33 instruments | ✅ verified by extraction on my install |
| `.swamec` import accepts generated files | ✅ verified (Trumpet 3.5.0, "Import Succeeded" + table inspected) |
| same hash for AU parameter addresses | ✅ verified via `auval` (56 internal names matched their reported AU parameter IDs) |
| state param name == exposed automation name | ⚠️ usually, but a few diverge (bowPositionParam, sordinoParam) — see the caveat above |
| Windows factory paths | ⚠️ untested |
