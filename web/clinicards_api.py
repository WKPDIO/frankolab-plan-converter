"""ClinicCards API client — the skeleton the patient cabinet will run on.

What is known from ClinicCards' public notes (to be checked against the full method list from the clinic owner):
- base URL https://cliniccards.com/api, every request carries a `Token: <API key>` header and `Content-Type: application/json`;
- the key is created by the clinic owner: Settings → Other → Clinic settings → API;
- answers look like {"result": "success" | "fail", "error": ..., ...};
- limit: 60 requests per minute;
- the API covers schedule, patients, performed works and payments. Treatment plans are not mentioned — to be confirmed.

The method paths below are PLACEHOLDERS. They are named after what the cabinet needs, not after real endpoints, and raise
NotImplementedError until the real paths are filled in. Everything above this client (sources.py, the cabinet) already
works with the shapes documented in each method, so connecting the API means filling these methods in, nothing else.
"""
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("CLINICCARDS_BASE_URL", "https://cliniccards.com/api")


class ClinicCardsError(RuntimeError):
    pass


class ClinicCardsClient:
    def __init__(self, api_key=None, base_url=BASE_URL, per_minute=60):
        self.api_key = api_key or os.environ.get("CLINICCARDS_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.min_interval = 60.0 / per_minute
        self._last = 0.0
        self._lock = threading.Lock()

    @property
    def configured(self):
        return bool(self.api_key)

    # ---- transport ---------------------------------------------------------------------------
    def _request(self, method, path, params=None, body=None):
        if not self.configured:
            raise ClinicCardsError("CLINICCARDS_API_KEY is not set")
        with self._lock:                                    # stay under 60 requests per minute
            wait = self._last + self.min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method,
                                     headers={"Token": self.api_key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                payload = json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            raise ClinicCardsError(f"HTTP {e.code} on {path}") from e
        except urllib.error.URLError as e:
            raise ClinicCardsError(f"ClinicCards is unreachable: {e.reason}") from e
        if payload.get("result") == "fail":
            raise ClinicCardsError(str(payload.get("error") or "ClinicCards answered fail"))
        return payload

    def get(self, path, **params):
        return self._request("GET", path, params=params)

    # ---- what the cabinet needs (paths to be confirmed) -------------------------------------
    def find_patient_by_phone(self, phone):
        """-> {"id": ..., "name": ..., "phone": ...} or None. Used for the patient's login by phone."""
        raise NotImplementedError("fill in the patients endpoint from the ClinicCards API docs")

    def treatment_plans(self, patient_id):
        """-> list of plans in the shape of parse_clinicards.parse(): {header, phases[blocks[items]], terms, totals}.
        If the API has no plans, the clinic uploads the plan PDF once per patient (see sources.PdfSource)."""
        raise NotImplementedError("treatment plans: confirm whether the API exposes them")

    def performed_works(self, patient_id):
        """-> [{"service": <name as in the price list>, "tooth": "11" | "", "date": "YYYY-MM-DD", "price": "...", "currency": "UAH"}]"""
        raise NotImplementedError("fill in the performed-works endpoint from the ClinicCards API docs")

    def payments(self, patient_id):
        """-> [{"date": "YYYY-MM-DD", "amount": "4800.00", "currency": "UAH"}]"""
        raise NotImplementedError("fill in the payments endpoint from the ClinicCards API docs")


def to_status(works, payments):
    """performed works + payments from the API -> the status object the cabinet reads (portal/cabinet.py)"""
    return {
        "done": [{"key": w["service"], "tooth": w.get("tooth") or "", "date": w.get("date", "")} for w in works],
        "payments": [{"date": p["date"], "amount": str(p["amount"]), "currency": p.get("currency", "UAH")} for p in payments],
    }
