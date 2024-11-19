from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
import google.auth
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import tempfile
import json

load_dotenv()
# Initialize FastAPI app
app = FastAPI()
def get_credentials():
    creds_json_str = json.dumps(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
    if creds_json_str is None:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON not found in environment")
 
    # create a temporary file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as temp:
        temp.write(creds_json_str) # write in json format
        temp_filename = temp.name
 
    return temp_filename
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= get_credentials()





# Define a Pydantic model for the request body
class BucketRequest(BaseModel):
    bucket_name: str
    location: str = "US"  # default location

def get_access_token():
    """Obtain an access token for the service account with the correct scope."""
    credentials, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token, project

def gcp_create_bucket(bucket_name: str, location: str):
    """Creates a new GCS bucket using the Google Cloud Storage API."""
    access_token, project = get_access_token()
    
    # Set the API endpoint and headers
    url = f"https://storage.googleapis.com/storage/v1/b?project={project}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "name": bucket_name,
        "location": location,
    }

    # Make the request to create the bucket
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return f"Bucket {bucket_name} created in {location}."
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Failed to create bucket: {response.text}")

@app.post("/create_bucket")
async def create_bucket(request: BucketRequest):
    """Endpoint to create a GCS bucket with a specified name and location."""
    result = gcp_create_bucket(request.bucket_name, request.location)
    return {"message": result}