#!/usr/bin/env python3
"""Extract the embedded SWAM state XML from the containers SWAM uses on disk.

SWAM's full state (sound-engine values, MIDI mapping, micro-tuning) is a plain
XML document (``<swam ...> ... </swam>``, magic ``VC2!`` when wrapped) that
hides inside several containers:

* ``*.settings`` files (``~/Library/Application Support/SWAM *.settings``):
  a JUCE PropertiesFile whose ``filterState`` value is a JUCE MemoryBlock in
  JUCE's *custom* base64 (charset ``.A-Za-z0-9+``, bits packed LSB-first,
  ``<size>.`` prefix) — not standard base64.
* ``*.nksf`` factory presets (``/Library/Application Support/Audio Modeling/
  <Instrument>/``): the XML sits raw inside the binary.
* DAW-side plugin state (e.g. the hex ``ProcessorState`` blob in an Ableton
  ``.als``): same raw XML once un-hexed.

This tool auto-detects the container and prints the XML to stdout.

Usage:
    python3 decode_state.py "~/Library/Application Support/SWAM Violin 3.settings"
    python3 decode_state.py "/Library/Application Support/Audio Modeling/SWAM Trumpet/Trumpet.nksf"
"""
import os
import re
import sys

JUCE_CHARSET = ".ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+"
_IDX = {c: i for i, c in enumerate(JUCE_CHARSET)}


def juce_base64_decode(blob: str) -> bytes:
    """Decode JUCE MemoryBlock::toBase64Encoding() ("<size>." + custom charset)."""
    size_str, _, data = blob.partition(".")
    size = int(size_str)
    out = bytearray(size)
    bit = 0
    for ch in data:
        idx = _IDX.get(ch)
        if idx is None:
            continue
        for k in range(6):
            if idx & (1 << k):
                byte = bit >> 3
                if byte < size:
                    out[byte] |= 1 << (bit & 7)
            bit += 1
    return bytes(out)


def largest_swam_span(raw: bytes) -> str | None:
    """Return the largest <swam ...>...</swam> span found in a binary blob."""
    best = None
    for m in re.finditer(rb"<swam\b", raw):
        end = raw.find(b"</swam>", m.start())
        if end == -1:
            continue
        span = raw[m.start():end + 7]
        if best is None or len(span) > len(best):
            best = span
    return best.decode("utf-8", "replace") if best else None


def extract(path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    # .settings container? decode the filterState JUCE-base64 first
    if b'name="filterState"' in data:
        m = re.search(rb'name="filterState"\s+val="([^"]+)"', data)
        if not m:
            raise SystemExit("filterState introuvable dans ce .settings")
        data = juce_base64_decode(m.group(1).decode("ascii"))
    xml = largest_swam_span(data)
    if xml is None:
        raise SystemExit("aucun bloc <swam>...</swam> trouvé dans ce fichier")
    return xml


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(extract(os.path.expanduser(sys.argv[1])))
