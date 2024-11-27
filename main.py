import requests
from zipfile import ZipFile
import os
import time
import math
import datetime
from PIL import Image, ImageFilter


def download_img_files():
    # Calculate the current time in milliseconds
    current_milliseconds = round(math.floor(time.time()) * 1000)
    start_time = current_milliseconds - 36000000
    end_time = current_milliseconds

    # Convert start and end times to datetime objects
    start_date = datetime.datetime.fromtimestamp(start_time / 1000)
    end_date = datetime.datetime.fromtimestamp(end_time / 1000)

    interval = 36000

    # Construct the URL for downloading the zip file
    url = f'https://img.hdrelay.com/api/frames/download?camera=09f922af-169d-4949-9bb7-295c6a859daa&position=default&from={
        start_time}&to={end_time}&hmax=24&interval={interval}&tz=America/Denver'

    # Generate the filename based on the start and end dates
    filename = f"09f922af-169d-4949-9bb7-295c6a859daa_default_{
        start_date:%Y%m%d%H%M}_{end_date:%Y%m%d%H%M}"

    print(f"\nURL: {url}")
    print(f"\nFilename: {filename}\n\n")

    # Download the file from the URL
    response = requests.get(url)

    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"File '{filename}' downloaded successfully.")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

    # Extract the contents of the zip file
    with ZipFile(f"./{filename}", 'r') as zObject:
        zObject.extractall(path=f"./images")

    # Remove the zip file after extraction
    os.remove(filename)


# download_img_files()

folder_path = "./sample_images"
jpg_files = os.listdir(folder_path)

# Function to convert milliseconds to a human-readable date


def convert_to_human_readable(file_name):
    try:
        milliseconds = int(os.path.splitext(file_name)[0])
        date_time = datetime.datetime.fromtimestamp(milliseconds / 1000)
        return date_time.strftime("%Y-%m-%d--%H:%M:%S")
    except ValueError:
        return "Invalid file name format"


# Loop through the list of files and convert the timestamps
for jpg_file in jpg_files:
    readable_date = convert_to_human_readable(jpg_file)
    print(f"File: {jpg_file} -> Date: {readable_date}")

    image_cropped = Image.open(
        f"./sample_images/{jpg_file}").crop((1390, 90, 1510, 870))

    image_blurred = image_cropped.filter(ImageFilter.GaussianBlur(4))

    pixels = image_blurred.load()

    image_cropped_pixels = image_cropped.load()

    width, height = image_blurred.size

    new_image = Image.new("RGB", (width, height))
    new_pixels = new_image.load()

    supr_img = Image.new("RGB", (4 * width, height))

    supr_img_pixels = supr_img.load()

    snow_height = 0
    no_snow = 0

    for x in range(width):
        for y in range(height - 1, -1, -1):
            r, g, b = pixels[x, y]
            rs, gs, bs = image_cropped_pixels[x, y]
            if (b-((r+g)/2) < 10):
                new_pixels[x, y] = (255, 0, 0)
                supr_img_pixels[x+width, y] = (0, 0, 0)
                supr_img_pixels[x+2*width, y] = (rs, gs, bs)
                if (x % 10 < 2 and no_snow < 3):
                    new_pixels[x, y] = (0, 255, 0)
                    snow_height += 1
                else:
                    ++no_snow
            else:
                supr_img_pixels[x+2*width, y] = (0, 0, 0)
                supr_img_pixels[x+width, y] = (rs, gs, bs)

    print(snow_height)

    supr_img.paste(image_cropped, (0, 0))
    supr_img.paste(new_image, (3*width, 0))

    new_image.save(f"./images/ALTERED_{jpg_file}")
    supr_img.save(f"./images/SUPER_{jpg_file}")
