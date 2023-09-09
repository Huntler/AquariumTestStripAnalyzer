import os, json
import numpy as np
from typing import Dict

from test_strip import TestStrip


class ReferenceTable:
    KEY_NAMES = [
        "iron",
        "copper",
        "nitrate",
        "nitrite",
        "chlorine",
        "GH",
        "alkalinity",
        "KH",
        "pH",
    ]

    IRON, COPPER, NITRATE, NITRITE, CHLORINE, GH, ALKALINITY, KH, PH = range(9)

    def __init__(self, path: str = "data/reference/reference.json") -> None:
        self._table = {}
        
        self._load_table_from_file(path)

    def _load_table_from_file(self, path: str) -> Dict:
        with open(path, "rb") as file:
            text = file.read()
            self._table = json.loads(text)

    def _color_distance_red_mean(self, color_a, color_b) -> float:
        # method from https://www.compuphase.com/cmetric.html
        # image in BGR format
        b1, g1, r1 = color_a[0], color_a[1], color_a[2]
        b2, g2, r2 = color_b[0], color_b[1], color_b[2]

        red_mean = int(round((r1 + r2) / 2))
        r = int(r1 - r2)
        g = int(g1 - g2)
        b = int(b1 - b2)

        return (((512 + red_mean) * r * r) >> 8) + 4 * g * g + (((767 - red_mean) * b * b) >> 8)

    def analyze_strip(self, strip: TestStrip) -> Dict:
        result = {}
        for i, color in enumerate(strip.values):
            key = self.KEY_NAMES[i]
            colors = np.array(self._table[key]["colors"])
            values = np.array(self._table[key]["values"])

            color_diff = [self._color_distance_red_mean(color, c) for c in colors]
            closest_idx = np.argmin(color_diff)
            result[key] = values[closest_idx]

            # print(f"key={key}, color_diff={color_diff}, index={closest_idx}, values={values}, value={values[closest_idx]}\n")

        return result