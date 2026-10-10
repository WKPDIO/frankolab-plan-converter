"""FrankoLab · the web app: the office converter and the patient cabinet in one place.

Office  (one shared password)   /login → /  upload a ClinicCards PDF (+ panorama) → /r/<token>  download the patient PDF,
                                preview the patient cabinet. Files live in a temporary folder and are deleted after TTL_MINUTES
                                or on «Видалити зараз»; nothing about patients is kept.
Patient                         /cabinet  login (by phone, once ClinicCards is connected) · /cabinet/demo  demo cabinet.

Settings (environment variables):
  OFFICE_PASSWORD   the office password (required)
  SECRET_KEY        signs the login cookie (required in production; any long random string)
  COOKIE_SECURE     "1" behind https (default), "0" for local runs over http
  TTL_MINUTES       how long a converted plan is kept (default 60)
  DATA_DIR          where temporary files go (default: system temp)
  CLINICCARDS_API_KEY   turns on the live patient cabinet once the API methods are filled in (web/clinicards_api.py)

Run locally:  OFFICE_PASSWORD=... SECRET_KEY=... COOKIE_SECURE=0 uvicorn web.app:app --reload
"""
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.concurrency import run_in_threadpool  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response  # noqa: E402
from starlette.routing import Mount, Route  # noqa: E402
from starlette.staticfiles import StaticFiles  # noqa: E402
from starlette.templating import Jinja2Templates  # noqa: E402

import parse_clinicards as P  # noqa: E402
from portal.cabinet import render_cabinet  # noqa: E402
from render import clean_title, render_plan  # noqa: E402

from .clinicards_api import ClinicCardsClient  # noqa: E402
from .icons import icon  # noqa: E402
from .sources import DemoSource, PdfSource, dictionary, status_from_plan  # noqa: E402

OFFICE_PASSWORD = os.environ.get("OFFICE_PASSWORD", "")
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)     # random per start if unset: logins reset on restart
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "1") != "0"
TTL = int(os.environ.get("TTL_MINUTES", "60")) * 60
DATA_DIR = Path(os.environ.get("DATA_DIR") or Path(tempfile.gettempdir()) / "frankolab-plans")
DATA_DIR.mkdir(parents=True, exist_ok=True)
SESSION_DAYS = 30
MAX_PDF = 25 * 1024 * 1024
MAX_IMG = 20 * 1024 * 1024
COOKIE = "fl_office"

templates = Jinja2Templates(directory=str(ROOT / "web" / "templates"))
templates.env.globals["icon"] = icon
RENDER_LOCK = threading.Lock()          # one Chromium at a time keeps memory low on a small server
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


# ---- office session: an HMAC-signed cookie with an expiry ----------------------------------------
def _sign(value):
    return hmac.new(SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()


def make_session():
    exp = str(int(time.time()) + SESSION_DAYS * 86400)
    return f"{exp}.{_sign(exp)}"


def is_office(request):
    raw = request.cookies.get(COOKIE, "")
    exp, _, sig = raw.partition(".")
    return bool(exp.isdigit() and hmac.compare_digest(sig, _sign(exp)) and int(exp) > time.time())


_attempts = {}


def too_many_attempts(ip):
    """at most 10 wrong passwords per 10 minutes from one address"""
    now = time.time()
    recent = [t for t in _attempts.get(ip, []) if now - t < 600]
    _attempts[ip] = recent
    return len(recent) >= 10


def need_office(handler):
    async def wrapped(request):
        if not is_office(request):
            return RedirectResponse(f"/login?next={request.url.path}", status_code=303)
        return await handler(request)
    return wrapped


# ---- temporary store ------------------------------------------------------------------------------
def cleanup():
    now = time.time()
    for d in DATA_DIR.iterdir():
        try:
            if d.is_dir() and now - d.stat().st_mtime > TTL:
                shutil.rmtree(d, ignore_errors=True)
        except FileNotFoundError:
            pass


def job_dir(token):
    if not TOKEN_RE.match(token or ""):
        return None
    d = DATA_DIR / token
    return d if d.is_dir() else None


def read_meta(d):
    return json.loads((d / "meta.json").read_text())


# ---- pages ---------------------------------------------------------------------------------------
async def login_page(request):
    if is_office(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html.j2", {"error": None, "next": request.query_params.get("next", "/")})


async def login_submit(request):
    form = await request.form()
    ip = request.client.host if request.client else "?"
    nxt = form.get("next") or "/"
    if not nxt.startswith("/") or nxt.startswith("//"):
        nxt = "/"
    if too_many_attempts(ip):
        return templates.TemplateResponse(request, "login.html.j2", {"error": "Забагато спроб. Спробуйте через 10 хвилин.", "next": nxt}, status_code=429)
    if not OFFICE_PASSWORD or not hmac.compare_digest(str(form.get("password", "")), OFFICE_PASSWORD):
        _attempts.setdefault(ip, []).append(time.time())
        msg = "Невірний пароль." if OFFICE_PASSWORD else "Пароль офісу ще не налаштований на сервері (OFFICE_PASSWORD)."
        return templates.TemplateResponse(request, "login.html.j2", {"error": msg, "next": nxt}, status_code=401)
    resp = RedirectResponse(nxt, status_code=303)
    resp.set_cookie(COOKIE, make_session(), max_age=SESSION_DAYS * 86400, httponly=True, secure=COOKIE_SECURE, samesite="lax")
    return resp


async def logout(request):
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(COOKIE)
    return resp


@need_office
async def office(request):
    cleanup()
    return templates.TemplateResponse(request, "office.html.j2", {"ttl_min": TTL // 60})


def _convert(job, pdf_bytes, pano_bytes):
    """the heavy part, run in a worker thread"""
    src = job / "source.pdf"
    src.write_bytes(pdf_bytes)
    try:
        plan = PdfSource(src).plan()
    finally:
        src.unlink(missing_ok=True)              # the original ClinicCards file is not kept
    (job / "plan.json").write_text(json.dumps(plan, ensure_ascii=False))
    pano = None
    if pano_bytes:
        img = Image.open(io.BytesIO(pano_bytes))
        img = img.convert("RGB")
        if img.width > 2400:
            img = img.resize((2400, round(img.height * 2400 / img.width)))
        pano = job / "pano.jpg"
        img.save(pano, "JPEG", quality=88)       # re-encoded: no metadata from the original file
    with RENDER_LOCK:
        pdf, report = render_plan(job / "plan.json", job, pano=pano, preview=job / "preview.png")
    for f in job.glob("*.html"):
        f.unlink()
    report["sum"] = {k: str(v) for k, v in report["sum"].items()}
    report["printed"] = {k: str(v) for k, v in report["printed"].items()}
    meta = {"pdf": pdf.name, "created": time.time(), "has_pano": bool(pano), **report}
    (job / "meta.json").write_text(json.dumps(meta, ensure_ascii=False))
    return meta


@need_office
async def convert(request):
    cleanup()
    if int(request.headers.get("content-length") or 0) > MAX_PDF + MAX_IMG + 1024 * 1024:
        return templates.TemplateResponse(request, "office.html.j2", {"error": "Файли завеликі. PDF — до 25 МБ, знімок — до 20 МБ.",
                                                                       "ttl_min": TTL // 60}, status_code=413)
    try:
        form = await request.form()
    except Exception:  # noqa: BLE001  malformed upload
        return templates.TemplateResponse(request, "office.html.j2", {"error": "Файл не завантажився. Спробуйте ще раз.",
                                                                       "ttl_min": TTL // 60}, status_code=400)
    up = form.get("plan")
    pano = form.get("pano")
    err = None
    pdf_bytes = await up.read() if up is not None and hasattr(up, "read") else b""
    pano_bytes = await pano.read() if pano is not None and hasattr(pano, "read") else b""
    if not pdf_bytes:
        err = "Додайте PDF плану лікування з ClinicCards."
    elif not pdf_bytes.startswith(b"%PDF"):
        err = "Це не PDF-файл. Потрібен план лікування, вивантажений з ClinicCards у PDF."
    elif len(pdf_bytes) > MAX_PDF:
        err = "Файл завеликий (понад 25 МБ)."
    elif pano_bytes and len(pano_bytes) > MAX_IMG:
        err = "Знімок завеликий (понад 20 МБ)."
    if pano_bytes and not err:
        try:
            Image.open(io.BytesIO(pano_bytes)).verify()
        except Exception:
            err = "Панорамний знімок має бути фото у форматі JPG або PNG."
    if err:
        return templates.TemplateResponse(request, "office.html.j2", {"error": err, "ttl_min": TTL // 60}, status_code=400)
    token = secrets.token_urlsafe(18)
    job = DATA_DIR / token
    job.mkdir()
    try:
        await run_in_threadpool(_convert, job, pdf_bytes, pano_bytes)
    except SystemExit as e:              # render_plan stops on any money mismatch
        shutil.rmtree(job, ignore_errors=True)
        detail = str(e).replace("STOP: ", "")
        return templates.TemplateResponse(request, "office.html.j2", {
            "error": "План не створено: суми в PDF не сходяться з позиціями, тож перевірте файл. Ми нічого не друкуємо, доки кожна сума не збігається.",
            "detail": detail, "ttl_min": TTL // 60}, status_code=422)
    except P.CollapsedBlocks as e:
        shutil.rmtree(job, ignore_errors=True)
        names = ", ".join(f"«{clean_title(t)}»" for t in e.titles)
        return templates.TemplateResponse(request, "office.html.j2", {
            "error": f"У цьому PDF блоки згорнуті — видно лише їхні суми, а послуг немає: {names}. "
                     "Розгорніть блоки в плані ClinicCards (щоб було видно кожну послугу), збережіть PDF ще раз і завантажте його.",
            "ttl_min": TTL // 60}, status_code=422)
    except ValueError as e:
        shutil.rmtree(job, ignore_errors=True)
        return templates.TemplateResponse(request, "office.html.j2", {
            "error": "Не вдалося прочитати цей PDF як план лікування з ClinicCards. Перевірте, що це план, вивантажений з картки пацієнта. "
                     "Якщо так — надішліть файл розробнику: можливо, змінився формат.",
            "detail": str(e), "ttl_min": TTL // 60}, status_code=422)
    except Exception as e:  # noqa: BLE001
        shutil.rmtree(job, ignore_errors=True)
        return templates.TemplateResponse(request, "office.html.j2", {
            "error": "Не вдалося створити план. Спробуйте ще раз; якщо повториться — надішліть цей PDF розробнику.",
            "detail": f"{type(e).__name__}: {e}", "ttl_min": TTL // 60}, status_code=500)
    return RedirectResponse(f"/r/{token}", status_code=303)


@need_office
async def result(request):
    job = job_dir(request.path_params["token"])
    if not job:
        return templates.TemplateResponse(request, "gone.html.j2", {"ttl_min": TTL // 60}, status_code=404)
    meta = read_meta(job)
    left = max(0, int((meta["created"] + TTL - time.time()) // 60))
    return templates.TemplateResponse(request, "result.html.j2", {"m": meta, "token": request.path_params["token"], "left_min": left})


@need_office
async def result_file(request):
    job = job_dir(request.path_params["token"])
    if not job:
        return Response("Файл уже видалено.", status_code=404)
    meta = read_meta(job)
    what = request.path_params["what"]
    if what == "preview.png":
        return FileResponse(job / "preview.png", media_type="image/png", headers={"Cache-Control": "private, max-age=600"})
    if what == "plan.pdf":
        inline = request.query_params.get("view") == "1"
        return FileResponse(job / meta["pdf"], media_type="application/pdf", filename=meta["pdf"],
                            content_disposition_type="inline" if inline else "attachment")
    return Response(status_code=404)


@need_office
async def result_cabinet(request):
    token = request.path_params["token"]
    job = job_dir(token)
    if not job:
        return templates.TemplateResponse(request, "gone.html.j2", {"ttl_min": TTL // 60}, status_code=404)
    plan = json.loads((job / "plan.json").read_text())
    out = job / "cabinet.html"
    await run_in_threadpool(render_cabinet, plan, dictionary(), status_from_plan(plan), out,
                            preview=True, back_url=f"/r/{token}")
    return HTMLResponse(out.read_text(), headers={"Cache-Control": "no-store"})


@need_office
async def result_delete(request):
    job = job_dir(request.path_params["token"])
    if job:
        shutil.rmtree(job, ignore_errors=True)
    return RedirectResponse("/?deleted=1", status_code=303)


# ---- patient side -------------------------------------------------------------------------------
async def patient_login(request):
    live = ClinicCardsClient().configured
    return templates.TemplateResponse(request, "patient_login.html.j2", {"live": live, "sent": False})


async def patient_login_submit(request):
    """phone → SMS code → cabinet. Becomes live once ClinicCards and an SMS provider are connected."""
    form = await request.form()
    phone = re.sub(r"\D", "", str(form.get("phone", "")))
    return templates.TemplateResponse(request, "patient_login.html.j2", {
        "live": False, "sent": False, "phone": phone,
        "notice": "Вхід для пацієнтів запрацює після підключення ClinicCards. Поки що можна подивитися демо-кабінет."})


_demo_cache = {}


async def patient_demo(request):
    """the demo cabinet on an anonymised example; public, no real patient data"""
    src = DemoSource("plan_2")
    key = (src.path.stat().st_mtime, (ROOT / "data" / "services.json").stat().st_mtime)
    if _demo_cache.get("key") != key:
        out = DATA_DIR / "demo-cabinet.html"
        await run_in_threadpool(render_cabinet, src.plan(), dictionary(), src.status(), out, home_url="/cabinet")
        _demo_cache.update(key=key, html=out.read_text())
    return HTMLResponse(_demo_cache["html"])


async def healthz(request):
    return JSONResponse({"ok": True})


async def not_found(request, exc):
    return templates.TemplateResponse(request, "gone.html.j2", {"ttl_min": TTL // 60, "not_found": True}, status_code=404)


routes = [
    Route("/login", login_page, methods=["GET"]),
    Route("/login", login_submit, methods=["POST"]),
    Route("/logout", logout, methods=["POST", "GET"]),
    Route("/", office, methods=["GET"]),
    Route("/convert", convert, methods=["POST"]),
    Route("/r/{token}", result, methods=["GET"]),
    Route("/r/{token}/cabinet", result_cabinet, methods=["GET"]),
    Route("/r/{token}/delete", result_delete, methods=["POST"]),
    Route("/r/{token}/{what}", result_file, methods=["GET"]),
    Route("/cabinet", patient_login, methods=["GET"]),
    Route("/cabinet", patient_login_submit, methods=["POST"]),
    Route("/cabinet/demo", patient_demo, methods=["GET"]),
    Route("/healthz", healthz, methods=["GET"]),
    Mount("/static", StaticFiles(directory=str(ROOT / "web" / "static")), name="static"),
    Mount("/fonts", StaticFiles(directory=str(ROOT / "assets" / "fonts")), name="fonts"),
]


class SecurityHeaders:
    """no indexing, no framing, no referrer leaks; patient files are never cached by shared caches"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                h = message.setdefault("headers", [])
                h += [(b"x-robots-tag", b"noindex, nofollow"), (b"x-frame-options", b"DENY"),
                      (b"referrer-policy", b"same-origin"), (b"x-content-type-options", b"nosniff")]
                if not any(k == b"cache-control" for k, _ in h):
                    static = scope["path"].startswith(("/static/", "/fonts/"))
                    h.append((b"cache-control", b"public, max-age=86400" if static else b"no-store"))
            await send(message)
        return await self.app(scope, receive, send_wrapper)


app = SecurityHeaders(Starlette(routes=routes, exception_handlers={404: not_found}))
