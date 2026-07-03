#!/usr/bin/env python3
"""Compute SWAM host-parameter IDs from internal parameter names.

SWAM instruments (Audio Modeling) are JUCE-based plugins. JUCE derives the
VST3 parameter ID from the parameter's internal string ID using Java-style
``String.hashCode()``. This was verified empirically against the
``ParameterId`` values Ableton Live stores after exposing SWAM parameters:

    growl         ->   98629305
    flutterTongue -> 1408862784

Knowing the ID lets you address any SWAM parameter from host-side tooling
(automation, project-file generators, controller integrations) without ever
opening the plugin GUI.

Note: IDs are printed as SIGNED 32-bit integers because that is how DAW
project files (e.g. Ableton ``.als``) store them. The unsigned VST3 ParamID
is the same bit pattern (add 2**32 to negative values).

Usage:
    python3 param_id.py                     # table of common SWAM parameters
    python3 param_id.py growl overBlow ...  # specific names
"""
import sys


def vst3_param_id(name: str) -> int:
    """Java String.hashCode() of the internal parameter name (signed int32)."""
    h = 0
    for c in name:
        h = (31 * h + ord(c)) & 0xFFFFFFFF
    return h - 2**32 if h >= 2**31 else h


# Internal names as found in SWAM state XML (<PARAM id="..."> entries).
COMMON = [
    # factory-mapped controls (same CC on every SWAM Solo instrument)
    "expression", "vibratoDepth", "vibratoRate", "mainVolume", "panPot",
    "sustain", "reverbMix",
    # popular non-factory-mapped expressive controls
    "growl", "flutterTongue",          # brass
    "flutter", "overBlow",             # woodwinds
    "tremoloParam", "bowPositionParam", "exprStrResParam", "sordinoParam",  # strings
    "dynamicPitch", "muteControl", "portamentoCtrl", "portamentoTime",
]

if __name__ == "__main__":
    names = sys.argv[1:] or COMMON
    width = max(len(n) for n in names)
    for n in names:
        print(f"{n:<{width}}  {vst3_param_id(n)}")
