from copy import deepcopy
import math
import os, json
import cv2
import numpy as np
from typing import Dict, Tuple

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

            hsv_converted = []
            for i in range(len(colors)):
                H, S, V = self._rgb_to_hsv(r[i], g[i], b[i])
                hsv_converted.append([H, S, V])
            
            new_table[key]["colors"] = hsv_converted
        
        self._table = new_table
    
    def _rgb_to_hsv(self, r: int, g: int, b: int) -> Tuple[float]:
        _r = 1.0 * r / 255
        _g = 1.0 * g / 255
        _b = 1.0 * b / 255

        c_max = max(_r, _g, _b)
        c_min = min(_r, _g, _b)

        delta = c_max - c_min

        H = 0
        if c_max == _r:
            H = 60 * (((_g - _b) / delta) % 6)
        elif c_max == _g:
            H = 60 * ((_b - _r) / delta + 2)
        elif c_max == _b:
            H = 60 * ((_r - _g) / delta + 4)

        S = 0
        if c_max != 0:
            S = delta / c_max

        V = c_max

        return H, S, V

    def _color_distance(self, color_a, reference: Tuple[float]) -> float:
        # method from https://www.compuphase.com/cmetric.html
        # image in BGR format
        H1, S1, V1 = self._rgb_to_hsv(color_a[2], color_a[1], color_a[0])
        H2, S2, V2 = reference

        hue_distance = 1.0 * min(abs(H2 - H1), 360 - abs(H2 - H1)) / 180
        saturation_distance = abs(S2 - S1)
        value_distance = 1.0 * abs(V2 - V1) / 255

        return math.sqrt(hue_distance**2 + saturation_distance**2 + value_distance**2)

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
            color_diff = [self._color_distance(color, c) for c in colors]
            closest_idx = np.argmin(color_diff)
            value = values[closest_idx]

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