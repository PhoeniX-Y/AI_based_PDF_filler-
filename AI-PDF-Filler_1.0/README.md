# AI PDF Filler

AI PDF Filler is an intelligent application that automatically fills PDF forms using AI-powered text generation and image processing techniques.

## Project Overview

This project uses Flask for the web interface, OpenCV and Tesseract for image processing, and Ollama for AI-powered text generation. It processes PDF files, detects form fields, and fills them with contextually appropriate information.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AI-PDF-Filler.git
   cd AI-PDF-Filler
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Tesseract OCR:
   - On Ubuntu: `sudo apt-get install tesseract-ocr`
   - On macOS: `brew install tesseract`
   - On Windows: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

5. Install Ollama:
   Follow the instructions at [Ollama's official website](https://ollama.ai/)

## Usage

1. Start the Flask application:
   ```bash
   python src/app.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`

3. Upload a PDF file and a context file (in .txt format)

4. Click "Process Files" to generate the filled PDF

5. Download the resulting filled PDF

## Testing

Run the tests using pytest:
