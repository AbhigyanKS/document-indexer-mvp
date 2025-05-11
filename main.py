from document_processor.document_processor import extract_text_from_file, categorize_document
from indexer.indexer import OpenSearchIndexer
from query_service.query_service import QueryService
import os

indexer = OpenSearchIndexer()
indexer.create_index()

document_dir = "sample_docs"
document_files = [os.path.join(document_dir, f) for f in os.listdir(document_dir) if os.path.isfile(os.path.join(document_dir, f))]

# Simulated user ID for indexing
user_id = 1

for file_path in document_files:
    text = extract_text_from_file(file_path)
    if text:
        category = categorize_document(text)
        document_data = {
            'title': os.path.basename(file_path),
            'content': text,
            'user_id': user_id,
            'category': category,
            'uploaded_at': "2025-05-11T00:00:00Z",
        }
        indexer.index_document(document_data)
        print(f"Indexed: {file_path}")
    else:
        print(f"Skipping: {file_path} (unsupported or unreadable)")

# Test search
query_service = QueryService()
queries = ["birth", "license", "Eye Color"]

print("\n=== Search Results ===")
for q in queries:
    results = query_service.search_documents(q, user_id)
    print(f"\nQuery: {q}")
    for r in results:
        print("-", r["_source"]["title"])
