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

    legs = []
    ticker = None
    first_valid_expiry = None
    
    for line in text.split('\n'):
        # 1. Action
        action_match = re.search(r'(buy|sell)', line, re.IGNORECASE)
        if not action_match: continue
        action = action_match.group(1).capitalize()
        
        # 2. Qty
        qty_search_str = line[action_match.end():]
        qty_match = re.search(r'\d+', qty_search_str)
        if not qty_match: continue
        qty = int(qty_match.group(0))
        
        # 3. Type
        type_match = re.search(r'(put|call)', line, re.IGNORECASE)
        if not type_match: continue
        opt_type = type_match.group(1).capitalize()
        
        # 4. Strike
        strike_match = re.search(r'([\d\.]+)\s*(?:put|call)', line, re.IGNORECASE)
        if not strike_match: continue
        strike = float(strike_match.group(1))
        
        # 5. Ticker
        ticker_str = qty_search_str[qty_match.end():]
        ticker_match = re.search(r'[A-Z]{2,5}', ticker_str)
        tick = ticker_match.group(0) if ticker_match else None
        if tick and not ticker:
            ticker = tick
            
        # 6. Expiry
        if ticker_match and strike_match:
            # Everything between ticker and strike
            exp_raw = ticker_str[ticker_match.end():].split(str(int(strike)))[0].strip()
            # Clean up obvious OCR errors like 'Juti' -> 'Jul'
            exp_raw = exp_raw.replace('Juti', 'Jul').replace('juti', 'jul')
        else:
            exp_raw = ''
            
        parsed_date = dateparser.parse(exp_raw)
        if parsed_date:
            expiry = parsed_date.strftime('%Y-%m-%d')
            if not first_valid_expiry:
                first_valid_expiry = expiry
        else:
            expiry = first_valid_expiry if first_valid_expiry else "" # Fallback to the first valid one we found
            
        legs.append({
            "action": action,
            "qty": qty,
            "strike": strike,
            "type": opt_type,
            "expiry": expiry
        })
            
    if not legs:
        return {"error": "Could not identify any trade legs in the image. Please check the image clarity or format."}
        
    return {"ticker": ticker, "legs": legs}

def parse_single_leg_image(image_input):
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

    ticker = None
    strike = 0.0
    expiry = ""
    opt_type = "Put"
    
    # Attempt OCC symbol match first (e.g. NVDA 261218P00194000)
    # Allows optional spaces/newlines between ticker and numbers
    occ_match = re.search(r'([A-Z]{1,6})\s*(\d{6})([CP])(\d{8})', text.replace('\n', ''))
    if occ_match:
        ticker = occ_match.group(1)
        date_str = occ_match.group(2)
        year = '20' + date_str[0:2]
        month = date_str[2:4]
        day = date_str[4:6]
        expiry = f'{year}-{month}-{day}'
        opt_type = 'Call' if occ_match.group(3) == 'C' else 'Put'
        strike = float(occ_match.group(4)) / 1000.0
    else:
        # Fallback to field matching
        u_match = re.search(r'Underlying\s+([A-Z]+)', text, re.IGNORECASE)
        if u_match: ticker = u_match.group(1)
        
        s_match = re.search(r'Strike\s+([\d\.]+)', text, re.IGNORECASE)
        if s_match: strike = float(s_match.group(1))
        
        e_match = re.search(r'Expiration Date\s+(.+)', text, re.IGNORECASE)
        if e_match:
            raw_exp = e_match.group(1).split('Last')[0].strip() # in case it reads onto the next column
            parsed_date = dateparser.parse(raw_exp)
            if parsed_date: expiry = parsed_date.strftime('%Y-%m-%d')
            
        t_match = re.search(r'Side\s+(Put|Call)', text, re.IGNORECASE)
        if t_match: opt_type = t_match.group(1).capitalize()

    if not ticker:
        return {"error": "Could not identify option details in the image."}
        
    legs = [{
        "action": "Buy", # default
        "qty": 1,        # default
        "strike": strike,
        "type": opt_type,
        "expiry": expiry
    }]
    
    return {"ticker": ticker, "legs": legs}
