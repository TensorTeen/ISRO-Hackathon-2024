import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain.docstore.document import Document

from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from ...schema import BaseTool


class KnowledgeBase(BaseTool):
    def __init__(self, pdf_location: str = os.environ["GEO_DATA_LOCATION"]):
        super().__init__(
            name="KnowledgeBase",
            description="A knowledge base tool that can be used to retrieve any information that you do not understand",
            version="1.0",
            args={"query": "Query to the Knowledge Base (str)"},
        )
        self.tool_type = "AUA"
        self.vector_store = FAISS
        self.document_path = pdf_location
        self.titles = []
        self.pdf_loader = DocumentAnalysisClient(
            endpoint=os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"],
            credential=AzureKeyCredential(
                os.environ["AZURE_DOCUMENT_INTELLIGENCE_SUBSCRIPTION_KEY"]
            ),
        )
        self.load_documents()
        self.create_vector_store()

    def load_documents(self):
        self.pages = []
        for file in os.listdir(self.document_path):
            if file.endswith(".pdf"):
                file_path = os.path.join(self.document_path, file)
                with open(file_path, "rb") as f:
                    poller = self.pdf_loader.begin_analyze_document(
                        "prebuilt-layout", f
                    )
                    result = poller.result()
                output_text = ""
                # Loop through each page in the document
                for page_num, page in enumerate(result.pages, start=1):
                    output_text += f"--- Page {page_num} ---\n"
                    # Loop through each line of text on the page
                    for line in page.lines:
                        output_text += line.content + "\n"
                    output_text += "\n"

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
                azure_deployment="textembedding",
                azure_endpoint="https://geoawaregptfour.openai.azure.com/",
            ),
        )

    def run(self, query, top_k=5):
        docs = self.vector_db.similarity_search(query, k=top_k)
        doc_string = ""
        for i, doc in enumerate(docs):
            doc_string += str(doc.metadata["page"]) + ":" + str(doc.page_content) + "\n"
        return doc_string


"""
Remember to remove the key from your code when you're done, and never post it publicly. For production, use
secure methods to store and access your credentials. For more information, see 
https://docs.microsoft.com/en-us/azure/cognitive-services/cognitive-services-security?tabs=command-line%2Ccsharp#environment-variables-and-application-configuration
"""
endpoint = "YOUR_FORM_RECOGNIZER_ENDPOINT"
key = "YOUR_FORM_RECOGNIZER_KEY"


def format_bounding_box(bounding_box):
    if not bounding_box:
        return "N/A"
    return ", ".join(["[{}, {}]".format(p.x, p.y) for p in bounding_box])


def analyze_read():
    # sample document
    formUrl = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-layout.pdf"

    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    poller = document_analysis_client.begin_analyze_document_from_url(
        "prebuilt-read", formUrl
    )
    result = poller.result()

    print("Document contains content: ", result.content)

    for idx, style in enumerate(result.styles):
        print(
            "Document contains {} content".format(
                "handwritten" if style.is_handwritten else "no handwritten"
            )
        )

    for page in result.pages:
        print("----Analyzing Read from page #{}----".format(page.page_number))
        print(
            "Page has width: {} and height: {}, measured with unit: {}".format(
                page.width, page.height, page.unit
            )
        )

        for line_idx, line in enumerate(page.lines):
            print(
                "...Line # {} has text content '{}' within bounding box '{}'".format(
                    line_idx,
                    line.content,
                    format_bounding_box(line.polygon),
                )
            )

        for word in page.words:
            print(
                "...Word '{}' has a confidence of {}".format(
                    word.content, word.confidence
                )
            )

    print("----------------------------------------")


if __name__ == "__main__":
    analyze_read()
