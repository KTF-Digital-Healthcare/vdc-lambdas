"""
This function will scan through one given PDF document, use Google's Natural Language API to find and censor
identifiable information, before uploading to a given GCS bucket as a txt file. The PDF can be given as a raw file path
or as an S3 file providing the S3 bucket and object key are given.
"""
import io
import os

import boto3
from google.cloud import language_v1, storage
from google.cloud.storage import Blob
from google.oauth2 import service_account
from pypdf import PdfReader
import re

# Regex pattern to detect emails
EMAIL_PATTERN = r"[A-Za-z0-9]+@[\w]+\.[\w]+"
PDF_PATH = os.getenv("pdf_path", None)
GCS_BUCKET_NAME = os.getenv("gcs_bucket_name", None)
S3_BUCKET_NAME = os.getenv("s3_bucket_name", None)
S3_OBJECT_KEY = os.getenv("s3_object_key", "example.pdf")

service_account_credentials = {
    "type": os.getenv("service_account_type", None),
    "project_id": os.getenv("service_account_project_id", None),
    "private_key_id": os.getenv("service_account_private_key_id", None),
    "private_key": os.getenv("service_account_private_key", None),
    "client_email": os.getenv("service_account_private_client_email", None),
    "client_id": os.getenv("service_account_client_id", None),
    "auth_uri": os.getenv("service_account_auth_uri", None),
    "token_uri": os.getenv("service_account_token_uri", None),
    "auth_provider_x509_cert_url": os.getenv(
        "service_account_auth_provider_x509_cert_url", None
    ),
    "client_x509_cert_url": os.getenv("service_account_client_x509_cert_url", None),
    "universe_domain": os.getenv("service_account_universe_domain", None),
}


def lambda_handler(event, context):

    credentials = service_account.Credentials.from_service_account_info(
        service_account_credentials,
    )

    # Set up a GCP Language Client using credentials provided
    language_client = language_v1.LanguageServiceClient(
        credentials=credentials,
    )
    storage_client = storage.Client(credentials=credentials)  # GCS Storage client
    s3_client = boto3.client("s3")  # AWS Storage client

    # Find GCS bucket
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    # creating a pdf reader object
    # From a downloaded pdf file
    if PDF_PATH is not None:
        reader = PdfReader(PDF_PATH)
    else:
        buffer = io.BytesIO()
        s3_client.download_fileobj(
            S3_BUCKET_NAME,
            S3_OBJECT_KEY,
            buffer,
        )
        reader = PdfReader(buffer)

    plain_text = ""

    # Iterate through pages in the PDF document
    for page in reader.pages:

        # extracting text from page
        text = page.extract_text()

        document = language_v1.Document(type_=language_v1.Document.Type.PLAIN_TEXT)
        document.content = text
        # Send an API request to Google Natural Language API to censor information
        request = language_v1.AnalyzeEntitiesRequest(
            document=document,
        )

        # Make the request to Google Cloud Language Client to analyse the text
        response = language_client.analyze_entities(request=request)

        # Extract a list of all entities with personally identifiable information
        entities: list[language_v1.Entity] = [
            _entity
            for _entity in response.entities
            if _entity.type_
            in [
                language_v1.Entity.Type.PERSON,
                language_v1.Entity.Type.ADDRESS,
                language_v1.Entity.Type.LOCATION,
                language_v1.Entity.Type.PHONE_NUMBER,
            ]
        ]

        # list all the individual words in each entity. These will be replaced with *****
        words_to_change = []
        if len(entities) > 0:
            for entity in entities:
                original_texts = [
                    _entity_mention.text.content for _entity_mention in entity.mentions
                ]
                for censor_word in original_texts:
                    new_lines = censor_word.split("\n")
                    for new_line in new_lines:
                        address_split = new_line.split(",")
                        for address_part in address_split:
                            words_to_change.append(address_part)

        print(words_to_change)
        # Replace each word
        for word in words_to_change:
            text = text.replace(word, "*****")

        # Find any email addresses and also replace them
        emails = re.findall(EMAIL_PATTERN, text)
        for email in emails:
            text = text.replace(email, "*****")
        print(text)  #

        plain_text += text
        plain_text += "\n"

    blob: Blob = bucket.blob("example.txt")  # Replace with document ID

    # Upload the content as text
    blob.upload_from_string(plain_text, content_type="text/plain")
