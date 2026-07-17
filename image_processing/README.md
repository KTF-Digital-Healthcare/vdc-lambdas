# Image Processing Lambda: Face Detection Pipeline
This AWS Lambda function integrates with the Google Cloud Vision API to inspect incoming images for identifiable facial features before they are transferred to our Google Cloud Storage (GCS) ecosystem. Its primary goal is to prevent images containing personally identifiable information (PII)—specifically human faces—from being moved over blindly.

## 📋 Architectural Logic & Workflow
The Vaidhyo platform categorizes images into two types. Our processing workflow differs depending on this metadata tag:

Radiograph: These images (X-rays, panoramic scans, etc.) do not contain surface facial features. They can bypass this detection pipeline entirely and be transferred directly straight over to our GCS bucket.

Images: These are standard photographic captures (clinical photos, teeth close-ups, etc.). These must be processed by this script to ensure an identifiable human face is not present.

## Production Pipeline Flow (To Be Implemented)
[ Vaidhyo Incoming Image ]
│
Does Category == 'Images'?
├── No ('Radiograph') ──► [ Direct Transfer to GCS ]
└── Yes ────────────────► [ Download Bytes from AWS S3 ]
│
[ Cloud Vision API Scan ]
│
Are Faces Detected?
├── Yes ──► [ Block / Flag PII ]
└── No  ──► [ Safe to Transfer to GCS ]
⚠️ Note on S3 Integration: The current local script reads a test file from disk (test_images/example_radiograph.jpg). For production execution via the Lambda handler, you will need to add boto3 logic to fetch the target image object from your S3 bucket using the incoming event data payload and pass the raw image_bytes directly into moderate_image_bytes().

## 🛠️ Configuration & Requirements
1. Prerequisites
   Google Cloud Project with the Cloud Vision API explicitly enabled.

A GCP Service Account assigned the Cloud Vision AI Viewer (roles/vision.viewer) role.

2. Local Setup
   To run the script locally for testing purposes:

Download your Service Account JSON key from the Google Cloud Console.

Place the file path into the CREDENTIALS_FP variable inside main.py:

Python
CREDENTIALS_FP = "C:\\path\\to\\your\\gcp-key.json"
Ensure your test image exists in test_images/example_radiograph.jpg (opened explicitly in "rb" binary read mode).

3. Production Environment Variables
   When deployed to AWS Lambda, authentication should switch back to utilizing environment variables (service_account_credentials object mapping). Ensure the following Lambda environment configuration variables are populated:

service_account_type

service_account_project_id

service_account_private_key_id

service_account_private_key (Replace literal \n characters with actual newlines if parsing issues occur)

service_account_private_client_email

🚀 Execution & Responses
Run the local module directly to verify connections and token generation:

Bash
python main.py
Response Evaluation Logic
The Google Vision API evaluation endpoint utilizes the FACE_DETECTION feature request. The pipeline handles the response as follows:

verdict is None: No faceAnnotations were returned by Google. The image is clean of recognizable facial layout markers (e.g., standard intraoral photos or teeth close-ups) and is safely approved for GCS migration.

verdict contains data: A face layout structure was successfully identified. The image contains identifying human profiles and is blocked from standard transfer to maintain strict compliance.