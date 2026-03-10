from openai import AzureOpenAI
import os
from dotenv import load_dotenv

from agents.retriever_agent import get_patient_records
from agents.planner_agent import generate_care_plan
from agents.executor_agent import execute_care_plan

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT")


def route_user_query(user_query, patient_id="patient_1"):

    prompt = f"""
You are a medical AI router.

Decide which system agent should handle the user request.

Agents available:
1. planner → questions about medication schedule, care plans
2. retriever → questions about medical records or history
3. executor → scheduling, reminders, actions

User query:
{user_query}

Respond with ONLY one word:

planner
retriever
executor
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    agent = response.choices[0].message.content.strip().lower()

    return agent


def handle_user_query(user_query):

    agent = route_user_query(user_query)

    if agent == "retriever":
        return get_patient_records("patient_1")

    elif agent == "planner":
        return {
            "message": "Planner agent should generate care plan."
        }
    elif agent == "executor":
        return {
            "message": "Executor agent handles reminders and scheduling."
        }
    else:
        return {"message": "Sorry, I could not understand the request."}