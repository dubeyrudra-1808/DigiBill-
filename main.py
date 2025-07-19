from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, json, requests, logging, time
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# —————— Setup & Logging ——————
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
app = FastAPI()

# 1️⃣ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 🔒 in prod: specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2️⃣ Ensure upload dir exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def ocr_image(path: str) -> str:
    return pytesseract.image_to_string(Image.open(path))

def ocr_pdf(path: str) -> str:
    pages = convert_from_path(path, dpi=200)
    texts = []
    for i, pg in enumerate(pages, start=1):
        texts.append(f"----- Page {i} -----\n" + pytesseract.image_to_string(pg))
    return "\n".join(texts)

# 5️⃣ Gemini API settings
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBYF6YY896mwS0_hod-A8VAcLMChAXBXvc")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"  # Changed to more stable model

def call_gemini_with_retry(prompt: str, max_retries: int = 3) -> dict:
    """Call Gemini API with retry logic and better error handling"""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048,
        }
    }
    params = {"key": API_KEY}
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Calling Gemini API (attempt {attempt + 1}/{max_retries})")
            
            resp = requests.post(
                GEMINI_URL, 
                params=params, 
                headers=headers, 
                json=payload, 
                timeout=60  # Increased timeout
            )
            
            # Log response details for debugging
            logging.info(f"Gemini API response status: {resp.status_code}")
            
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 503:
                logging.warning(f"Gemini API unavailable (503), retrying in {2 ** attempt} seconds...")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            elif resp.status_code == 429:
                logging.warning(f"Rate limited (429), retrying in {5 * (attempt + 1)} seconds...")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
            elif resp.status_code == 400:
                # Bad request - likely API key or prompt issue
                error_detail = resp.text
                logging.error(f"Bad request to Gemini API: {error_detail}")
                raise HTTPException(status_code=400, detail=f"Invalid API request: {error_detail}")
            
            resp.raise_for_status()
            
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
        except requests.exceptions.ConnectionError:
            logging.warning(f"Connection error on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [503, 429] and attempt < max_retries - 1:
                continue
            raise
    
    # If all retries failed
    raise HTTPException(
        status_code=503, 
        detail="Gemini API is currently unavailable. Please try again later."
    )

def extract_json_from_text(text: str) -> dict:
    """Extract and parse JSON from Gemini response with better error handling"""
    try:
        # Try to find JSON block first
        start = text.find("{")
        end = text.rfind("}")
        
        if start == -1 or end == -1:
            # If no JSON found, try to create structured data from text
            logging.warning("No JSON found in response, attempting to structure data")
            return {
                "raw_response": text,
                "error": "Could not extract structured data",
                "suggestion": "The AI response did not contain valid JSON format"
            }
        
        json_str = text[start:end + 1]
        parsed_json = json.loads(json_str)
        
        # Validate that it's not empty
        if not parsed_json:
            raise ValueError("Empty JSON object")
            
        return parsed_json
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        return {
            "raw_response": text,
            "error": "Invalid JSON format in response",
            "json_error": str(e)
        }
    except Exception as e:
        logging.error(f"Unexpected error parsing JSON: {e}")
        return {
            "raw_response": text,
            "error": "Unexpected error parsing response",
            "details": str(e)
        }

@app.post("/upload")
async def upload_bill(file: UploadFile = File(...)):
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (10MB limit)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400, 
                detail="File size exceeds 10MB limit"
            )
        
        # Save file
        dest = os.path.join(UPLOAD_DIR, file.filename)
        with open(dest, "wb") as buf:
            buf.write(content)
        
        logging.info(f"Saved upload to {dest} ({file_size} bytes)")
        
        # OCR
        try:
            if file_extension == '.pdf':
                text = ocr_pdf(dest)
            else:
                text = ocr_image(dest)
            
            logging.info(f"OCR text length: {len(text)} chars")
            
            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="No text could be extracted from the file. Please ensure the file contains readable text."
                )
                
        except Exception as e:
            logging.error(f"OCR error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to extract text from file: {str(e)}"
            )
        
        # Build enhanced Gemini prompt
        prompt = f"""
Extract ALL relevant information from this bill/invoice and return ONLY a valid JSON object with the following structure:

{{
    "business_name": "Name of the business/store",
    "business_address": "Complete address",
    "business_phone": "Phone number if available",
    "bill_number": "Invoice/bill number",
    "date": "Date in YYYY-MM-DD format",
    "time": "Time if available",
    "items": [
        {{
            "name": "Item name",
            "quantity": number,
            "unit_price": number,
            "total_price": number
        }}
    ],
    "subtotal": number,
    "tax_amount": number,
    "tax_percentage": number,
    "discount": number,
    "total_amount": number,
    "payment_method": "Cash/Card/UPI etc",
    "customer_info": "Customer details if available"
}}

Bill Text:
{text}

Return ONLY the JSON object, no explanation or markdown formatting.
"""

        # Call Gemini API with retry logic
        try:
            gem_response = call_gemini_with_retry(prompt)
            gem_text = gem_response["candidates"][0]["content"]["parts"][0]["text"]
            logging.info(f"Gemini returned {len(gem_text)} chars")
            
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            # Return OCR text as fallback
            return JSONResponse(
                content={
                    "error": "AI processing unavailable",
                    "message": "Extracted text only (AI service temporarily unavailable)",
                    "raw_text": text,
                    "suggestion": "Please try again later or contact support"
                },
                status_code=202  # Accepted but not fully processed
            )
        
        # Extract and parse JSON
        extracted_data = extract_json_from_text(gem_text)
        
        # Clean up uploaded file (optional)
        try:
            os.remove(dest)
        except:
            pass
            
        return JSONResponse(content=extracted_data)
        
    except HTTPException as he:
        logging.error(f"HTTPException: {he.detail}")
        raise he
    except Exception as e:
        logging.exception("Unhandled error in /upload")
        return JSONResponse(
            content={
                "error": "Internal server error",
                "message": str(e),
                "suggestion": "Please try again or contact support"
            },
            status_code=500
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/test-gemini")
async def test_gemini():
    """Test Gemini API connectivity"""
    try:
        test_response = call_gemini_with_retry("Hello, respond with: {\"status\": \"working\"}")
        return {"gemini_status": "connected", "response": test_response}
    except Exception as e:
        return {"gemini_status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)