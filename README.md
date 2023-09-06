# Aquarium Test Strip Analyzer

Raw Input | Test Strip Detection | Color Extraction
--- | --- | ---
![](https://github.com/Huntler/AquariumTestStripAnalyzer/blob/master/images/raw_example.JPG) | ![](https://github.com/Huntler/AquariumTestStripAnalyzer/blob/master/images/detection_example.jpg) | ![](https://github.com/Huntler/AquariumTestStripAnalyzer/blob/master/images/extraction_example.jpg)

## Image Processing Pipeline
- Initial image
  - Noise reduction
  - Thresholding
  - Morphing
  - Edge detection
  - Contour detection
- On extracted test strip
  - Histogram Equalization
  - Edge detection
  - White balance
  - Extraction of colors (mean)

## Exection (WIP)
The software requires Python 3, OpenCV 4, and NumPy to run. Type the follwing command to exectute the code:

```
python3 reference_table.py
```

The folder structure must be:

```
- data
  - raw_input (photos here)
  - reference (json file containing colors to measure water quality)
  - strips (empty folder containing debugging images)
```
