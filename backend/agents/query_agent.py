import json
import os
import re

from dotenv import load_dotenv
from openai import AzureOpenAI

from agents.executor_agent import execute_care_plan
from agents.planner_agent import generate_care_plan
from agents.retriever_agent import get_patient_records

load_dotenv()

DEFAULT_PATIENT_ID = "patient_1"
DEFAULT_PATIENT_PROFILE = {
    "wake_time": "07:00",
    "breakfast_time": "09:00",
    "lunch_time": "13:00",
    "dinner_time": "20:00",
    "sleep_time": "23:00"
}

VALID_AGENTS = {"planner", "retriever", "executor"}
AGENT_LABELS = {
    "planner": "Planner Agent",
    "retriever": "Retriever Agent",
    "executor": "Executor Agent"
}

FALLBACK_PLANNER_KEYWORDS = (
    "medicine", "medicines", "medication", "medications", "take",
    "schedule", "care plan", "careplan", "prescription", "dose",
    "follow-up", "follow up", "test", "tests", "today"
)
FALLBACK_RETRIEVER_KEYWORDS = (
    "record", "records", "history", "condition", "conditions", "diagnosis",
    "diagnoses", "allergy", "allergies", "lab", "labs", "result",
    "results", "medical", "patient", "age", "name"
)
FALLBACK_EXECUTOR_KEYWORDS = (
    "calendar", "reminder", "reminders", "create", "add",
    "schedule appointment", "appointment", "book", "set up", "setup", "notify"
)

LATEST_CONTEXT = {
    "structured_data": None,
    "care_plan": None,
    "actions": None,
    "patient_records": None
}

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT")


def set_latest_context(structured_data=None, care_plan=None, actions=None, patient_records=None):
    if structured_data is not None:
        LATEST_CONTEXT["structured_data"] = structured_data
    if care_plan is not None:
        LATEST_CONTEXT["care_plan"] = care_plan
    if actions is not None:
        LATEST_CONTEXT["actions"] = actions
    if patient_records is not None:
        LATEST_CONTEXT["patient_records"] = patient_records


def fallback_route(query: str) -> str:
    normalized_query = query.lower()

    if any(keyword in normalized_query for keyword in FALLBACK_EXECUTOR_KEYWORDS):
        return "executor"
    if any(keyword in normalized_query for keyword in FALLBACK_RETRIEVER_KEYWORDS):
        return "retriever"
    if any(keyword in normalized_query for keyword in FALLBACK_PLANNER_KEYWORDS):
        return "planner"

    return "unknown"


def call_llm(system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()


def route_user_query(query: str) -> str:
    system_prompt = """
You are a healthcare orchestration router.

Choose exactly one agent for each user query:
- planner: medication schedules, care plans, tests, prescriptions
- retriever: patient records, history, conditions, labs
- executor: actions like reminders, appointments, calendar tasks

Respond with exactly one word:
planner
retriever
executor
"""

    try:
        route = call_llm(system_prompt, f"User query:\n{query}").lower().strip()
        if route in VALID_AGENTS:
            return route
    except Exception:
        pass

    return fallback_route(query)


def get_patient_context(patient_id: str):
    if LATEST_CONTEXT["patient_records"]:
        return LATEST_CONTEXT["patient_records"]

    records = get_patient_records(patient_id)
    LATEST_CONTEXT["patient_records"] = records
    return records


def get_or_create_care_plan(patient_id: str):
    if LATEST_CONTEXT["care_plan"]:
        return LATEST_CONTEXT["care_plan"]

    structured_data = LATEST_CONTEXT["structured_data"]
    if not structured_data:
        return None

    patient_records = get_patient_context(patient_id)
    care_plan = generate_care_plan(
        structured_data,
        DEFAULT_PATIENT_PROFILE,
        patient_records
    )
    LATEST_CONTEXT["care_plan"] = care_plan
    return care_plan


def get_or_create_actions(patient_id: str):
    if LATEST_CONTEXT["actions"]:
        return LATEST_CONTEXT["actions"]

    care_plan = get_or_create_care_plan(patient_id)
    if not care_plan:
        return []

    actions = execute_care_plan(care_plan)
    LATEST_CONTEXT["actions"] = actions
    return actions


def get_agent_output(agent_name: str, patient_id: str):
    if agent_name == "planner":
        return get_or_create_care_plan(patient_id)

    if agent_name == "retriever":
        return get_patient_context(patient_id)

    if agent_name == "executor":
        return get_or_create_actions(patient_id)

    return None


def format_executor_confirmation(actions):
    if not actions:
        return (
            "I need a generated care plan before I can create reminders or "
            "appointments. Upload a prescription first."
        )

    reminder_actions = [
        action for action in actions
        if isinstance(action, dict) and action.get("action") == "create_reminder"
    ]
    follow_up_actions = [
        action for action in actions
        if isinstance(action, dict) and action.get("action") == "schedule_followup"
    ]

    if reminder_actions:
        return "Medication reminders were added to your calendar."

    if follow_up_actions:
        return "Your follow-up appointment has been scheduled successfully."

    return "Your requested healthcare action was completed successfully."


def format_bullet_list(items):
    items = list(items)

    if not items:
        return "• None available"

    return "\n".join(f"• {item}" for item in items)


def format_planner_fallback(query: str, agent_output):
    if not agent_output:
        return (
            "I do not have a generated care plan yet.\n\n"
            "Upload a prescription first so I can answer medication and test questions."
        )

    normalized_query = query.lower()
    schedule = agent_output.get("daily_schedule", [])
    monitoring = agent_output.get("monitoring", [])
    follow_up = agent_output.get("follow_up", "")

    sections = []

    if any(word in normalized_query for word in ("test", "tests", "monitor", "monitoring")):
        sections.append("Upcoming tests")
        sections.append("")
        sections.append(format_bullet_list(
            f"{item.get('day', 'Scheduled')} — {item.get('task', 'Monitoring task')}"
            for item in monitoring
        ))

        if follow_up:
            sections.extend(["", "Regular monitoring", "", f"• {follow_up}"])

        return "\n".join(sections)

    if any(word in normalized_query for word in ("follow-up", "follow up", "appointment")):
        if follow_up:
            return f"Follow-up plan\n\n{follow_up}"
        return "Follow-up plan\n\nNo follow-up is scheduled yet."

    sections.append("Today's medications")
    sections.append("")
    sections.append(format_bullet_list(
        f"{item.get('time', 'Time TBD')} — {item.get('task', 'Medication task')}"
        for item in schedule
    ))

    if monitoring and any(word in normalized_query for word in ("plan", "care", "prescription", "explain")):
        sections.extend([
            "",
            "Upcoming tests",
            "",
            format_bullet_list(
                f"{item.get('day', 'Scheduled')} — {item.get('task', 'Monitoring task')}"
                for item in monitoring
            )
        ])

    if follow_up and any(word in normalized_query for word in ("plan", "care", "prescription", "explain")):
        sections.extend(["", "Follow-up plan", "", follow_up])

    return "\n".join(sections)


def format_retriever_fallback(agent_output):
    if not agent_output:
        return "Patient Information\n\nNo patient records are available right now."

    lines = [
        "Patient Information",
        "",
        f"Name: {agent_output.get('name', 'Unknown patient')}",
        f"Age: {agent_output.get('age', 'Unknown')}",
        "",
        "Conditions",
        format_bullet_list(agent_output.get("conditions", [])),
        "",
        "Current medications",
        format_bullet_list(agent_output.get("current_medications", []))
    ]

    allergies = agent_output.get("allergies", [])
    if allergies:
        lines.extend(["", "Allergies", format_bullet_list(allergies)])

    return "\n".join(lines)


def normalize_formatted_response(text: str) -> str:
    cleaned = text.replace("**", "").replace("__", "").replace("`", "")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    lines = []
    for raw_line in cleaned.split("\n"):
        line = raw_line.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue

        line = re.sub(r"^\d+\.\s*", "", line)

        if line.startswith(("-", "*")):
            line = f"• {line[1:].strip()}"

        if line.startswith("•"):
            line = f"• {line[1:].strip()}"

        lines.append(line)

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def needs_structured_fallback(formatted_text: str, agent_name: str, agent_output) -> bool:
    if not formatted_text:
        return True

    if "**" in formatted_text or "`" in formatted_text:
        return True

    if agent_name == "planner":
        has_list_data = bool(
            (agent_output or {}).get("daily_schedule") or
            (agent_output or {}).get("monitoring")
        )
        if has_list_data and "•" not in formatted_text:
            return True

    if agent_name == "retriever":
        has_list_data = bool(
            (agent_output or {}).get("conditions") or
            (agent_output or {}).get("current_medications")
        )
        if has_list_data and "•" not in formatted_text:
            return True

    return False


def add_agent_label(agent_name: str, response_text: str) -> str:
    label = AGENT_LABELS.get(agent_name, "Assistant")
    return f"Agent used: {label}\n\n{response_text}"


def format_agent_response(query: str, agent_name: str, agent_output):
    if agent_name == "executor":
        return add_agent_label(agent_name, format_executor_confirmation(agent_output))

    if not agent_output:
        if agent_name == "planner":
            return add_agent_label(agent_name, (
                "I do not have a generated care plan yet. Upload a prescription "
                "first so I can answer medication and test questions."
            ))
        if agent_name == "retriever":
            return add_agent_label(
                agent_name,
                "I could not find any patient records right now."
            )

    system_prompt = """
You are a healthcare AI assistant.

You will be given:
1. The user's question
2. The selected backend agent
3. The agent output in JSON

Write a concise natural language reply for the user.

Rules:
- Do not show raw JSON
- Only include information relevant to the user's question
- Use the bullet character • for list items
- Put each list item on its own line
- Never write lists inline inside a paragraph
- Do not use markdown symbols such as ** or -
- Keep the answer short and clear
- If times are available, include them
- If no relevant information exists, say so plainly
- Start with a short section title when useful
"""

    user_prompt = (
        f"User query:\n{query}\n\n"
        f"Selected agent:\n{agent_name}\n\n"
        f"Agent output JSON:\n{json.dumps(agent_output, indent=2)}"
    )

    try:
        formatted = normalize_formatted_response(call_llm(system_prompt, user_prompt))
        if needs_structured_fallback(formatted, agent_name, agent_output):
            raise ValueError("Unstructured formatter output")
        return add_agent_label(agent_name, formatted)
    except Exception:
        if agent_name == "retriever":
            return add_agent_label(agent_name, format_retriever_fallback(agent_output))

        if agent_name == "planner":
            return add_agent_label(agent_name, format_planner_fallback(query, agent_output))

        return add_agent_label(agent_name, "I completed your request.")


def handle_user_query(query: str):
    patient_id = DEFAULT_PATIENT_ID

    try:
        agent_name = route_user_query(query)
        if agent_name not in VALID_AGENTS:
            return (
                "I can help with medications, care plans, tests, reminders, "
                "and medical records. What would you like to know?"
            )

        agent_output = get_agent_output(agent_name, patient_id)
        return format_agent_response(query, agent_name, agent_output)
    except Exception:
        return (
            "I ran into a problem while checking your healthcare information. "
            "Please try again after uploading a prescription."
        )
