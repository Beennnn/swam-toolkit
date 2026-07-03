#!/usr/bin/env python3
"""Generate ``.swamec`` (External Controller Mapping) files for SWAM instruments.

A ``.swamec`` is the plain-XML mapping file SWAM exports/imports from
*main menu (…) -> Controller Mapping -> Import*. Audio Modeling confirms one
file is valid for any instrument of the same family — so three files
(Brass / Woodwinds / Strings) can cover an entire SWAM Solo collection.

This tool builds each family file from the factory mapping of an *anchor*
instrument you own (read from its ``.nksf``), keeps the factory table intact,
and appends the extra CC assignments you configure (growl, flutter, …).

Import was verified working on SWAM Trumpet v3.5.0 (VST3, Ableton Live 12).

Caveats:
* The file also carries the anchor's MIDI options (transpose, pitch-bend
  range…). After importing into a *different* instrument of the family, play
  one note and check the octave; fix Transpose in the options if needed.
* Don't combine plugin-side CC mappings with host-side control of the SAME
  CCs (double-driving: SWAM listens Omni).

Usage:
    python3 gen_swamec.py --out ./swamec              # default config
    python3 gen_swamec.py --config my_rig.json --out ./swamec
"""
import argparse
import json
import os
import re
import time

from decode_state import largest_swam_span

DEFAULT_FACTORY = "/Library/Application Support/Audio Modeling"

# family -> anchor instrument folder + {internal param name: CC number}
DEFAULT_CONFIG = {
    "Brass": {
        "anchor": "SWAM Trumpet",
        "additions": {"growl": 12, "flutterTongue": 13, "dynamicPitch": 8,
                      "muteControl": 9, "portamentoCtrl": 65},
    },
    "Woodwinds": {
        "anchor": "SWAM Tenor Sax 3",
        "additions": {"growl": 12, "flutter": 13, "dynamicPitch": 8,
                      "overBlow": 9, "portamentoCtrl": 65},
    },
    "Strings": {
        "anchor": "SWAM Violin 3",
        "additions": {"tremoloParam": 12, "bowPositionParam": 13,
                      "exprStrResParam": 8, "sordinoParam": 9, "portamentoCtrl": 65},
    },
}


def entry(param_id: str, cc: int) -> str:
    return (f'        <MIDIRemappingEntry parameterId="{param_id}" channel="17" '
            f'messageType="1" msb="{cc}"\n'
            f'                            lsb="-1" pickup="0" midiInputMode="0">\n'
            f'          <MIDIRemappingCurve input_min="0.0" input_max="127.0" '
            f'out_min="0.0" out_max="127.0"\n'
            f'                              shape="0.0" symmetry="0.5" bypass="0" '
            f'bipolar="0"/>\n'
            f'        </MIDIRemappingEntry>\n')


def build(family: str, spec: dict, factory_dir: str, out_dir: str) -> str:
    folder = os.path.join(factory_dir, spec["anchor"])
    nksfs = sorted(f for f in os.listdir(folder) if f.endswith(".nksf"))
    if not nksfs:
        raise SystemExit(f"{family}: no .nksf under {folder}")
    anchor = os.path.join(folder, min(nksfs, key=len))
    with open(anchor, "rb") as f:
        xml = largest_swam_span(f.read())
    prog_name = f"{family} Custom"
    xml = re.sub(r'(<program\s+name=")[^"]*(")', rf"\g<1>{prog_name}\g<2>", xml, count=1)
    head = re.search(r"<swam[^>]*>", xml).group(0)
    if "<datetime" not in xml:
        now = time.strftime("%a %b %e %H:%M:%S %Y")
        xml = xml.replace(head, head + f'\n  <datetime value="{now}&#10;"/>', 1)
    for pid, cc in spec["additions"].items():
        if f'parameterId="{pid}"' in xml:
            raise SystemExit(f"{family}: {pid} is already mapped in the factory table")
        xml = xml.replace("</MIDIRemappingTable>",
                          entry(pid, cc) + "      </MIDIRemappingTable>", 1)
    out = os.path.join(out_dir, f"{prog_name}.swamec")
    with open(out, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n\n' + xml + "\n")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--factory-dir", default=DEFAULT_FACTORY)
    ap.add_argument("--config", help="JSON file overriding the default family config")
    ap.add_argument("--out", default=".", help="output directory")
    args = ap.parse_args()
    cfg = DEFAULT_CONFIG
    if args.config:
        with open(args.config) as f:
            cfg = json.load(f)
    os.makedirs(args.out, exist_ok=True)
    for family, spec in cfg.items():
        path = build(family, spec, os.path.expanduser(args.factory_dir), args.out)
        adds = ", ".join(f"{p}→CC{cc}" for p, cc in spec["additions"].items())
        print(f"[{family}] {path}  ({adds})")
