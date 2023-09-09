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

## Exection
The software requires Python 3, OpenCV 4, and NumPy to run. Type the follwing command to exectute the code:

```
python3 main.py -i {image_path}
```

Debugging the processing pipeline relies on analyzing the intermediate images. Hence, run the program using `-s`

```
python3 main.py -i {image_path} -s
```

In case there is a different reference table needed, execute the command with `-r`

```
python3 main.py -i {image_path} -r {reference_table_path}
```

The folder default folder structure is:

```
- data
  - reference           (json file containing colors to measure water quality)
    - default.json      (loaded as default)
  - debugging           (created when calling the program with `-s`)
```

## Used Test-Strips
The program was developed based on the 9-in-one test strips found on [amazon](https://www.amazon.de/dp/B0BFX4H44F?ref=ppx_yo2ov_dt_b_product_details&th=1&language=en_GB). Different tests are possible, if the program uses a different reference table for the color-to-value operation. Feel free to create an issue for that and provide the corresponding `reference.json`.