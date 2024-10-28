from translation_dict import eng, rus
import numpy as np
import pytesseract
import cv2
import imutils
import re
import skimage.filters as filters
from imageprocessing import ImageProcessing


class MRZScanner:
    @staticmethod
    def search_for_mrz(image_list):
        for img in image_list:
            image_roi = ImageProcessing.get_image_roi(img)
            mrztext = MRZScanner.findmrz(image_roi)
            if mrztext is not None:
                return mrztext
        return None

    @staticmethod
    def findmrz(mrz):
        (h, w) = mrz.shape[:2]
        mrz = cv2.resize(mrz, (w * 5, h * 5))

        gray = cv2.cvtColor(mrz, cv2.COLOR_BGR2GRAY)
        smooth = cv2.GaussianBlur(gray, (95, 95), 0)
        division = cv2.divide(gray, smooth, scale=255)
        sharp = filters.unsharp_mask(division, radius=1.5, amount=1.5,
                                     preserve_range=False)
        sharp = (255 * sharp).clip(0, 255).astype(np.uint8)
        thresh = cv2.threshold(sharp, 0, 255,
                               cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        dist = cv2.threshold(thresh, 0, 255,
                             cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))
        opening = cv2.morphologyEx(dist, cv2.MORPH_OPEN, kernel)

        cnts = cv2.findContours(opening.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        chars = []

        for c in cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            if w >= 35 and h >= 100:
                chars.append(c)

        if len(chars) == 0:
            return None

        chars = np.vstack([chars[i] for i in range(len(chars))])
        hull = cv2.convexHull(chars)
        mask = np.zeros(mrz.shape[:2], dtype="uint8")
        cv2.drawContours(mask, [hull], -1, 255, -1)
        mask = cv2.dilate(mask, None, iterations=2)

        final = cv2.bitwise_and(opening, opening, mask=mask)

        config = "--oem 3 --psm 6 -c " \
                 "tessedit_char_whitelist" \
                 "=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789>< "
        mrz_text = pytesseract.image_to_string(final, lang='eng', config=config)
        print("mrzAttempt:", mrz_text)

        mrz_text = mrz_text.replace(" ", "")
        print(len(mrz_text))
        if len(mrz_text) < 80 or len(mrz_text) > 100:
            return None
        mrz_text = mrz_text.split()
        for line in mrz_text:
            if len(line) < 5:
                mrz_text.remove(line)
        if mrz_text[0][0:1] != 'P':
            del mrz_text[0]
        el1 = mrz_text[0]
        el2 = mrz_text[1]
        el1 = el1.replace('1', 'I')
        el2 = el2.replace('O', '0')
        el1 = el1[5:]
        el1 = re.split("<<|<|\n", el1)
        el2 = re.split("RUS|<", el2)
        el1 = list(filter(None, el1))
        el1 = list(map(list, el1))
        el1 = el1[0:3]
        el2 = list(filter(None, el2))
        for i in el1:
            for c, j in enumerate(i):
                ind = eng.index(str(j))
                i[c] = rus[ind]
        surname = ''.join(el1[0])
        name = ''.join(el1[1])
        otch = ''.join(el1[2])
        seria = el2[0][0:3] + el2[2][0:1]
        nomer = el2[0][3:9]
        data = el2[1][0:6]
        if int(data[0:1]) > 2:
            data = '19' + data
        else:
            data = '20' + data
        data = data[6:8] + '.' + data[4:6] + '.' + data[0:4]
        passport_data = {
            'Фамилия': surname.capitalize(),
            'Имя': name.capitalize(),
            'Отчество': otch.capitalize(),
            'Дата рождения': data,
            'Серия': seria,
            'Номер': nomer
        }
        return passport_data
