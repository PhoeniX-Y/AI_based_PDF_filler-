import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
from ollama_utils import get_ollama_response, is_url

def preprocess_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    
    return denoised

def detect_cells(gray):
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cells = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 3000 < area < 200000:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 50 and h > 20:
                cells.append((x, y, w, h))
    return cells

def is_cell_empty(img, x, y, w, h):
    cell = img[y:y+h, x:x+w]
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
    white_pixel_ratio = np.sum(binary == 255) / (w * h)
    return white_pixel_ratio > 0.95

def get_field_name(img, x, y, w, h):
    # Check the entire left side for the field name
    left_cell = img[y:y+h, 0:x]
    left_text = pytesseract.image_to_string(left_cell)
    return left_text.strip() if left_text.strip() else "Unknown Field"

def put_text_in_box(img, text, x, y, w, h, color=(0, 0, 0), font_size=38, thickness=2, align_left=False, align_top=False):
    # Convert OpenCV image to PIL Image
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    
    margin = 5
    line_spacing = 8  # Increased line spacing
    
    # Split text into lines if it's too wide
    lines = []
    words = text.split()
    current_line = words[0]
    for word in words[1:]:
        bbox = draw.textbbox((0, 0), current_line + " " + word, font=font)
        if bbox[2] - bbox[0] <= w - 2*margin:
            current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    
    # Calculate total text height
    bbox = draw.textbbox((0, 0), "A", font=font)
    line_height = bbox[3] - bbox[1] + line_spacing
    total_text_height = len(lines) * line_height - line_spacing
    
    # Draw text
    for i, line in enumerate(lines):
        if align_top:
            text_y = y + margin + i * line_height
        else:
            text_y = y + (h - total_text_height) // 2 + i * line_height
        
        bbox = draw.textbbox((0, 0), line, font=font)
        if align_left:
            text_x = x + margin
        else:
            text_x = x + (w - (bbox[2] - bbox[0])) // 2
        
        # Draw text with a slight offset to create a bold effect
        for offset in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            draw.text((text_x + offset[0], text_y + offset[1]), line, font=font, fill=color)
    
    # Convert back to OpenCV image
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def detect_and_mark_cells(image_path, output_image_path, context):
    img = cv2.imread(image_path)
    
    # Preprocess the image
    preprocessed = preprocess_image(img)
    
    cells = detect_cells(preprocessed)
    
    # Process cells
    i = 0
    while i < len(cells):
        x, y, w, h = cells[i]
        if is_cell_empty(img, x, y, w, h):
            # Check for multiple empty cells
            multi_cells = [cells[i]]
            j = i + 1
            while j < len(cells) and cells[j][1] == y and is_cell_empty(img, *cells[j]):
                multi_cells.append(cells[j])
                j += 1
            
            if len(multi_cells) > 1:
                # Sort multi_cells from left to right
                multi_cells.sort(key=lambda cell: cell[0])
                
                field_name = get_field_name(img, multi_cells[0][0], multi_cells[0][1], multi_cells[0][2], multi_cells[0][3])

                # Get all items for the field at once
                prompt = f"What are the {field_name}? Provide a comma-separated list of {len(multi_cells)} items, each item should be 1-3 words long."
                answer = get_ollama_response(prompt, context)
                items = [item.strip() for item in answer.split(',')]
                
                # Ensure we have enough items
                while len(items) < len(multi_cells):
                    items.append("")
                
                # Fill each cell with a different item
                for idx, cell in enumerate(multi_cells):
                    x, y, w, h = cell
                    item = items[idx] if idx < len(items) else ""
                    img = put_text_in_box(img, item, x, y, w, h, font_size=24, align_left=True)
                
                i = j - 1
            else:
                field_name = get_field_name(img, x, y, w, h)
                prompt = f"What is the {field_name}? Provide a very concise answer, preferably 1-3 words only. If it's a date, If it's a number, provide only the number. For date calculations, use the current date provided."
                answer = get_ollama_response(prompt, context)
                # Truncate the answer if it's too long
                answer = ' '.join(answer.split()[:3])  # Limit to 3 words
                img = put_text_in_box(img, answer, x, y, w, h, font_size=28)
        else:
            pass
        i += 1

    # Process entire image for Q. and A.
    pil_img = Image.fromarray(cv2.cvtColor(preprocessed, cv2.COLOR_BGR2RGB))
    data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
    
    i = 0
    last_question = ""
    while i < len(data['text']):
        if data['text'][i].strip().lower().startswith('q.'):
            start_x, start_y = data['left'][i], data['top'][i]
            end_x, end_y = start_x + data['width'][i], start_y + data['height'][i]
            
            # Find the end of the question (next Q. or A.)
            j = i + 1
            while j < len(data['text']) and not (data['text'][j].strip().lower().startswith('q.') or data['text'][j].strip().lower().startswith('a.')):
                end_x = max(end_x, data['left'][j] + data['width'][j])
                end_y = max(end_y, data['top'][j] + data['height'][j])
                j += 1
            
            # Adjust the question box size
            start_x = max(0, start_x - 5)
            start_y = max(0, start_y - 5)
            end_x = min(img.shape[1], end_x + 5)
            end_y = min(img.shape[0], end_y - int((end_y - start_y) * 0.2))  # Reduce height by 20%
            
            last_question = ' '.join(data['text'][i:j])
            i = j - 1  # Move to the last processed word
        
        elif data['text'][i].strip().lower().startswith('a.'):
            x, y = data['left'][i], data['top'][i]
            w, h = data['width'][i], data['height'][i]
            
            # Create imaginary box that includes A. and extends below
            img_h, img_w = img.shape[:2]
            answer_box_w = int((img_w - (x + w + 3)) * 0.9)  # 10% shorter from the right side
            
            # Find the next element's y-coordinate
            next_element_y = img_h
            for j in range(i+1, len(data['text'])):
                if data['text'][j].strip():
                    next_element_y = data['top'][j]
                    break
            
            answer_box_h = next_element_y - y - 10  # Leave a small gap
            answer_box_y = y
            
            prompt = f"{last_question} Please keep the answer concise and to the point in about 20-25 words. For date calculations, use the current date provided."
            answer = get_ollama_response(prompt, context)
            
            # Check if the answer is a URL
            if is_url(answer):
                color = (0, 0, 255)  # Blue color for URLs
            else:
                color = (0, 0, 0)  # Black color for regular text
            
            img = put_text_in_box(img, answer, x + w + 3, answer_box_y, answer_box_w, answer_box_h, align_left=True, align_top=True, font_size=28, color=color)
        
        i += 1

    cv2.imwrite(output_image_path, img)
    return img