import cv2
import numpy as np
from image_process import strip_pipeline


class TestStrip:
    def __init__(self, path: str, debugging_path: str = None) -> None:
        self._values, self._image = strip_pipeline(path, debugging_path)

    @property
    def values(self) -> np.array:
        return np.array(self._values)
    
    def save_result(self, path: str) -> None:
        cv2.imwrite(path, self._image)