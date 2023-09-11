from typing import List, Tuple
import cv2
import numpy as np
import os


def pre_process(image: np.array) -> np.array:
    # Copy the image to avoid changes
    image = image.copy()

    # Smooth the image
    blur = cv2.GaussianBlur(image, (15, 15), 3)

    # Morph: Close to Open
    kernel = np.ones((12, 12), np.uint8)
    morphed = cv2.morphologyEx(
        blur,
        cv2.MORPH_CLOSE,
        kernel,
        anchor=(-1, -1),
        iterations=8,
        borderType=cv2.BORDER_CONSTANT,
    )
    morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel, iterations=4)

    # Morph: Dialate
    dialate_param = 5
    kernel = np.ones((dialate_param, dialate_param), np.uint8)
    noise_reduced = cv2.morphologyEx(morphed, cv2.MORPH_ERODE, kernel)

    return noise_reduced


def detect_edges(image: np.array) -> Tuple[np.array, int]:
    # Edge detection
    canny = cv2.Canny(image, 50, 100, apertureSize=3, L2gradient=True)

    # Post-process edges
    # Morph: Dialate
    dilate_param = 50
    iterations = 4
    kernel = np.ones((dilate_param, dilate_param), np.uint8)
    noise_reduced = cv2.morphologyEx(
        canny, cv2.MORPH_DILATE, kernel, iterations=iterations
    )

    return noise_reduced, (dilate_param * iterations) // 2


def extract_test_strip(image: np.array, edges: np.array, padding: int = 0) -> np.array:
    test_stripe_ratio = 0.042099354476564696

    # Get contours of the image (given edges)
    contours = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    # Find the contours covering the largest area
    area = 0
    for c in contours:
        contour_area = cv2.contourArea(c)
        if area < contour_area:
            area = contour_area
            big_contour = c

    # Rotate rectangle matching the contour
    rot_rect = cv2.minAreaRect(big_contour)
    box = cv2.boxPoints(rot_rect)
    box = np.intp(box)

    image_contours = image.copy()
    cv2.drawContours(image_contours, [box], 0, (0, 255, 0), 8)

    # Clip the box
    box[:, 0] = np.clip(box[:, 0], 0, image.shape[1])
    box[:, 1] = np.clip(box[:, 1], 0, image.shape[0])

    # Extract the rectangle and perform perspective transformation
    min_x = np.min(box[:, 0])
    max_x = np.max(box[:, 0])
    min_y = np.min(box[:, 1])
    max_y = np.max(box[:, 1])
    extracted_region = image[min_y:max_y, min_x:max_x]

    # Rotate the extracted region to align it with the horizontal axis
    angle = rot_rect[2]
    if angle > 45:
        angle -= 90
    elif angle < -45:
        angle += 90
    
    rotated_extracted_region = cv2.warpAffine(
        extracted_region,
        cv2.getRotationMatrix2D(
            (extracted_region.shape[1] / 2, extracted_region.shape[0] / 2), angle, 1
        ),
        (extracted_region.shape[1], extracted_region.shape[0]),
    )

    # Apply the padding if given
    if padding > 0:
        padded_region = rotated_extracted_region[padding:-padding, padding:-padding]

        # check if the extracted shpae has the correct ratio
        ratio = test_stripe_ratio / (padded_region.shape[1] / padded_region.shape[0])
        offset = int(padded_region.shape[1] - padded_region.shape[1] * ratio) // 2
        if offset > 0:
            # adapt the padding, as the ratio was incorrect
            padded_region = padded_region[:, offset:-offset]

        return padded_region, image_contours

    return rotated_extracted_region, image_contours


def white_balance(image: np.array, value: List = None) -> np.array:
    if value is None:
        patch = image[image.shape[0] - 100 :, :]
        value = patch.mean(axis=(0, 1))
        if (value == 0).any():
            return image, None

    value = np.array(value)
    return (image * 1.0 / value * 255).clip(0, 255).astype(np.intp), value


def apply_white_balance(image: np.array, value: List) -> np.array:
    if value is None:
        print("Warning: No white-balance applied.")
        return image

    value = np.array(value)
    return (image * 1.0 / value * 255).clip(0, 255).astype(np.intp)


def extract_color_patches(image: np.array) -> Tuple[np.array, List]:
    patch_start_threshold = 200
    patch_end_threshold = 150
    algorithm_start_offset = 0.05

    # 1. Store a copy of the original image and improve the contrast to highlight the colors
    original_image = image.copy()
    image = improve_contrast(image)

    # 2. drop unnecessary data of horizontal information
    vertical_img = image[:, image.shape[1] // 2, :]
    vertical_img = vertical_img[:, np.newaxis, :]
    image = np.repeat(vertical_img, image.shape[1], axis=1)

    # 3. Equalize the hisotgram to highlight the colors
    hist, bins = np.histogram(image.flatten(), 256, [0, 256])
    cdf = hist.cumsum()
    cdf_normalized = cdf * float(hist.max()) / cdf.max()

    cdf_m = np.ma.masked_equal(cdf, 0)
    cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
    cdf = np.ma.filled(cdf_m, 0).astype("uint8")
    image = cdf[image]

    # 4. Find edges to extract the color patches only
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((12, 12), np.uint8)
    image = cv2.morphologyEx(
        image,
        cv2.MORPH_CLOSE,
        kernel,
        anchor=(-1, -1),
        iterations=8,
        borderType=cv2.BORDER_CONSTANT,
    )
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=4)

    kernel = np.ones((5, 5), np.uint8)
    image = cv2.morphologyEx(image, cv2.MORPH_ERODE, kernel)
    image = 255 - image

    image_search = image.copy()

    # 4. Go over the image and extract the color patches
    patch_start = -1
    patches = []
    result_image = original_image.copy()

    # detect the first two patches which help finding all patches afterward
    # note: the assumption here is, that all test-patch are sized and placed equally!
    offset = int(image.shape[0] * algorithm_start_offset)
    for y in range(image.shape[0] - offset, 0, -1):
        # detect start of first patch
        if np.mean(image[y, :]) > patch_start_threshold and patch_start == -1:
            patch_start = y
            result_image[y, :, :] = np.repeat(
                [[0, 255, 0]], result_image.shape[1], axis=0
            )
        
        # detect end of first patch
        if np.mean(image[y, :]) < patch_end_threshold and patch_start != -1:
            result_image[y, :, :] = np.repeat(
                [[0, 0, 255]], result_image.shape[1], axis=0
            )

            center = patch_start - ((patch_start - y) // 2)
            result_image[center, :, :] = np.repeat(
                [[255, 0, 0]], result_image.shape[1], axis=0
            )

            patches.append([patch_start, y, center])
            patch_start = -1
        
        # end loop if first patch was detected
        if len(patches) == 2:
            break
    
    # calculate the distance between ptaches and the average patch size
    patch_distance = patches[0][2] - patches[1][2]
    avg_patch_height = (patches[0][0] - patches[0][1] + patches[1][0] - patches[1][1]) // 2
    
    # get all patches
    patch_start = patches[0][2]
    patches = []
    for i in range(9):
        y = patch_start - patch_distance * i
        start = y + avg_patch_height // 2
        end = y - avg_patch_height // 2

        # adding lines to debug
        result_image[y, :, :] = np.repeat(
            [[255, 0, 0]], result_image.shape[1], axis=0
        )
        result_image[start, :, :] = np.repeat(
            [[0, 255, 0]], result_image.shape[1], axis=0
        )
        if end > 0:
            result_image[end, :, :] = np.repeat(
                [[0, 0, 255]], result_image.shape[1], axis=0
            )

        # get the mean-color
        # TODO: background color to NAN
        # TODO: enlarge the mean-area
        mean_color = np.nanmean(original_image[y, :, :], axis=0)
        patches.insert(0, mean_color)

    np.nan_to_num(result_image, copy=False)
    return result_image, image_search, patches


def strip_pipeline(image_path: str, debugging_path: str = None) -> np.array:
    image_name = os.path.splitext(os.path.basename(image_path))[0]
    save = (
        lambda img, pre: save_image(image_name, img, pre, debugging_path)
        if debugging_path
        else 0
    )

    # Load the image
    image = cv2.imread(image_path)

    # Transform to gray scale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Run the pipeline
    # 1. Pre-process the image
    pre_processed = pre_process(gray)
    save(pre_processed, "0_pre")

    # 2. Find edges
    edges, offset = detect_edges(pre_processed)
    save(edges, "1_edges")

    # 3. Extract the strip only
    # add gaussian kernel, morph:open, and morph:dialate to the offset (7 + 12 + 5 = 24)
    offset += 24
    extracted_strip, detection = extract_test_strip(image, edges, padding=offset)
    save(detection, "2_1_detection")
    save(extracted_strip, "2_extracted")

    # 4. Analyze the white color to perform a white balance
    color_balanced, white_value = white_balance(extracted_strip)
    save(color_balanced, "3_balance")

    # 5. extract the 9 color patches
    color_patches, image_search, color_values = extract_color_patches(extracted_strip)
    save(color_patches, "4_2_patch_detection")
    save(image_search, "4_1_patch_detection")

    balanced_colors = []
    result_image = np.zeros(shape=(450, 50, 3), dtype=np.intp)
    if len(color_values) != 0:
        for i, color in enumerate(color_values):
            balanced_color = apply_white_balance(np.array([color]), white_value)[0]
            result_image[i * 50 :, :] = balanced_color
            balanced_colors.append(balanced_color)

        save(result_image, "5_result")

    return balanced_colors, result_image


def save_image(
    file_name: str,
    image: np.array,
    prefix: str = "",
    folder_name: str = "",
    create_subfolder: bool = True,
):
    # Create the file name with prefix and file extension
    file_name = file_name if prefix == "" else f"{prefix}_{file_name}.jpg"

    # Create the full path and needed directories
    if not os.path.exists(folder_name) and create_subfolder:
        os.mkdir(folder_name)

    # Store the image
    full_path = os.path.join(folder_name, file_name)
    cv2.imwrite(full_path, image)


def improve_contrast(image: np.array) -> np.array:
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)
    # Applying CLAHE to L-channel
    # feel free to try different values for the limit and grid size:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l_channel)

    # merge the CLAHE enhanced L-channel with the a and b channel
    limg = cv2.merge((cl, a, b))

    # Converting image from LAB Color model to BGR color spcae
    enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    return enhanced_img
