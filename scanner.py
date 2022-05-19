import cv2
import imutils
import requests
from skimage.filters import threshold_local
from imutils.perspective import four_point_transform
from BillSplitterApp.backend.data import *




# Try asprice first
receiptOcrEndpoint = 'https://ocr.asprise.com/api/v1/receipt' # Receipt OCR API endpoint
imageFile = "receipt4.jpg" # // Modify it to use your own file
r = requests.post(receiptOcrEndpoint, data = { \
  'client_id': 'TEST',        # Use 'TEST' for testing purpose \
  'recognizer': 'auto',       # can be 'US', 'CA', 'JP', 'SG' or 'auto' \
  'ref_no': 'ocr_python_123', # optional caller provided ref code \
  }, \
  files = {"file": open(imageFile, "rb")})
print(r.text)
success = r.json()['success']   # quota not exceeded
if success:
    receipt = r.json()['receipts'][0]
    receiptitems = receipt['items'] # result in JSON
    tax = receipt['tax'] if 'tax' in receipt and receipt['tax'] else 0
    service_charge = receipt['service_charge'] if 'service_charge' in receipt and receipt['service_charge'] else 0
    tip = receipt['tip'] if 'tip' in receipt and receipt['tip'] else 0
    
    # turn tax service charge and tip into items  (they are shared evenly by everyone by default)
    tax = item('tax', tax, 1, 0)
    service_charge = item('service_charge', service_charge, 1, 0)
    tip = item('tip', tip, 1, 0)
    
    # TO-DO submit the above three items using submit_tempexpenses()
    print(f'tax is {tax.price}')
    print(f'service charge is {service_charge.price}')
    print(f'tip is {tip.price}')
    print("=====================")
    
    for receiptitem in receiptitems:
        newitem = item(receiptitem['description'], receiptitem['amount'], receiptitem['qty'], 1)
        # TO-DO set the splitmode and submit the newitem using submit_tempexpenses()
        print(f"{newitem.quantity} {newitem.name}:     ${newitem.price}")
else:
# Receipt data extraction pipeline using OCR.space   
    pass















# orig = cv2.imread('receipt5.jpg')
# image = orig.copy()
# image = imutils.resize(image, width=500)


# warped = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# T = threshold_local(warped, 11, offset = 10, method = "gaussian")
# warped = (warped > T).astype("uint8") * 255


# print("STEP 3: Apply perspective transform")
# cv2.imshow("Original", imutils.resize(orig, height = 650))
# cv2.imshow("Scanned", imutils.resize(warped, height = 650))
# cv2.waitKey(0)