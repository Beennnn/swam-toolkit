#!/usr/bin/env python3
"""Sweep the installed SWAM factory presets and report every instrument's
default (factory) MIDI mapping — without opening a single plugin GUI.

Reads the base ``.nksf`` preset of each instrument under the factory folder
(macOS default: ``/Library/Application Support/Audio Modeling``), pulls the
embedded state XML out of the binary, and tabulates:

* family (Brass / Woodwinds / Strings), receive channel (17 = Omni)
* the External-Controller remap table (parameter -> CC)
* pitch-bend ranges
* whether the mapping is identical across every preset of that instrument

Output: Markdown table (default) or JSON (``--json``).

Usage:
    python3 extract_mappings.py                       # markdown to stdout
    python3 extract_mappings.py --json > mappings.json
    python3 extract_mappings.py --factory-dir "/custom/path"
"""
import argparse
import glob
import json
import os
import re

from decode_state import largest_swam_span

DEFAULT_FACTORY = "/Library/Application Support/Audio Modeling"

# order in which mapped parameters are shown
CC_COLUMNS = [
    ("expression", "Expr"), ("vibratoDepth", "VibDep"), ("vibratoRate", "VibRate"),
    ("mainVolume", "Vol"), ("panPot", "Pan"), ("sustain", "Sus"), ("reverbMix", "Rev"),
]


def parse_state(xml: str) -> dict:
    d = {}
    m = re.search(r'<swam\s+type="([^"]*)"', xml)
    d["family"] = m.group(1) if m else "?"
    m = re.search(r'id="receiveMIDIChannel" value="([\d.]+)"', xml)
    d["channel"] = int(float(m.group(1))) if m else None
    pbu = re.search(r'id="pitchBend(?:Range)?Up" value="([\-\d.]+)"', xml)
    pbd = re.search(r'id="pitchBend(?:Range)?Down" value="([\-\d.]+)"', xml)
    d["pb_up"] = int(float(pbu.group(1))) if pbu else None
    d["pb_down"] = int(float(pbd.group(1))) if pbd else None
    d["map"] = {m.group(1): int(m.group(2)) for m in re.finditer(
        r'<MIDIRemappingEntry parameterId="([^"]+)"[^>]*\bmsb="([\-\d]+)"', xml)}
    return d


def scan(factory_dir: str) -> list[dict]:
    rows = []
    for folder in sorted(os.listdir(factory_dir)):
        fpath = os.path.join(factory_dir, folder)
        if not os.path.isdir(fpath) or not folder.startswith("SWAM"):
            continue
        nksfs = sorted(glob.glob(os.path.join(fpath, "*.nksf")))
        if not nksfs:
            continue
        base = min(nksfs, key=lambda p: len(os.path.basename(p)))  # shortest name = base preset
        with open(base, "rb") as f:
            xml = largest_swam_span(f.read())
        if not xml:
            continue
        info = parse_state(xml)
        info["instrument"] = folder.replace("SWAM ", "")
        info["n_presets"] = len(nksfs)
        # is the remap table identical across all presets of this instrument?
        signatures = set()
        for n in nksfs:
            with open(n, "rb") as f:
                x = largest_swam_span(f.read())
            if x:
                signatures.add(json.dumps(parse_state(x)["map"], sort_keys=True))
        info["uniform_across_presets"] = len(signatures) == 1
        rows.append(info)
    return rows


def to_markdown(rows: list[dict]) -> str:
    out = ["| Instrument | Family | Ch | " + " | ".join(h for _, h in CC_COLUMNS)
           + " | Pitch bend | Presets |",
           "|---|---|---|" + "---|" * len(CC_COLUMNS) + "---|---|"]
    for r in sorted(rows, key=lambda z: (z["family"], z["instrument"])):
        ch = "Omni" if r["channel"] == 17 else str(r["channel"])
        ccs = " | ".join(f'CC{r["map"][pid]}' if pid in r["map"] else "—"
                         for pid, _ in CC_COLUMNS)
        pb = f'±{r["pb_up"]}/{r["pb_down"]}' if r["pb_up"] is not None else "?"
        uni = "" if r["uniform_across_presets"] else " ⚠︎varies"
        out.append(f'| {r["instrument"]} | {r["family"]} | {ch} | {ccs} | {pb} '
                   f'| {r["n_presets"]}{uni} |')
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--factory-dir", default=DEFAULT_FACTORY)
    ap.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = ap.parse_args()
    rows = scan(os.path.expanduser(args.factory_dir))
    if not rows:
        raise SystemExit(f"no SWAM factory presets found under {args.factory_dir}")
    print(json.dumps(rows, indent=1) if args.json else to_markdown(rows))
