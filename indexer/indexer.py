from opensearchpy import OpenSearch
import json
from datetime import datetime

class OpenSearchIndexer:
    def __init__(self, host='localhost', port=9200):
        self.client = OpenSearch([{'host': host, 'port': port}])
        self.index_name = 'documents'
    
    def create_index(self):
        """Create an OpenSearch index if it doesn't exist."""
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(
                index=self.index_name,
                body={
                    "mappings": {
                        "properties": {
                            "title": {"type": "text"},
                            "content": {"type": "text"},
                            "document_type": {"type": "keyword"},
                            "tags": {"type": "text"},
                            "uploaded_at": {"type": "date"}
                        }
                    }
                }
            )

    def index_document(self, document_data):
        """Index a document in OpenSearch."""
        self.client.index(
            index=self.index_name,
            body=document_data
        )
