import requests
from zipfile import ZipFile
import os
import time
import math
import datetime
from PIL import Image, ImageFilter
import numpy as np


def download_img_files(location, camera, time_duration_secs, interval_secs, long_ago=0, timezone="America/Denver"):
    current_seconds = round(math.floor(time.time())) - long_ago
    start_time_mil = (current_seconds - time_duration_secs) * 1000
    end_time_mil = (current_seconds) * 1000

    start_date = datetime.datetime.fromtimestamp(start_time_mil / 1000)
    end_date = datetime.datetime.fromtimestamp(end_time_mil / 1000)

    url = f"https://img.hdrelay.com/api/frames/download?camera={camera}&position=default&from={
        start_time_mil}&to={end_time_mil}&hmax=24&interval={interval_secs}&tz={timezone}"

    filename = f"{camera}_default_{
        start_date:%Y%m%d%H%M}_{end_date:%Y%m%d%H%M}"

    print(f"\nURL: {url}")
    print(f"\nFilename: {filename}\n\n")

    response = requests.get(url)

    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"File '{filename}' downloaded successfully.")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

    with ZipFile(f"./{filename}", 'r') as zObject:
        zObject.extractall(path=location)

    os.remove(filename)

    return os.listdir(location)


def remove_outliers(data):
    # Convert data to a numpy array
    data = np.array(data)

    # Calculate Q1 (25th percentile) and Q3 (75th percentile)
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)

    # Calculate the IQR
    IQR = Q3 - Q1

    # Define the lower and upper bounds for outliers
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Filter out the outliers
    filtered_data = [x for x in data if lower_bound <= x <= upper_bound]

    return filtered_data


def get_median_snow_height_px(img_path, crop_dimensions):
    # Preprocessing
    input_img = Image.open(img_path).crop(crop_dimensions).filter(
        ImageFilter.GaussianBlur(3))

    # input_img.show()

    input_img_pixels = input_img.load()

    snow_path_heights = []

    new_img = Image.new("RGB", input_img.size)

    new_img_pixels = new_img.load()

    width, height = input_img.size
    for x in range(0, width, 5):
        for y in range(height-1, -1, -1):
            r, g, b = input_img_pixels[x, y]
            if (y == height - 1):
                snow_path_heights.append(height - 1)
            if (b-((r+g)/2) < 10):
                if (snow_path_heights[-1] - y < 3):
                    new_img_pixels[x, y] = (255, 0, 0)
                    snow_path_heights[-1] = y
                else:
                    break
        snow_path_heights[-1] = height - 1 - snow_path_heights[-1]

    # new_img.show()
    no_outliars = remove_outliers(snow_path_heights)

    # Calculate the median of the remaining values
    # print(no_outliars)
    median_value = np.median(no_outliars)

    return median_value


def get_dimensions_of_bounding_box(img_path, initial_crop):
    input_img = Image.open(img_path)

    # input_img.show()

    cropped_img = input_img.crop(initial_crop).filter(
        ImageFilter.GaussianBlur(3))

    # cropped_img.show()

    width, height = cropped_img.size

    pixels = cropped_img.load()

    new_img = Image.new("RGB", (width, height))
    new_img_pixels = new_img.load()

    max_heights = []

    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            if (not b-((r+g)/2) < 10):
                new_img_pixels[x, y] = (255, 255, 255)
                max_heights.append(y)
                break
            if (y == height - 1):
                max_heights.append(height - 1)

    current_line = {"domain": [0, 0], "y_vals": [0]}
    lines = []

    # new_img.show()

    for x_val, height in enumerate(max_heights):
        # print(abs(height))
        if (abs(height - current_line["y_vals"][-1]) < 5):
            current_line["y_vals"].append(height)
            current_line["domain"][1] = x_val
        else:

            if (len(current_line["y_vals"]) > 150):
                if (current_line["y_vals"][-1] - current_line["y_vals"][0] < 10):
                    median_height = np.median(np.array(current_line["y_vals"]))
                    lines.append(
                        {"domain": current_line["domain"], "height": median_height})

            # print(current_line)
            current_line = {"domain": [x_val, x_val], "y_vals": [height]}

    initial_left, initial_top, initial_right, initial_bottom = initial_crop

    print(lines)

    lines.sort(key=lambda x: x["height"])

    if not lines:
        return ()

    return (initial_left + lines[0]["domain"][0] + 40, initial_top + lines[0]["height"], initial_left + lines[0]["domain"][1] - 65, initial_top + lines[0]["height"] + 795)


def pixels_to_inches(pixels):
    return pixels * (24/670)


def show_blue(img_path):
    # Preprocessing
    input_img = Image.open(img_path).filter(
        ImageFilter.GaussianBlur(3))

    # input_img.show()

    input_img_pixels = input_img.load()

    new_img = Image.new("RGB", input_img.size)
    new_img_pixels = new_img.load()

    width, height = input_img.size
    for x in range(width):
        for y in range(height):
            r, g, b = input_img_pixels[x, y]
            if (not (b-((r+g)/2) < 10)):
                new_img_pixels[x, y] = (255, 255, 255)
            else:
                new_img_pixels[x, y] = (0, 0, 0)
    # new_img.show()


extract_files = "./downloaded_images"

images = os.listdir(extract_files)

# images = download_img_files(location=extract_files, camera="09f922af-169d-4949-9bb7-295c6a859daa",
#                             time_duration_secs=1000, interval_secs=0, long_ago=0)

# 1000 seconds is about 16 minutes, and the webcams take a picture every 5 minutes, so we should get about 3 images

median_snow_heights = []

for image in images:
    dimensions = get_dimensions_of_bounding_box(
        f"{extract_files}/{image}", (1180, 0, 1720, 1080))

    print(f"{dimensions}")
    if (not dimensions):
        continue

    Image.open(f"{extract_files}/{image}").crop(dimensions).show()
    pixels = get_median_snow_height_px(
        f"{extract_files}/{image}", dimensions)

    median_snow_heights.append(pixels_to_inches(pixels))

print(f"Estimated Snow Height: {np.max(np.array(median_snow_heights))} inches")

# for image in images:
# show_blue(f"{extract_files}/{image}")
