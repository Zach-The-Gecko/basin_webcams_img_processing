from PIL import Image, ImageFilter

file_path = "./downloaded_images/1735542304142.jpg"
crop_dimensions = (1220, 1079.0, 1304, 1874.0)
# crop_dimensions = (1409, 83.0, 1523, 878.0)

input_img = Image.open(file_path).crop(
    crop_dimensions).filter(ImageFilter.GaussianBlur(4))

input_img.show()
