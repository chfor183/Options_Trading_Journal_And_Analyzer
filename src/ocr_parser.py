import io
import re
import os
import pytesseract
from PIL import Image
import dateparser

# Set typical windows path if not in env to make it easier for Windows users
if os.name == 'nt' and os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def parse_trade_image(image_input):
    try:
        if isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        else:
            img = image_input
            
        if img.mode == 'RGBA':
            img = img.convert('RGB')
            
        text = pytesseract.image_to_string(img)
    except pytesseract.TesseractNotFoundError:
        return {"error": "Tesseract-OCR is not installed or not in PATH. Please install it from https://github.com/UB-Mannheim/tesseract/wiki and add to your system PATH."}
    except Exception as e:
        return {"error": f"Failed to process image: {str(e)}"}

    # Regex to match: Action Qty Ticker Expiry Strike Type
    # Example: Buy 1 GLD Jul24'26 345 PUT
    pattern = re.compile(r"(Buy|Sell)\s+(\d+)\s+([A-Z]+)\s+([a-zA-Z0-9\']+)\s+([\d\.]+)\s+(PUT|CALL)", re.IGNORECASE)
    
    legs = []
    ticker = None
    
    for line in text.split('\n'):
        match = pattern.search(line)
        if match:
            action, qty, tick, exp_raw, strike, opt_type = match.groups()
            
            if not ticker:
                ticker = tick.upper()
                
            # Parse date
            parsed_date = dateparser.parse(exp_raw)
            if parsed_date:
                expiry = parsed_date.strftime('%Y-%m-%d')
            else:
                expiry = exp_raw # Fallback
                
            legs.append({
                "action": action.capitalize(),
                "qty": int(qty),
                "strike": float(strike),
                "type": opt_type.capitalize(),
                "expiry": expiry
            })
            
    if not legs:
        return {"error": "Could not identify any trade legs in the image. Please check the image clarity or format."}
        
    return {"ticker": ticker, "legs": legs}
