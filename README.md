# ISRO-Hackthon-2024
We present our solution as the python library GeoAwareGPT, included in this repository along with a streamlit-based app
## Setup
- clone the repository
- `pip install poetry`
- create a venv of py3.11
- `poetry install` (or use `pip install -e .` from within the folder)
- create a .env file with the following:  
    - AZURE_SUBSCRIPTION_KEY # API key for Azure maps  
    - AZURE_CLIENT_ID  
    - GEO_DATA_LOCATION # Path to unstructured data  
    - DB_USER  
    - DB_PASSWORD  
    - DB_HOST  
    - DB_PORT  
    - DB_NAME  
    - TEXT_TRANSLATION_KEY  
    - TRANSLATION_ENDPOINT  
    - AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT  
    - AZURE_DOCUMENT_INTELLIGENCE_SUBSCRIPTION_KEY  
    - AZURE_OPENAI_API_KEY  
- Use `pip install -r requirements.txt` to install the requirements for running the streamlit application
- 

## Usage
Check the tests folder on how to use the library
