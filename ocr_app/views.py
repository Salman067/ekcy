import json
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
import re
import base64
from io import BytesIO
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Initialize PaddleOCR with CPU (set use_gpu=False)
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)

# Month abbreviation mapping to numerical month
month_map = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
    'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12',
    'Jn': '01', 'Fb': '02', 'Mr': '03', 'Ar': '04', 'My': '05', 'Jn': '06',
    'Jl': '07', 'Ag': '08', 'Sp': '09', 'Ot': '10', 'Nv': '11', 'Dc': '12',
    'Ja': '01', 'Fe': '02', 'Ma': '03', 'Ap': '04', 'Ma': '05', 'Ju': '06',
    'Ju': '07', 'Au': '08', 'Se': '09', 'Oc': '10', 'No': '11', 'De': '12',
    'an': '01', 'eb': '02', 'ar': '03', 'pr': '04', 'ay': '05', 'un': '06',
    'ul': '07', 'ug': '08', 'ep': '09', 'ct': '10', 'ov': '11', 'ec': '12'
}

# Convert to YYYY-MM-DD format
def convert_to_yyyy_mm_dd(day, month_abbr, year):
    month = month_map.get(month_abbr, None)
    if month:
        return f"{year}-{month}-{day}"
    else:
        return None 

@csrf_exempt
def extract_info(request):
    if request.method == 'POST':
        try:
            # Load the body and get the image data
            body = json.loads(request.body)
            data = body.get('image') 
            
            if not data:
                return JsonResponse({'error': 'No image data provided'}, status=400)

            # Decode the base64 image data
            image_bytes = base64.b64decode(data)
            image = Image.open(BytesIO(image_bytes)).convert('RGB')  # Ensure RGB format
            image_np = np.array(image)

            # Resize the image to a smaller size to avoid resource constraints
            image = image.resize((1024, 1024))
            image_np = np.array(image)

            # Run OCR on the image
            result = ocr.ocr(image_np, cls=True)

            # Extract text from the OCR result
            text = ""
            for line in result[0]:
                text += line[1][0]

            # Remove spaces for easier pattern matching
            text_no_spaces = text.replace(" ", "")

            # Define regex patterns for NID and DOB
            nid_pattern = r'\d{10}'
            dob_pattern = r'\d{2}[A-Za-z]{2,3}\d{4}'
            nid_match = re.search(nid_pattern, text_no_spaces)
            dob_match = re.search(dob_pattern, text_no_spaces)

            # Extract NID and DOB from the text
            nid = nid_match.group() if nid_match else None
            dob = dob_match.group() if dob_match else None

            # Check for multiple date of birth matches and format them
            matches = re.findall(dob_pattern, text_no_spaces)
            if matches:
                for match in matches:
                    day = match[:2]
                    if len(match) > 8:
                        month_abbr = match[2:5]
                        year = match[5:]
                    else:
                        month_abbr = match[2:4]
                        year = match[4:]
                    formatted_date = convert_to_yyyy_mm_dd(day, month_abbr, year)
                    dob = formatted_date
            else:
                dob = None

            # Return the extracted NID and DOB in the response
            return JsonResponse({
                'nid': nid if nid else 'NID not found',
                'dob': dob if dob else 'DOB not found'
            })
        except Exception as e:
            # Catch any unexpected errors
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


# import requests
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from django.conf import settings


# INNOVACTRICS_URL= 'https://dot.innovatrics.com/identity/api/v1/customers'

# headers = {
#     "Authorization": "RElTX2V2YWxfMzYwOkczclBONzc0d2pSWWdKSExQQkowNFNuSUlLUlVvNE1W",
#     "Content-Type": "application/json"
# }

# VALID_API_KEYS = {"eW91cl9zZWN1cmVfYXBpX2tleQ=="}

# def validate_api_key(api_key):
#     return api_key in VALID_API_KEYS
   
    
# @api_view(['GET'])
# def get_customer_data(request):
#     api_key = request.headers.get("x-api-key")
#     if not validate_api_key(api_key):
#         return Response({"error": "Unauthorized access"}, status=status.HTTP_401_UNAUTHORIZED)

#     try:
#         response = requests.post(
#             INNOVACTRICS_URL,
#             headers=headers,
#             verify=False,  
#             proxies={"http": None, "https": None} 
#         )
#         response.raise_for_status()
#         return Response({
#             "status": "Success",
#             "response": response.json()
#         })

#     except requests.exceptions.RequestException as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    
# @api_view(['POST']) 
# def get_document_data(request,customerId):
#     print(customerId)
#     INNOVACTRICS_DOCUMENT_URL = f'https://dot.innovatrics.com/identity/api/v1/customers/{customerId}/document/pages'
#     api_key = request.headers.get("x-api-key")
#     if not validate_api_key(api_key):
#         return Response({"error": "Unauthorized access"}, status=status.HTTP_401_UNAUTHORIZED)
    
#     request_data = request.data  
#     advice = request_data.get('advice', {})
#     image_data = request_data.get('image', {}).get('data', '')
#     request_payload = {
#         "advice": advice,
#         "image": {
#             "data": image_data
#         }
#     }
    
#     try:
#         response = requests.put(
#             INNOVACTRICS_DOCUMENT_URL,
#             headers=headers,
#             json=request_payload,  
#             verify=False,  
#             proxies={"http": None, "https": None}
#         )
#         response.raise_for_status()
#         return Response({
#             "status": "Success",
#             "response": response.json()  
#         })

#     except requests.exceptions.RequestException as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
