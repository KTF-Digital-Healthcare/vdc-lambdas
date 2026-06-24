# PII Redaction & PDF-to-Text Lambda Function

An AWS Lambda function that processes PDF documents, extracts text, utilizes the **Google Cloud Natural Language API** to detect and redact Personally Identifiable Information (PII), and saves the redacted text output directly to a **Google Cloud Storage (GCS)** bucket.

---

## Features

- **Multi-Cloud Processing:** Reads documents from AWS S3 or a local/container file path and writes outputs to Google Cloud Storage.
- **Smart PII Detection:** Automatically extracts and replaces sensitive entities utilizing Google Cloud's Natural Language model:
    - Names (`PERSON`)
    - Locations & Addresses (`LOCATION`, `ADDRESS`)
    - Phone Numbers (`PHONE_NUMBER`)
- **Email Redaction:** Integrates a regex fallback layer to capture and redact email addresses natively.
- **In-Memory Parsing:** Processes AWS S3 objects entirely in-memory using byte streams—no local storage needed.

---

## How It Works

1. **Fetch:** The Lambda searches for a defined `pdf_path`. If none is found, it streams the PDF object directly from the designated Amazon S3 bucket via `boto3`.
2. **Analyze:** The text is extracted page-by-page using `pypdf`. Each block of text is passed to Google Cloud’s Cloud Natural Language Client.
3. **Redact:** Identified PII strings and matching email regex occurrences are overwritten with masking characters (`*****`).
4. **Export:** The unified, plain-text output is uploaded to your specified Google Cloud Storage bucket as `example.txt`.

---

## Environment Variables Configuration

To run this function successfully, the following environment variables must be supplied to your AWS Lambda execution environment:

### Application Configurations
| Variable | Description | Example |
| :--- | :--- | :--- |
| `pdf_path` | *(Optional)* Local file path to evaluate. Set to blank to use S3 sourcing. | `/tmp/document.pdf` |
| `gcs_bucket_name` | Target Google Cloud Storage bucket where the `.txt` is saved. | `my-gcs-redacted-bucket` |
| `s3_bucket_name` | Source AWS S3 bucket name containing the target PDF. | `my-aws-source-bucket` |
| `s3_object_key` | Target key path of the PDF inside the S3 bucket. Defaults to `example.pdf`. | `incoming/user_doc.pdf` |

### Google Cloud Service Account Credentials
| Variable | Matching JSON Service Account Key |
| :--- | :--- |
| `service_account_type` | `type` |
| `service_account_project_id` | `project_id` |
| `service_account_private_key_id` | `private_key_id` |
| `service_account_private_key` | `private_key` *(See Newline Note Below)* |
| `service_account_private_client_email` | `client_email` |
| `service_account_client_id` | `client_id` |
| `service_account_auth_uri` | `auth_uri` |
| `service_account_token_uri` | `token_uri` |
| `service_account_auth_provider_x509_cert_url`| `auth_provider_x509_cert_url` |
| `service_account_client_x509_cert_url` | `client_x509_cert_url` |
| `service_account_universe_domain` | `universe_domain` |

> ⚠️ **Important Lambda Note on `service_account_private_key`:**
> When pasting your multi-line Google private key into the AWS Lambda Configuration Console, replace any '\n' with actual newlines before copying it in. The runtime code handles escaping these backslashes into standard cryptographic newlines cleanly.

---

## Setup & Deployment Requirements

### 1. External Dependencies
Make sure the following Python libraries are bundled in your Lambda Deployment Package or loaded via a custom Lambda Layer:
```text
boto3
google-cloud-language
google-cloud-storage
google-auth
pypdf