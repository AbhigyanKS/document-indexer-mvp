import os
import json
from datetime import datetime
from query_service.llm_extractor import encode_file_to_base64, extract_info_with_llm
from document_processor.document_proc import extract_text_from_file
# --- Config ---
document_dir = "sample_docs"
output_dir = "extracted_results"
os.makedirs(output_dir, exist_ok=True)

# --- Process Documents via Bedrock LLM ---
document_files = [
    os.path.join(document_dir, f)
    for f in os.listdir(document_dir)
    if os.path.isfile(os.path.join(document_dir, f))
]

for file_path in document_files:
    try:
        extracted_text = extract_text_from_file(file_path)
        filename = os.path.basename(file_path)
       
        # Safe initialization
        llm_output = None
        llm_output = extract_info_with_llm(extracted_text, filename)

      

        parsed = llm_output  # Already a Python dict
        parsed["file_name"] = filename
        parsed["processed_at"] = datetime.utcnow().isoformat()

        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{base_name}.json")

        with open(output_path, "w") as f:
            json.dump(parsed, f, indent=2)

        print(f"✅ Extracted: {filename} → {output_path}")

    except json.JSONDecodeError:
        print(f"❌ JSON error from LLM on: {filename}\nRaw output:\n{llm_output}")
    except Exception as e:
        print(f"❌ Failed to process {filename}: {str(e)}")
