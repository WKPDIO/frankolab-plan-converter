"""Where a patient's plan and progress come from.

Every source returns the same two things, so the PDF, the office preview and the patient cabinet never care where
the data came from:
    plan   — the dict parse_clinicards.parse() produces (header, phases → blocks → items, terms, totals)
    status — {"done": [{key, tooth, date}], "payments": [{date, amount, currency}], "demo"?: bool}

Today:  PdfSource (the office uploads a ClinicCards PDF) and DemoSource (an anonymised example with made-up progress).
Later:  ClinicCardsSource reads everything from the ClinicCards API — or, if the API has no treatment plans,
        takes the plan from a PDF uploaded once and the progress and payments from the API.
"""
import json
from pathlib import Path

import parse_clinicards as P
from portal.cabinet import demo_status

from .clinicards_api import ClinicCardsClient, to_status

ROOT = Path(__file__).resolve().parent.parent
EMPTY_STATUS = {"done": [], "payments": []}


def dictionary():
    """services, categories, pictures — re-read on every call so edits to data/services.json apply at once"""
    return json.loads((ROOT / "data" / "services.json").read_text())


class PdfSource:
    """a plan uploaded as a ClinicCards PDF; no progress yet"""

    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path)

    def plan(self):
        try:
            plan = P.parse(str(self.pdf_path))
        except Exception as e:  # noqa: BLE001  an unknown layout: not a ClinicCards plan, or a format change
            raise ValueError(f"could not read the plan: {type(e).__name__}: {e}") from e
        if not plan.get("phases") or not any(b["items"] for ph in plan["phases"] for b in ph["blocks"]):
            raise ValueError("not a ClinicCards treatment plan")
        return plan

    def status(self):
        return dict(EMPTY_STATUS)


class DemoSource:
    """an anonymised example plan with believable made-up progress and payments"""

    def __init__(self, example="plan_2"):
        self.path = ROOT / "examples" / f"{example}.json"

    def plan(self):
        plan = json.loads(self.path.read_text())
        plan["header"].update(patient="Пацієнтка Олена", doctor="FrankoLab")     # a clearly made-up person for the demo
        return plan

    def status(self):
        return demo_status(self.plan(), dictionary())


class ClinicCardsSource:
    """a patient's live data from ClinicCards. plan_fallback — a plan from an uploaded PDF, used if the API has no plans"""

    def __init__(self, patient_id, client=None, plan_fallback=None):
        self.patient_id = patient_id
        self.client = client or ClinicCardsClient()
        self.plan_fallback = plan_fallback

    def plan(self):
        try:
            plans = self.client.treatment_plans(self.patient_id)
            if plans:
                return plans[0]
        except NotImplementedError:
            pass
        if self.plan_fallback is not None:
            return self.plan_fallback
        raise LookupError("no treatment plan for this patient")

    def status(self):
        return to_status(self.client.performed_works(self.patient_id), self.client.payments(self.patient_id))
