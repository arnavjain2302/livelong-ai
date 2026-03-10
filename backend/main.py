from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

from dotenv import load_dotenv
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from openai import AzureOpenAI
import json

from agents.retriever_agent import get_patient_records
from agents.planner_agent import generate_care_plan
from agents.executor_agent import execute_care_plan
from agents.query_agent import handle_user_query, set_latest_context

from pydantic import BaseModel

load_dotenv()

DOC_ENDPOINT = os.getenv("DOC_INTELLIGENCE_ENDPOINT")
DOC_KEY = os.getenv("DOC_INTELLIGENCE_KEY")

OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

openai_client = AzureOpenAI(
    api_key=OPENAI_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=OPENAI_ENDPOINT
)

document_client = DocumentAnalysisClient(
    endpoint=DOC_ENDPOINT,
    credential=AzureKeyCredential(DOC_KEY)
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_pdf(file_path):

    with open(file_path, "rb") as f:

        poller = document_client.begin_analyze_document(
            "prebuilt-read",
            document=f
        )

        result = poller.result()

    extracted_text = ""

    for page in result.pages:
        for line in page.lines:
            extracted_text += line.content + "\n"

    return extracted_text


def parse_prescription_with_llm(text):

    prompt = f"""
You are a medical assistant.

Extract structured medical information from this prescription text.

Return ONLY JSON.

Prescription text:
{text}

JSON format:
{{
 "medications":[
  {{
   "name":"",
   "dose":"",
   "frequency":""
  }}
 ],
 "tests":[],
 "follow_up":""
}}
"""

    response = openai_client.chat.completions.create(
        model=OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    result = response.choices[0].message.content
    result = result.replace("```json","").replace("```","")

    return json.loads(result)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

patient_profile = {
    "wake_time": "07:00",
    "breakfast_time": "09:00",
    "lunch_time": "13:00",
    "dinner_time": "20:00",
    "sleep_time": "23:00"
}

patient_records = get_patient_records("patient_1")
set_latest_context(patient_records=patient_records)

@app.get("/")
def home():
    return {"message": "LiveLong AI backend running"}

@app.post("/upload-prescription")
async def upload_prescription(file: UploadFile = File(...)):

    file_path = f"{UPLOAD_FOLDER}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted_text = extract_text_from_pdf(file_path)

    structured_data = parse_prescription_with_llm(extracted_text)

    care_plan = generate_care_plan(structured_data, patient_profile, patient_records)

    actions = execute_care_plan(care_plan)

    set_latest_context(
        structured_data=structured_data,
        care_plan=care_plan,
        actions=actions,
        patient_records=patient_records
    )

    return {
        "message": "Prescription processed",
        "extracted_data" : extracted_text,
        "structured_data": structured_data,
        "care_plan" : care_plan,
        "actions" : actions
    }

class ChatRequest(BaseModel):
    query: str


@app.post("/chat")
def chat_with_agent(request: ChatRequest):

    response = handle_user_query(request.query)

    return {"response": response}
