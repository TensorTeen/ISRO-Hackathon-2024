# Bharatiya-Antariksh-Hackathon-2024
We present our solution as the python library GeoAwareGPT, included in this repository along with a streamlit-based app
## Setup
1. clone the repository
2. ```pip install poetry```
3. create a venv of py3.11
4. `poetry install` (or use `pip install -e .` from within the folder)
5. create a .env file with the following: 
    - DB_USER = geoaware_admin
    - DB_PASSWORD = ISROgpt01
    - DB_HOST = geoawaretesting.postgres.database.azure.com
    - DB_PORT = 5432
    - DB_NAME = geo_database
    - GEO_DATA_LOCATION = ".../ISRO-Hackathon/split_pages" # requires absolute path 
    - AZURE_SUBSCRIPTION_KEY # Azure maps resource  
    - TEXT_TRANSLATION_KEY # Translator resource (azure)  
    - SPEECH_KEY # Speech service resource (azure)  
    - SPEECH_REGION # region of speech service resource (eg. centralindia)
    - TRANSLATION_ENDPOINT = https://api.cognitive.microsofttranslator.com/ # Likely will not change if using similar settings
    - AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT # endpoint to OpenAI embeddings resource for retrieval
    - AZURE_DOCUMENT_INTELLIGENCE_SUBSCRIPTION_KEY  # OpenAI embeddings for retrieval
    - AZURE_OPENAI_API_KEY # Required for deploying endpoint for document retrieval
- Use `pip install -r requirements.txt` to install the requirements for running the streamlit application

## Usage
1. Enter the root folder, containing app.py
2. Run the following
    ```streamlit run app.py```