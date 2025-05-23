# app.py

import os
import json
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime

from query_service.llm_extractor import encode_file_to_base64, extract_info_with_llm
from document_processor.document_proc import extract_text_from_file

# --- Config ---
UPLOAD_FOLDER = "uploaded_docs"
OUTPUT_FOLDER = "extracted_results"
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Helper ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---
@app.route('/extract', methods=['POST'])
def extract_document_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Process
        extracted_text = extract_text_from_file(file_path)
        llm_output = extract_info_with_llm(extracted_text, filename)

        result = llm_output
        result["file_name"] = filename
        result["processed_at"] = datetime.utcnow().isoformat()

        # Save to file (optional)
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(OUTPUT_FOLDER, f"{base_name}.json")
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({"error": "LLM returned invalid JSON", "raw_output": str(llm_output)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Run ---
if __name__ == '__main__':
    app.run(debug=True)
