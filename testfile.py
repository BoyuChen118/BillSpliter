import BillSplitterApp.backend.mongodb as backendService
import random, string
from BillSplitter.strings import *
import requests


# auth = backendService.Authenticator()
# surveydata = auth.get_survey_data("KX0J4L5X", "test")
# print(surveydata)







# print("=== Python Receipt OCR ===")

# receiptOcrEndpoint = 'https://ocr.asprise.com/api/v1/receipt' # Receipt OCR API endpoint
# imageFile = "receipt.jpg" # // Modify it to use your own file
# r = requests.post(receiptOcrEndpoint, data = { \
#   'client_id': 'TEST',        # Use 'TEST' for testing purpose \
#   'recognizer': 'auto',       # can be 'US', 'CA', 'JP', 'SG' or 'auto' \
#   'ref_no': 'ocr_python_123', # optional caller provided ref code \
#   }, \
#   files = {"file": open(imageFile, "rb")})
# print(r.json())
# items = r.json()['receipts'][0]['items'] # result in JSON
# for item in items:
#     print(f"{item['qty']} {item['description']}:     ${item['amount']}")








#receipt ocr with german API
import cv2
import imutils
def ocr_file(filename, overlay=False, api_key=receipt_ocr_api_key, language='eng'):
    """ OCR.space API request with local file.
        Python3.5 - not tested on 2.7
    :param filename: Your file path & name.
    :param overlay: Is OCR.space overlay required in your response.
                    Defaults to False.
    :param api_key: OCR.space API key.
                    Defaults to 'helloworld'.
    :param language: Language code to be used in OCR.
                    List of available language codes can be found on https://ocr.space/OCRAPI
                    Defaults to 'en'.
    :return: Result in JSON format.
    """

    payload = {'isOverlayRequired': overlay,
               'apikey': api_key,
               'language': language,
               'isTable': True,
               }
    with open(filename, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image',
                          files={filename: f},
                          data=payload,
                          )
    print(r.text)
    print('----------------------------json below----------------------------')
    return r.json()['ParsedResults'][0]['ParsedText']

print(ocr_file('receipt12.png'))



















# receipt ocr with opencv
# import cv2
# import re
# import imutils
# import pytesseract
# from imutils.perspective import four_point_transform

# orig = cv2.imread('receipt10.jpg')
# image = orig.copy()
# image = imutils.resize(image, width=500)
# ratio = orig.shape[1] / float(image.shape[1])

# # convert the image to grayscale, blur it slightly, and then apply
# # edge detection
# gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# blurred = cv2.GaussianBlur(gray, (5, 5,), 0)


# # canny edge detection
# t_lower = 100
# t_upper = 300
# edged = cv2.Canny(gray, t_lower, t_upper)



# # # check to see if we should show the output of our edge detection
# # # procedure
# cv2.imshow("Input", image)
# cv2.imshow("Edged", edged)
# cv2.waitKey(0)


# # find contours in the edge map and sort them by size in descending
# # order
# cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
# 	cv2.CHAIN_APPROX_SIMPLE)

# cnts = imutils.grab_contours(cnts)
# cnts = sorted(cnts, key=cv2.contourArea, reverse=True)


# # initialize a contour that corresponds to the receipt outline
# receiptCnt = None
# # loop over the contours
# for c in cnts:
# 	# approximate the contour
# 	peri = cv2.arcLength(c, True)
# 	approx = cv2.approxPolyDP(c, 0.02 * peri, True)
# 	# if our approximated contour has four points, then we can
# 	# assume we have found the outline of the receipt
# 	if len(approx) == 4:
# 		receiptCnt = approx
# 		break
# # if the receipt contour is empty then our script could not find the
# # outline and we should be notified
# if receiptCnt is None:
# 	raise Exception(("Could not find receipt outline. "
# 		"Try debugging your edge detection and contour steps."))
 
 
 
 
#  # check to see if we should draw the contour of the receipt on the
# # image and then display it to our screen

# output = image.copy()
# cv2.drawContours(output, [receiptCnt], -1, (0, 255, 0), 2)
# cv2.imshow("Receipt Outline", output)
# cv2.waitKey(0)
# # apply a four-point perspective transform to the *original* image to
# # obtain a top-down bird's-eye view of the receipt
# receipt = four_point_transform(orig, receiptCnt.reshape(4, 2) * ratio)
# # show transformed image
# cv2.imshow("Receipt Transform", imutils.resize(receipt, width=500))
# cv2.waitKey(0)


# # apply OCR to the receipt image by assuming column data, ensuring
# # the text is *concatenated across the row* (additionally, for your
# # own images you may need to apply additional processing to cleanup
# # the image, including resizing, thresholding, etc.)
# options = "--psm 4"
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# text = pytesseract.image_to_string(
# 	cv2.cvtColor(receipt, cv2.COLOR_BGR2RGB),
# 	config=options)
# # show the raw output of the OCR process
# print("[INFO] raw output:")
# print("==================")
# print(text)
# print("\n")























# document scan
# import cv2
# import imutils
# from skimage.filters import threshold_local
# from imutils.perspective import four_point_transform

# orig = cv2.imread('receipt5.jpg')
# image = orig.copy()
# image = imutils.resize(image, width=500)
# ratio = orig.shape[1] / float(image.shape[1])

# # convert the image to grayscale, blur it slightly, and then apply
# # edge detection
# gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# blurred = cv2.GaussianBlur(gray, (5, 5,), 0)


# # canny edge detection
# t_lower = 200
# t_upper = 300
# edged = cv2.Canny(gray, t_lower, t_upper)



# # # check to see if we should show the output of our edge detection
# # # procedure
# cv2.imshow("Input", image)
# cv2.imshow("Edged", edged)
# cv2.waitKey(0)


# # find contours in the edge map and sort them by size in descending
# # order
# cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
# 	cv2.CHAIN_APPROX_SIMPLE)

# cnts = imutils.grab_contours(cnts)
# cnts = sorted(cnts, key=cv2.contourArea, reverse=True)


# # initialize a contour that corresponds to the receipt outline
# receiptCnt = None
# # loop over the contours
# for c in cnts:
# 	# approximate the contour
# 	peri = cv2.arcLength(c, True)
# 	approx = cv2.approxPolyDP(c, 0.02 * peri, True)
# 	# if our approximated contour has four points, then we can
# 	# assume we have found the outline of the receipt
# 	if len(approx) == 4:
# 		receiptCnt = approx
# 		break
# # if the receipt contour is empty then our script could not find the
# # outline and we should be notified
# if receiptCnt is None:
# 	raise Exception(("Could not find receipt outline. "
# 		"Try debugging your edge detection and contour steps."))
 
 
 
 
#  # check to see if we should draw the contour of the receipt on the
# # image and then display it to our screen

# output = image.copy()
# cv2.drawContours(output, [receiptCnt], -1, (0, 255, 0), 2)
# cv2.imshow("Receipt Outline", output)
# cv2.waitKey(0)
# # apply a four-point perspective transform to the *original* image to
# # obtain a top-down bird's-eye view of the receipt
# receipt = four_point_transform(orig, receiptCnt.reshape(4, 2) * ratio)
# # show transformed image
# cv2.imshow("Receipt Transform", imutils.resize(receipt, width=500))
# cv2.waitKey(0)


# warped = cv2.cvtColor(receipt, cv2.COLOR_BGR2GRAY)
# T = threshold_local(warped, 11, offset = 10, method = "gaussian")
# warped = (warped > T).astype("uint8") * 255


# print("STEP 3: Apply perspective transform")
# cv2.imshow("Original", imutils.resize(orig, height = 650))
# cv2.imshow("Scanned", imutils.resize(warped, height = 650))
# cv2.waitKey(0)