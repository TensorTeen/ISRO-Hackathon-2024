from PyPDF2 import PdfReader, PdfWriter
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import os, io, pdfplumber
from PIL import Image

from dotenv import load_dotenv

load_dotenv()

# Replace with your Form Recognizer endpoint and key
endpoint = os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"]
key = os.environ["AZURE_DOCUMENT_INTELLIGENCE_SUBSCRIPTION_KEY"]

# Initialize the DocumentAnalysisClient
document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
)

# Path to your original PDF file
pdf_path = r"D:\Workspace\GitRepos\ISRO-Hackathon-2024\tests\data\documents\lulc.pdf"
pdf_comp_path = (
    r"D:\Workspace\GitRepos\ISRO-Hackathon-2024\tests\data\documents\lulc_comp.pdf"
)
import pikepdf


def compress_pdf(input_pdf, output_pdf):
    pdf = pikepdf.open(input_pdf)
    pdf.save(output_pdf, compress_streams=True)
    pdf.close()


# Replace 'path_to_your_pdf_file.pdf' with the path to your PDF file
compress_pdf(pdf_path, pdf_comp_path)


def split_pdf(input_pdf, output_folder):
    reader = PdfReader(input_pdf)
    num_pages = len(reader.pages)
    os.makedirs(output_folder, exist_ok=True)
    for i in range(num_pages):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        output_filename = os.path.join(output_folder, f"page_{i + 1}.pdf")
        with open(output_filename, "wb") as output_pdf:
            writer.write(output_pdf)
        print(f"Created: {output_filename}")


def process_pdf_pages(input_folder):
    for filename in os.listdir(input_folder):
        if filename.endswith(".pdf"):
            page_path = os.path.join(input_folder, filename)
            with open(page_path, "rb") as pdf_file:
                poller = document_analysis_client.begin_analyze_document(
                    model_id="prebuilt-read", document=pdf_file
                )
                result = poller.result()

            # Extract text from the page
            output_text = ""
            for page_num, page in enumerate(result.pages, start=1):
                output_text += f"--- Page {page_num} ---\n"
                for line in page.lines:
                    output_text += line.content + "\n"
                output_text += "\n"  # Add a blank line between pages

            # Save the extracted text to a file
            text_file_name = os.path.splitext(filename)[0] + ".txt"
            with open(os.path.join(input_folder, text_file_name), "w") as text_file:
                text_file.write(output_text)
            print(f"Text extracted and saved to: {text_file_name}")


# Folder to store split pages
output_folder = "split_pages"

# Split the PDF into single-page files
split_pdf(pdf_comp_path, output_folder)

# Process each page and extract text
process_pdf_pages(output_folder)
