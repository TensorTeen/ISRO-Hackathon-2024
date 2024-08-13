from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from ...schema import BaseTool
from langchain_community.embeddings import AzureOpenAIEmbeddings
import os
from langchain.docstore.document import Document


class KnowledgeBase(BaseTool):
    def __init__(self, **kwargs):
        super().__init__(
            name="KnowledgeBase",
            description="A knowledge base tool that can be used to retrive any information that you do not understand",
            version="1.0",
            args={"query": "Query to the Knowledge Base (str)"},
        )
        self.tool_type = "AUA"
        self.vector_store = FAISS
        self.document_path = kwargs.get(
            "pdf_location",
            r"D:\Workspace\GitRepos\ISRO-Hackathon-2024\tests\data\documents",
        )
        self.titles = []
        self.pdf_loader = PyPDFLoader
        self.load_documents()
        self.create_vector_store()

    def load_documents(self):
        self.pages = []
        for file in os.listdir(self.document_path):
            if file.endswith(".pdf"):
                file_path = os.path.join(self.document_path, file)
                self.pages.extend(self.pdf_loader(file_path).load_and_split())
                self.titles.append(file)
            if file.endswith(".txt"):
                file_path = os.path.join(self.document_path, file)
                with open(file_path, "r") as f:
                    text = f.read()
                    self.pages.append(
                        Document(page_content=text, metadata={"page": file})
                    )
                    self.titles.append(file)

    def create_vector_store(self):
        self.vector_db = self.vector_store.from_documents(
            self.pages,
            AzureOpenAIEmbeddings(
                chunk_size=3000,
                azure_deployment="azure-text-embedding",
                azure_endpoint="https://azure-geoaware-gpt.openai.azure.com/",
            ),
        )

    def run(self, query, top_k=5):
        docs = self.vector_db.similarity_search(query, k=top_k)
        doc_string = ""
        for i, doc in enumerate(docs):
            doc_string += str(doc.metadata["page"]) + ":" + str(doc.page_content) + "\n"
        return doc_string
