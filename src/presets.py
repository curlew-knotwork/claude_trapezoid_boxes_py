"""
presets.py — Named presets for both modes.

A preset is a dict with keys matching CommonConfig and mode-specific config field names,
plus 'mode': str and 'description': str. Omitted keys use dataclass defaults.
"""
from __future__ import annotations

PRESETS: dict[str, dict] = {
    'pencil-box': {
        'mode': 'box',
        'description': 'Small open-top box. Good first project for students.',
        'common': {'long': 220.0, 'short': 30.0, 'length': 200.0, 'depth': 25.0, 'thickness': 3.0},
        'box':    {'lid': 'none'},
    },
    'storage-box': {
        'mode': 'box',
        'description': 'Medium box with lift-off lid.',
        'common': {'long': 200.0, 'short': 150.0, 'length': 300.0, 'depth': 80.0, 'thickness': 3.0},
        'box':    {'lid': 'lift-off'},
    },
    'sliding-box': {
        'mode': 'box',
        'description': 'Compact box with sliding lid. Demonstrates sliding lid joint.',
        'common': {'long': 160.0, 'short': 120.0, 'length': 200.0, 'depth': 40.0, 'thickness': 3.0},
        'box':    {'lid': 'sliding'},
    },
    'dulcimer': {
        'mode': 'instrument',
        'description': 'Dulcimer instrument body. long=180, short=120, length=380, depth=90, T=3mm. Rounded-trapezoid soundhole, hardware, kerfing.',
        'common':     {'long': 180.0, 'short': 120.0, 'length': 380.0, 'depth': 90.0, 'thickness': 3.0},
        'instrument': {'soundhole_type': 'rounded-trapezoid', 'soundhole_aspect': 0.6, 'hardware': True, 'kerfing': True},
    },
    'tenor-guitar': {
        'mode': 'instrument',
        'description': 'Tenor guitar body. Scaled-up dulcimer at tenor guitar proportions.',
        'common':     {'long': 280.0, 'short': 200.0, 'length': 480.0, 'depth': 100.0, 'thickness': 3.0},
        'instrument': {'soundhole_type': 'rounded-trapezoid', 'soundhole_aspect': 0.6, 'hardware': True, 'kerfing': True, 'helmholtz_freq': 82.4},
    },
}


def list_presets() -> None:
    print('Available presets:')
    for name, preset in PRESETS.items():
        mode = preset['mode']
        desc = preset['description']
        print(f'  {name:20s} [{mode:10s}] {desc}')


def get_preset(name: str) -> dict:
    if name not in PRESETS:
        raise KeyError(f"Unknown preset '{name}'. Use --list-presets to see available presets.")
    return PRESETS[name]
