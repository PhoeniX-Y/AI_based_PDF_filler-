import requests
import json
from datetime import datetime
import re

def get_ollama_response(prompt, context, model="llama3.2:3b"):
    url = "http://localhost:11434/api/generate"
    
    full_prompt = f"{context}\n\nBased on the above information, {prompt}"
    
    data = {
        "model": model,
        "prompt": full_prompt,
        "stream": False
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return json.loads(response.text)['response']
    else:
        return f"Error: {response.status_code}, {response.text}"

def add_current_date_to_context(context):
    current_date = datetime.now().strftime("%d/%m/%Y")
    return f"Current Date: {current_date}\n\n{context}"

def read_context_file(context_file):
    with open(context_file, 'r', encoding='utf-8') as file:
        return file.read()

def is_url(text):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return bool(url_pattern.match(text))