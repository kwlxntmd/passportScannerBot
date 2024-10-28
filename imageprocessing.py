import numpy as np
import cv2
import os


class ImageProcessing:
    @staticmethod
    def vert_to_horizontal(img):
        h1, w1 = img.shape[0], img.shape[1]
        if h1 > w1:
            img = ImageProcessing.rotate_image(img, 90)
        return img

    @staticmethod
    def rotate_image(img, angle):
        size_reverse = np.array(img.shape[1::-1])
        matrix = cv2.getRotationMatrix2D(tuple(size_reverse / 2.), angle, 1.)
        abs_matrix = np.absolute(matrix[:, :2])
        size_new = abs_matrix @ size_reverse
        matrix[:, -1] += (size_new - size_reverse) / 2.
        return cv2.warpAffine(img, matrix, tuple(size_new.astype(int)))

    @staticmethod
    def reformat_coords(coords):
        coords_list = coords.tolist()
        reformatted_coords = []
        for i in range(6):
            reformatted_coords.append(coords_list[(i + 1) % 6])
        reformatted_coords = np.array(reformatted_coords)
        return reformatted_coords

    @staticmethod
    def find_bigger_bounding_box(approx):
        area_1 = cv2.contourArea(approx[[0, 1, 3, 4]])
        area_2 = cv2.contourArea(approx[[0, 2, 3, 5]])
        print(area_1, area_2)
        return area_1 > area_2

    @staticmethod
    def get_image_roi(image):
        h, w = image.shape[0], image.shape[1]
        y2 = h
        x2 = w
        y1 = int(0.75 * y2)
        x1 = 0
        roi = image[y1:y2, x1:x2]
        return roi

    @staticmethod
    def warp_image_perspective(img, coords):
        pts = np.array(coords, dtype=np.float32)

        width = int(
            max(np.linalg.norm(pts[0] - pts[1]),
                np.linalg.norm(pts[2] - pts[3])))
        height = int(
            max(np.linalg.norm(pts[0] - pts[3]),
                np.linalg.norm(pts[1] - pts[2])))

        dst_pts = np.array(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype=np.float32)

        m = cv2.getPerspectiveTransform(pts, dst_pts)
        output = cv2.warpPerspective(img, m, (width, height))
        return cv2.flip(output, 1)

    @staticmethod
    def deskew(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Найти контуры на изображении
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        # Найти контур с самой большой площадью
        max_contour = max(contours, key=cv2.contourArea)

        # cv2.drawContours(image, max_contour, -1, (0, 0, 255), 3)
        # cv2.imshow("Max_contour", image)
        # cv2.waitKey(0)

        # Аппроксимировать контур
        epsilon = 0.0025 * cv2.arcLength(max_contour, True)
        approx = cv2.approxPolyDP(max_contour, epsilon, True)
        while len(approx) != 6:
            epsilon += 0.005
            approx = cv2.approxPolyDP(max_contour, epsilon, True)

        flag = ImageProcessing.find_bigger_bounding_box(approx)
        if flag:
            approx = ImageProcessing.reformat_coords(approx)

        cv2.drawContours(image, [approx], -1, (0, 0, 255), 3)

        # Разделить аппроксимированный контур на две трапеции
        trap1 = [approx[0], approx[1], approx[4], approx[5]]
        trap2 = [approx[1], approx[2], approx[3], approx[4]]

        # Применить афинные преобразования
        result1 = ImageProcessing.warp_image_perspective(image, trap1)

        result2 = ImageProcessing.warp_image_perspective(image, trap2)

        return result1, result2

    @staticmethod
    def save_photo(img_as_bytearray, date_of_birth, tg_id):
        day, month, year = date_of_birth.split('.')
        year_dir = os.path.join('passport_photos', year)
        if not os.path.exists(year_dir):
            os.makedirs(year_dir)
        month_dir = os.path.join(year_dir, month)
        if not os.path.exists(month_dir):
            os.makedirs(month_dir)
        filepath = os.path.join(month_dir, str(tg_id) + '.jpg')
        with open(filepath, 'wb') as file:
            file.write(img_as_bytearray)
