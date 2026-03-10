from openai import AzureOpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()

OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

client = AzureOpenAI(
    api_key=OPENAI_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=OPENAI_ENDPOINT
)


def generate_care_plan(structured_data, patient_profile, patient_records):

    # --- Normalize frequency text ---
    for med in structured_data.get("medications", []):
        freq = med.get("frequency", "").lower()
        freq = freq.replace("take one tablet", "").replace("take 1 tablet", "")
        med["frequency"] = freq.strip()

    prompt = f"""
You are an AI healthcare planning agent.

Your job is to convert prescriptions into a structured daily care plan.

Follow these rules carefully:

MEDICATION SCHEDULING:

1. If medicine says "after meals":
   schedule it 15 minutes after the meal time.

2. If frequency is "twice daily after meals":
   schedule after breakfast and dinner.

3. If frequency is "once daily in the morning":
   schedule shortly after wake_time.

4. If medicine is "at bedtime":
   schedule 30 minutes before sleep_time.

5. If frequency is unclear, choose the safest reasonable time.

MONITORING RULES:

1. If monitoring tests are mentioned (blood sugar, HbA1c etc),
   schedule them logically.

2. Blood sugar monitoring should occur twice per week.

SAFETY RULES:

1. Look at patient medical records.
2. Warn if medications might conflict with existing conditions.
3. If no issues exist return empty warnings.

Patient lifestyle profile:
{patient_profile}

Patient medical records:
{patient_records}

Prescription data:
{structured_data}

Return ONLY JSON using this format:

{{
 "daily_schedule":[
   {{"time":"","task":"","type":"medication"}}
 ],
 "monitoring":[
   {{"day":"","task":""}}
 ],
 "warnings":[],
 "follow_up":""
}}
"""

    response = client.chat.completions.create(
        model=OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    result = response.choices[0].message.content

    # Remove markdown formatting if present
    result = result.replace("```json", "").replace("```", "").strip()

    care_plan = json.loads(result)

    # --- Sort schedule chronologically ---
    if "daily_schedule" in care_plan:
        care_plan["daily_schedule"].sort(key=lambda x: x["time"])

    return care_plan