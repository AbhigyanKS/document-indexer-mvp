from indexer.opensearch import search_documents

class QueryService:
    def search_documents(self, query, user_id):
        return search_documents(query, user_id)
