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

    img = image.copy()
    cv2.drawContours(img, [box], 0, (0, 255, 0), 8)

    # Clip the box
    box[:, 0] = np.clip(box[:, 0], 0, image.shape[0])
    box[:, 1] = np.clip(box[:, 1], 0, image.shape[1])

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
        return rotated_extracted_region[padding:-padding, padding:-padding], img

    return rotated_extracted_region, img


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
    # 1. Store a copy of the original image and improve the contrast to highlight the colors
    original_image = image.copy()
    image = improve_contrast(image)

    # 2. Equalize the hisotgram to highlight the colors
    hist, bins = np.histogram(image.flatten(), 256, [0, 256])
    cdf = hist.cumsum()
    cdf_normalized = cdf * float(hist.max()) / cdf.max()

    cdf_m = np.ma.masked_equal(cdf, 0)
    cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
    cdf = np.ma.filled(cdf_m, 0).astype("uint8")
    image = cdf[image]

    # 3. Find edges to extract the color patches only
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    image = cv2.GaussianBlur(image, (5, 5), 3)
    _, image = cv2.threshold(image, 127, 255, cv2.THRESH_TOZERO_INV)

    # 4. Go over the image and extract the color patches
    patch_region_marker = -1
    i, j = 0, 0
    patches = []
    result_image = original_image.copy()
    for y in range(image.shape[0]):
        if np.mean(image[y, :]) > 10 and patch_region_marker == -1:
            patch_region_marker = y
            result_image[y, :, :] = np.repeat(
                [[0, 255, 0]], result_image.shape[1], axis=0
            )

        if np.mean(image[y, :]) < 10 and patch_region_marker != -1:
            if y - patch_region_marker < 0.8 * original_image.shape[1]:
                patch_region_marker = -1
                continue

            result_image[y, :, :] = np.repeat(
                [[0, 0, 255]], result_image.shape[1], axis=0
            )
            patch = original_image[patch_region_marker:y, :, :]

            patch[:, :, 0] = np.mean(patch[:, :, 0])
            patch[:, :, 1] = np.mean(patch[:, :, 1])
            patch[:, :, 2] = np.mean(patch[:, :, 2])

            patches.append((patch, patch[0, 0, :]))
            patch_region_marker = -1

    np.nan_to_num(result_image, copy=False)
    return result_image, patches


def strip_pipeline(image_path: str, save_intermediates: bool = False) -> np.array:
    image_name = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = f"./data/strips/{image_name}"
    save = (
        lambda img, pre: save_image(image_name, img, pre, output_dir)
        if save_intermediates
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
    color_patches, color_values = extract_color_patches(extracted_strip)
    save(color_patches, "4_patch_detection")

    balanced_colors = []
    result_image = np.zeros(shape=(450, 50, 3), dtype=np.intp)
    if len(color_values) != 0:
        for i, (patch, color) in enumerate(color_values):
            balanced_color = apply_white_balance(patch[0], white_value)[0]
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


if __name__ == "__main__":
    output_dir = "./data/strips/"

    # Find the strip and remove the background
    image_path = "./data/raw_input/IMG_3193.JPG"
    strip_pipeline(image_path, save_intermediates=True)

    image_path = "./data/raw_input/IMG_3196.JPG"
    strip_pipeline(image_path, save_intermediates=True)
