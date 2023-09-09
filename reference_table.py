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

    def analyze_strip(self, strip: TestStrip) -> Dict:
        result = {}
        for i, color in enumerate(strip.values):
            key = self.KEY_NAMES[i]
            colors = np.array(self._table[key]["colors"])
            values = np.array(self._table[key]["values"])

            closest_idx = np.argmin(np.abs(np.mean(colors - color, axis = -1)))
            result[key] = values[closest_idx]

        return result