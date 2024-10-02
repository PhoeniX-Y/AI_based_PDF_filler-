from flask import Flask, render_template, request, send_file, session
import os
from main import process_pdf
from ollama_utils import add_current_date_to_context, read_context_file

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key

# Get the absolute path of the current script
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get uploaded files
        pdf_file = request.files['pdf_file']
        context_file = request.files['context_file']

        # Save uploaded files
        uploads_dir = os.path.join(BASE_DIR, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        pdf_path = os.path.join(uploads_dir, pdf_file.filename)
        context_path = os.path.join(uploads_dir, context_file.filename)
        pdf_file.save(pdf_path)
        context_file.save(context_path)

        # Process the PDF
        output_dir = os.path.join(BASE_DIR, 'output')
        os.makedirs(output_dir, exist_ok=True)
        context = read_context_file(context_path)
        context_with_date = add_current_date_to_context(context)
        output_filename = f"filled_{os.path.splitext(pdf_file.filename)[0]}.pdf"
        output_pdf = process_pdf(pdf_path, output_dir, context_with_date, output_filename)

        # Store the output PDF path in the session
        session['output_pdf'] = output_pdf
        
        return render_template('index.html', processing_complete=True)

    return render_template('index.html', processing_complete=False)

@app.route('/download')
def download():
    output_pdf = session.get('output_pdf')
    if output_pdf and os.path.exists(output_pdf):
        return send_file(output_pdf, as_attachment=True)
    else:
        return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)
