import json

def get_patient_records(patient_id):

    with open("data/patients.json") as f:
        patients = json.load(f)

    return patients.get(patient_id, {})