import traceback
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR
import re
import base64
from io import BytesIO
import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True,gpu_id=0)
# ocr = PaddleOCR(use_gpu=True, gpu_id=0) 
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

# DRF API View
@api_view(['POST'])
def extract_info(request):
    try:
        # Step 1: Extract the image data from the request
        body = request.data
        data = body.get('image', None)

        if not data:
            return Response({'error': 'No image data provided'}, status=400)

        # Step 2: Decode the base64 image data and load it
        try:
            image_bytes = base64.b64decode(data)
            image = Image.open(BytesIO(image_bytes)).convert('RGB')  # Ensure RGB format
        except Exception as e:
            return Response({'error': f'Failed to process the image: {str(e)}'}, status=400)
        try:
            # Define the cropping box (left, upper, right, lower) as a tuple
            # Example: Cropping a region of the image (this is just an example; adjust as needed)
            left, upper, right, lower = 100, 50, 900, 800  # Example crop coordinates (adjust as needed)
            cropped_image = image.crop((left, upper, right, lower))
            print(cropped_image)
        except Exception as e:
            return Response({'error': f'Failed to crop the image: {str(e)}'}, status=400)


        # Step 3: Resize the image to avoid resource constraints
        try:
            cropped_image = cropped_image.resize((1024, 1024))
            print(cropped_image)
            image_np = np.array(cropped_image)
        except Exception as e:
            return Response({'error': f'Error during image resizing: {str(e)}'}, status=500)

        # Step 4: Perform OCR on the image
        try:
            result = ocr.ocr(image_np, cls=True)  # Assuming `ocr` is properly defined elsewhere
        except Exception as e:
            return Response({'error': f'OCR processing failed: {str(e)}'}, status=500)

        # Step 5: Extract text from the OCR result
        text = "".join([line[1][0] for line in result[0]]) if result and result[0] else ""
        text_no_spaces = text.replace(" ", "")

        # Step 6: Define and apply regex patterns for NID and DOB
        nid_pattern = r'\d{10}'
        dob_pattern = r'\d{2}[A-Za-z]{2,3}\d{4}'
        nid_match = re.search(nid_pattern, text_no_spaces)
        dob_match = re.search(dob_pattern, text_no_spaces)

        nid = nid_match.group() if nid_match else None
        dob = dob_match.group() if dob_match else None

        # Step 7: Handle multiple DOB matches and format them
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
                try:
                    dob = convert_to_yyyy_mm_dd(day, month_abbr, year)
                    break  # Use the first valid match
                except ValueError as ve:
                    print(f"Invalid date format: {match}. Error: {str(ve)}")
        else:
            dob = None

        # Step 8: Prepare the response
        return Response({
            'nid': nid if nid else 'NID not found',
            'dob': dob if dob else 'DOB not found'
        })

    except Exception as e:
        # Catch any unexpected errors
        print("Error traceback:", traceback.format_exc())
        return Response({'error': f'An unexpected error occurred: {str(e)}'}, status=500)




INNOVACTRICS_URL= 'https://dot.innovatrics.com/identity/api/v1/customers'

headers = {
    "Authorization": "RElTX2V2YWxfMzYwOkczclBONzc0d2pSWWdKSExQQkowNFNuSUlLUlVvNE1W",
    "Content-Type": "application/json"
}

VALID_API_KEYS = {"eW91cl9zZWN1cmVfYXBpX2tleQ=="}

def validate_api_key(api_key):
    return api_key in VALID_API_KEYS
   
    
@api_view(['POST'])
def get_customer_data(request):
    api_key = request.headers.get("x-api-key")
    if not validate_api_key(api_key):
        return Response({"error": "Unauthorized access"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        response = requests.post(
            INNOVACTRICS_URL,
            headers=headers,
            verify=False,  
            proxies={"http": None, "https": None} 
        )
        response.raise_for_status()
        return Response({
            "status": "Success",
            "response": response.json()
        })

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    
@api_view(['PUT'])
def create_document(request, customerId):
    print(f"Customer ID: {customerId}") 
    INNOVACTRICS_DOCUMENT_URL = f'https://dot.innovatrics.com/identity/api/v1/customers/{customerId}/document'
    api_key = request.headers.get("x-api-key")
    if not validate_api_key(api_key):
        return Response({"error": "Unauthorized access"}, status=status.HTTP_401_UNAUTHORIZED)
    
    request_data = request.data  
    advice = request_data.get('advice', {})
    sources = request_data.get('sources', [])  
    
    request_payload = {
        "advice": advice,
        "sources": sources
    }
    
    try:
        response = requests.put(
            INNOVACTRICS_DOCUMENT_URL,
            headers=headers,
            json=request_payload,  
            verify=False,  
            proxies={"http": None, "https": None} 
        )
        
        response.raise_for_status()

        return Response({
            "status": "Success",
            "response": response.json()  
        }, status=response.status_code)

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def create_document_front(request, customerId):
    print(f"Customer ID: {customerId}") 
    INNOVACTRICS_DOCUMENT_URL = f'https://dot.innovatrics.com/identity/api/v1/customers/{customerId}/document/pages'
    api_key = request.headers.get("x-api-key")
    if not validate_api_key(api_key):
        return Response({"error": "Unauthorized access"}, status=status.HTTP_401_UNAUTHORIZED)
    
    request_data = request.data  
    image_data = request_data.get('image', {}).get('data', '')
    
    request_payload = {
        "image": {
            "data": image_data
        }
    }
    
    try:
        response = requests.put(
            INNOVACTRICS_DOCUMENT_URL,
            headers=headers,
            json=request_payload,  
            verify=False,  
            proxies={"http": None, "https": None} 
        )
        
        response.raise_for_status()

        return Response({
            "status": "Success",
            "response": response.json()  
        }, status=response.status_code)

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    
    
    
@api_view(['PUT'])
def create_document_Back(request, customerId):
    print(f"Customer ID: {customerId}") 
    INNOVACTRICS_DOCUMENT_URL = f'https://dot.innovatrics.com/identity/api/v1/customers/{customerId}/document/pages'
    api_key = request.headers.get("x-api-key")
    if not validate_api_key(api_key):
        return Response({"error": "Unauthorized access"}, status=status.HTTP_401_UNAUTHORIZED)
    
    request_data = request.data  
    pageTypes = request_data.get('advice', {}).get('classification',{}.get('pageTypes',[]))
    image_data = request_data.get('image', {}).get('data', '')
    
    request_payload = {
        "advice": {
            "classification": {
                "pageTypes": pageTypes
            }
                   
                   },
        "image": {
            "data": image_data
        }
    }
    
    print("Request Payload:", request_payload)  # To ensure the payload is formed correctly
    try:
        response = requests.put(
            INNOVACTRICS_DOCUMENT_URL,
            headers=headers,
            json=request_payload,  
            verify=False,  
            proxies={"http": None, "https": None} 
        )
        
        response.raise_for_status()

        return Response({
            "status": "Success",
            "response": response.json()  
        }, status=response.status_code)

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    
@api_view(['GET'])
def get_customer_with_document(request, customerId):
    print(f"Customer ID: {customerId}") 
    INNOVACTRICS_DOCUMENT_URL = f'https://dot.innovatrics.com/identity/api/v1/customers/{customerId}'
    api_key = request.headers.get("x-api-key")
    if not validate_api_key(api_key):
        return Response({"error": "Unauthorized access"}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        response = requests.get(
            INNOVACTRICS_DOCUMENT_URL,
            headers=headers,
            verify=False,  
            proxies={"http": None, "https": None} 
        )
        
        response.raise_for_status()

        return Response({
            "status": "Success",
            "response": response.json()  
        }, status=response.status_code)

    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

