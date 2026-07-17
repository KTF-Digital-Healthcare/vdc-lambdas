import base64
import json
import os

import google
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

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

CREDENTIALS_FP = ""

def moderate_image_bytes(image_bytes, features, safesearch_endpoint, headers,):

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "requests": [
            {
                "image": {"content": image_b64},
                "features": features,
            }
        ]
    }
    resp = requests.post(
        safesearch_endpoint,
        headers=headers,
        data=json.dumps(payload),
        timeout=30,
    )
    resp.raise_for_status()  # raises HTTPError if Vision returns 4xx/5xx

    fa = resp.json()["responses"][0].get("faceAnnotations", None)
    if not fa:
        return None

    return fa  # e.g. {"adult":"VERY_UNLIKELY", "spoof":"UNLIKELY", ...}

def lambda_handler(*args, **kwargs):

    # credentials = service_account.Credentials.from_service_account_info(
    #     service_account_credentials,
    # )

    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FP,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    # Force-refresh the credentials to populate credentials.token
    auth_request = Request()
    credentials.refresh(auth_request)  # <--- This fetches the token

    # Re-use the same HTTP transport for every refresh
    features: list[dict] = [{"type": "FACE_DETECTION"}]
    safesearch_endpoint: str = "https://vision.googleapis.com/v1/images:annotate"

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }

    image_file_path = "test_images/example_radiograph.jpg"
    with open(image_file_path, "rb") as image_file:
        image_bytes = image_file.read()

    try:
        verdict = moderate_image_bytes(image_bytes, features, safesearch_endpoint, headers,)
    except Exception as exc:
        print("Vision API call failed")
        raise exc

    if verdict is None:
        # Image has no face detected within it. This could be a radiograph or just teeth. We can transfer this image
        # over
        print("No facial features found")
        return

    # Image has a full face and should not be transferred over as it has identifying features
    print("Facial features found")
    return

if __name__=="__main__":
    lambda_handler(None, None)