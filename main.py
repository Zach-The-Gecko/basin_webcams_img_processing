import requests
from zipfile import ZipFile
import os
import time
import math
import datetime
from PIL import Image, ImageFilter
import numpy as np


def download_img_files(location, camera, time_duration_secs, interval_secs, timezone="America/Denver"):
    current_seconds = round(math.floor(time.time()))
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
        ImageFilter.GaussianBlur(4))

    input_img.save(f"{img_path}_blurry.jpg")

    input_img_pixels = input_img.load()

    new_image = Image.new("RGB", input_img.size)
    new_image_pixels = new_image.load()

    snow_path_heights = []

    width, height = input_img.size
    for x in range(0, width, 10):
        for y in range(height-1, -1, -1):
            r, g, b = input_img_pixels[x, y]
            if (y == height - 1):
                snow_path_heights.append(height - 1)
            if (b-((r+g)/2) < 10):

                if (snow_path_heights[-1] - y < 3):
                    snow_path_heights[-1] = y
                    new_image_pixels[x, y] = (255, 0, 0)
                else:
                    break
        snow_path_heights[-1] = height - 1 - snow_path_heights[-1]

    new_image.save(f"{img_path}computer_vision.jpg")

    no_outliars = remove_outliers(snow_path_heights)

    # Calculate the median of the remaining values
    median_value = np.mean(no_outliars)

    return median_value


def pixels_to_inches(pixels):
    return pixels * (24/700)


images = download_img_files(location="./test_imgs", camera="09f922af-169d-4949-9bb7-295c6a859daa",
                            time_duration_secs=3600, interval_secs=10)

for image in images:
    pixels = get_median_snow_height_px(
        f"./test_imgs/{image}", (1390, 90, 1510, 870))
    print(f"Snow height in pixels: {pixels}")
    print(f"Snow height in inches: {pixels_to_inches(pixels)}")
    print()
