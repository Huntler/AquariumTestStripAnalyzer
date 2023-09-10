from copy import deepcopy
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
            parsed = json.loads(text)
            self._table = parsed["table"]
            self._convert_table(parsed["type"])
        
    def _convert_table(self, _type: str) -> None:
        new_table = deepcopy(self._table)
        for key, sub_dict in self._table.items():
            colors = np.array(sub_dict["colors"])
            
            if _type == "rgb":
                r, g, b = colors[:, 0], colors[:, 1], colors[:, 2]
            
            new_table[key]["colors"] = np.array([b, g, r]).T
        
        self._table = new_table

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
    
    def _convert_hardness(self, value) -> float:
        return 1.0 * value / 10

    def analyze_strip(self, strip: TestStrip) -> Dict:
        result = {"good": {}, "low": {}, "high": {}}

        for i, color in enumerate(strip.values):
            # get the table's information
            key = self.KEY_NAMES[i]
            colors = np.array(self._table[key]["colors"])
            values = np.array(self._table[key]["values"])
            valid_range = np.array(self._table[key]["valid"])
            unit = self._table[key]["unit"]

            # find the matching entry concering the test strip
            color_diff = [self._color_distance_red_mean(color, c) for c in colors]
            closest_idx = np.argmin(color_diff)
            value = values[closest_idx]
            print(key, color_diff, color, colors[closest_idx], colors[1])

            # convert hardness
            if key in [self.KEY_NAMES[self.KH], self.KEY_NAMES[self.GH]]:
                value = self._convert_hardness(value)
                valid_range = [self._convert_hardness(v) for v in valid_range]
                unit = "°dH"

            # sort quality based on valid range
            if value < min(valid_range):
                result["low"][key] = [value, unit]
            elif value > max(valid_range):
                result["high"][key] = [value, unit]
            else:
                result["good"][key] = [value, unit]

            # print(f"key={key}, color_diff={color_diff}, index={closest_idx}, values={values}, value={values[closest_idx]}\n")

        return result