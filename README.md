# Aquarium Test Strip Analyzer

Raw Input | Test Strip Detection
--- | ---
![](https://github.com/Huntler/AquariumTestStripAnalyzer/blob/master/images/detection_example.jpg) | ![](https://github.com/Huntler/AquariumTestStripAnalyzer/blob/master/images/raw_example.jpg)

Color Extraction | Test Strip Detection
--- | ---
![](https://github.com/Huntler/AquariumTestStripAnalyzer/blob/master/images/extraction_example.jpg) | Reference image of colors -> values required to return measurements

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
