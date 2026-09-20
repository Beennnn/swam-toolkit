# swam-toolkit

**Address any SWAM parameter from the host side, and generate the `.swamec` files that
map the ones the factory leaves unmapped — no GUI clicking, no per-instance MIDI-Learn.**

```console
$ python3 param_id.py growl
growl  98629305

$ python3 extract_mappings.py
| Instrument | Family | Ch | Expr | VibDep | VibRate | Vol | Pan | Sus | Rev | Pitch bend | Presets |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Trumpet | Brass | Omni | CC11 | CC1 | CC19 | CC7 | CC10 | CC64 | CC90 | ±12/12 | 7 |
| Tenor Sax 3 | Woodwinds | Omni | CC11 | CC1 | CC19 | CC7 | CC10 | CC64 | CC90 | ±2/3 | 6 |
| Violin 3 | Strings | Omni | CC11 | CC1 | CC19 | CC7 | CC10 | CC64 | CC90 | ±2/2 | 7 |
…

$ python3 gen_swamec.py --out ./swamec      # Brass / Woodwinds / Strings, factory table + your extra CCs
```

> **Not affiliated with Audio Modeling.** Everything here was obtained by inspecting files
> installed on my own machine. No factory content is redistributed — the tools read *your*
> installed presets at runtime.

## What it's for

Growl, flutter, tremolo, bow position and portamento are **not** factory-mapped on any
SWAM instrument, so exposing them means MIDI-Learn, per parameter, per instance — and
again for every new project. Two findings remove that: the host parameter ID of any SWAM
parameter is just a hash of its internal name, and a `.swamec` mapping file is plain XML
that imports into any instrument of the same family.

## The tools

| Script | What it does |
|---|---|
| `param_id.py` | internal parameter name → host (VST3) parameter ID |
| `extract_mappings.py` | sweep installed factory presets → full default-mapping table (Markdown/JSON) |
| `decode_state.py` | extract the state XML from `.settings` / `.nksf` / raw blobs |
| `gen_swamec.py` | generate per-family `.swamec` files: factory table + your extra CCs |

Python 3, standard library only. The default factory path is the macOS one
(`/Library/Application Support/Audio Modeling`) — use `--factory-dir` on Windows (untested
there; reports welcome).

## Parameter IDs

SWAM plugins are JUCE-based, and JUCE derives the VST3 parameter ID from the parameter's
internal name via Java's `String.hashCode()` (signed 32-bit). `param_id.py` with no
argument prints the common ones:

```console
$ python3 param_id.py expression growl vibratoDepth flutterTongue tremoloParam bowPositionParam
expression        -1795452264
growl             98629305
vibratoDepth      1044572362
flutterTongue     1408862784
tremoloParam      1781921569
bowPositionParam  -1134376134
```

⚠️ For a few parameters the **state** name and the **exposed automation** name diverge, so
derive IDs for those from the exposed parameter list rather than from state names — see
[docs/reverse-engineering.md](docs/reverse-engineering.md#caveat--state-names-vs-exposed-automation-names).

## What was established, and how sure

The four findings behind these tools — the ID hash, the factory map being identical across
the whole SWAM Solo range, the shared XML state container, and the `.swamec` format — are
written up with their evidence in **[docs/reverse-engineering.md](docs/reverse-engineering.md)**, alongside a
verification-status table that says plainly which claims were measured and which are
untested. The full extracted factory table for 33 instruments is in
[docs/default-mappings.md](docs/default-mappings.md).

## Discussion

Announcement thread (feedback / AU + Windows reports welcome):
[KVR Audio — Instruments forum](https://www.kvraudio.com/forum/viewtopic.php?t=631399).

## Credits

Built by Benoît Besson in an AI-assisted workflow: a substantial part of the reverse
engineering, tooling and documentation was produced together with
[Claude](https://claude.com/claude-code) (Anthropic). All empirical verification ran
against real installs and a real live rig.

## License

MIT — see [LICENSE](LICENSE). Provided as-is; SWAM and the `.swamec`/`.nksf` formats belong
to Audio Modeling and are undocumented, so any update may change them.

## See also

[als-wire](https://github.com/Beennnn/ableton-als-wire) — companion project: batch-wire plugin
parameters (by these very IDs) to Ableton rack macros and MIDI mappings directly in `.als`
files.
