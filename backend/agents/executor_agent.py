import datetime


def execute_care_plan(care_plan):

    actions = []

    # Medication reminders
    for task in care_plan.get("daily_schedule", []):
        actions.append({
            "action": "create_reminder",
            "time": task["time"],
            "task": task["task"]
        })

    # Monitoring tasks
    for monitor in care_plan.get("monitoring", []):
        actions.append({
            "action": "health_check",
            "day": monitor["day"],
            "task": monitor["task"]
        })

    # Follow-up appointment
    if care_plan.get("follow_up"):
        actions.append({
            "action": "schedule_followup",
            "details": care_plan["follow_up"]
        })

    return actions