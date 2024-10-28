import pytesseract
from imageprocessing import ImageProcessing
from mrzscanner import MRZScanner


def main(image_temp):
    pytesseract.pytesseract.tesseract_cmd = \
        r'/usr/local/Cellar/tesseract/5.3.2/bin/tesseract'
    image1, image2 = ImageProcessing.deskew(image_temp)

    image1 = ImageProcessing.vert_to_horizontal(image1)
    image2 = ImageProcessing.vert_to_horizontal(image2)

    image_list = [image2, image1, ImageProcessing.rotate_image(image1, 180),
                  ImageProcessing.rotate_image(image2, 180)]
    mrz_scanner = MRZScanner()
    mrztext = mrz_scanner.search_for_mrz(image_list)
    if mrztext is None:
        print("Could not find passport info")
        return "Could not find passport info"
    else:
        print(mrztext)
        return mrztext
