from opensearchpy import OpenSearch
import os

# Fetch OpenSearch host from environment variables or hardcoded if required
OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST', 'http://localhost:9200')
INDEX_NAME = "documents"

# Create the OpenSearch client
client = OpenSearch(hosts=[OPENSEARCH_HOST])


def init_index():
    """
    Initializes the OpenSearch index with autocomplete analyzers and proper mappings.
    Call this once during setup.
    """
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(
            index=INDEX_NAME,
            body={
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "autocomplete": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "autocomplete_filter"]
                            },
                            "autocomplete_search": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase"]
                            }
                        },
                        "filter": {
                            "autocomplete_filter": {
                                "type": "edge_ngram",
                                "min_gram": 1,
                                "max_gram": 20
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "title": {
                            "type": "text",
                            "analyzer": "autocomplete",
                            "search_analyzer": "autocomplete_search"
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "autocomplete",
                            "search_analyzer": "autocomplete_search"
                        },
                        "user_id": {"type": "integer"},
                        "category": {"type": "keyword"},
                        "uploaded_at": {"type": "date"}
                    }
                }
            }
        )


def index_document(document_data):
    """
    Index a single document into OpenSearch.
    :param document_data: dict containing the document's fields
    """
    response = client.index(index=INDEX_NAME, body=document_data)
    return response


def search_documents(query, user_id):
    """
    Perform a search query scoped to a user.
    :param query: search term (string)
    :param user_id: int
    :return: list of matching documents
    """
    body = {
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content"],
                        "fuzziness": "AUTO"
                    }
                },
                "filter": {
                    "term": {
                        "user_id": user_id
                    }
                }
            }
        }
    }

    response = client.search(index=INDEX_NAME, body=body)
    return response["hits"]["hits"]


def get_autocomplete_suggestions(prefix, user_id):
    """
    Get autocomplete suggestions for a given prefix (typically from user input).
    :param prefix: String query prefix
    :param user_id: int user ID for scoped search
    :return: List of autocomplete suggestions
    """
    body = {
        "size": 0,
        "aggs": {
            "autocomplete_suggestions": {
                "terms": {
                    "field": "content.keyword",
                    "include": f"{prefix}.*",
                    "size": 5
                }
            }
        },
        "query": {
            "term": {
                "user_id": user_id
            }
        }
    }

    response = client.search(index=INDEX_NAME, body=body)
    return [s["key"] for s in response["aggregations"]["autocomplete_suggestions"]["buckets"]]
