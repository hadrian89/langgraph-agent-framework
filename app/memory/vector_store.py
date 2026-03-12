from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma


class VectorMemory:

    def __init__(self):

        embeddings = OllamaEmbeddings(model="nomic-embed-text")

        self.db = Chroma(collection_name="health_memory", embedding_function=embeddings)

    def add_memory(self, text):

        self.db.add_texts([text])

    def search(self, query):

        docs = self.db.similarity_search(query)

        return docs
