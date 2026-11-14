"""API for the clinic's new site: the converter as a service, no pages.

The new site sends a ClinicCards PDF and gets back the patient plan (PDF), a ready patient-cabinet page and the plan
as JSON. Every call carries the secret key:  Authorization: Bearer <CONVERTER_API_KEY>.
Several keys may be set, comma-separated, so a key can be replaced without a gap. With no key set the API is off (503).

    POST   /api/v1/plans                  multipart: plan = PDF from ClinicCards, pano = optional panoramic image (JPG/PNG)
    GET    /api/v1/plans/{id}             the same JSON as the POST answer, while the files are kept
    GET    /api/v1/plans/{id}/plan.pdf    the patient PDF
    GET    /api/v1/plans/{id}/preview.png first page as an image
    GET    /api/v1/plans/{id}/cabinet.html  the patient cabinet as one self-contained page (progress from the plan's marks)
    DELETE /api/v1/plans/{id}             delete now instead of waiting for the expiry

Files live TTL_MINUTES (the same store as the office pages); the source PDF is deleted right after reading.
Errors are JSON: {"error": code, "message": text in Ukrainian for staff, "detail": ...} — see docs/API.md.
"""
import hmac
import json
import os
import secrets
import shutil

from starlette.concurrency import run_in_threadpool
from starlette.responses import FileResponse, JSONResponse, Response

import parse_clinicards as P
import render as R
from portal.cabinet import render_cabinet

from .sources import dictionary, status_from_plan

API_KEYS = [k.strip() for k in os.environ.get("CONVERTER_API_KEY", "").split(",") if len(k.strip()) >= 24]


def _err(status, code, message, **extra):
    return JSONResponse({"error": code, "message": message, **extra}, status_code=status)


def authorised(request):
    head = request.headers.get("authorization", "")
    key = head[7:].strip() if head.lower().startswith("bearer ") else ""
    return bool(key) and any(hmac.compare_digest(key, k) for k in API_KEYS)


def need_key(handler):
    async def wrapped(request):
        if not API_KEYS:
            return _err(503, "api_off", "API вимкнено: на сервері не задано CONVERTER_API_KEY.")
        if not authorised(request):
            return _err(401, "bad_key", "Немає ключа або ключ невірний.")
        return await handler(request)
    return wrapped


def _summary(job, plan, meta, base):
    """what the new site needs to show the plan in its own design, plus links to the ready files"""
    view, missing, _ = R.build(plan, dictionary())
    phases = []
    for ph in view["phases"]:
        phases.append({
            "num": ph["num"], "label": ph["label"], "title": ph["head"], "timing": ph["timing"], "duration": ph["duration"],
            "note": ph["note"], "done": ph["done_state"], "total": ph["total"],
            "blocks": [{
                "title": b["title"], "plain": b["plain"], "done": b["done_state"], "total": b["total"],
                "rows": [{
                    "name": r["name"], "teeth": r["teeth"], "description": r["desc_full"], "included": r["incl"],
                    "lab": bool(r["lab"]), "unit_price": r["unit"], "discount": r["disc"], "qty": str(r["qty"]),
                    "price": str(r["final"]), "currency": r["currency"], "done": r["done_state"],
                } for r in b["rows"]],
            } for b in ph["blocks"]],
        })
    h = view["h"]
    token = job.name
    return {
        "id": token,
        "expires_at": int(meta["created"] + _ttl()),   # unix time; after it the files are gone
        "patient": h.get("patient", ""), "doctor": h.get("doctor", ""), "date": h.get("date", ""),
        "total": view["grand"], "done_total": view.get("done_total") or "", "left_total": view.get("left_total") or "",
        "sums": meta["sum"],                      # exact sums per currency, as strings ("12345.00"), checked against the PDF
        "phases": phases,
        "missing_descriptions": sorted(set(missing)),
        "files": {
            "pdf": f"{base}/api/v1/plans/{token}/plan.pdf",
            "preview": f"{base}/api/v1/plans/{token}/preview.png",
            "cabinet": f"{base}/api/v1/plans/{token}/cabinet.html",
        },
    }


def _ttl():
    from . import app as A
    return A.TTL


def _base(request):
    return str(request.base_url).rstrip("/")


@need_key
async def create(request):
    from . import app as A           # the office pages and the API share one store and one printer
    A.cleanup()
    if int(request.headers.get("content-length") or 0) > A.MAX_PDF + A.MAX_IMG + 1024 * 1024:
        return _err(413, "too_large", "Файли завеликі. PDF — до 25 МБ, знімок — до 20 МБ.")
    try:
        form = await request.form()
    except Exception:  # noqa: BLE001
        return _err(400, "bad_upload", "Файл не завантажився. Надішліть multipart/form-data з полем plan.")
    up, pano = form.get("plan"), form.get("pano")
    pdf_bytes = await up.read() if up is not None and hasattr(up, "read") else b""
    pano_bytes = await pano.read() if pano is not None and hasattr(pano, "read") else b""
    if not pdf_bytes:
        return _err(400, "no_file", "Додайте PDF плану лікування з ClinicCards (поле plan).")
    if not pdf_bytes.startswith(b"%PDF"):
        return _err(400, "not_pdf", "Це не PDF-файл. Потрібен план лікування, вивантажений з ClinicCards у PDF.")
    if len(pdf_bytes) > A.MAX_PDF or len(pano_bytes) > A.MAX_IMG:
        return _err(413, "too_large", "Файли завеликі. PDF — до 25 МБ, знімок — до 20 МБ.")
    if pano_bytes:
        try:
            A.Image.open(A.io.BytesIO(pano_bytes)).verify()
        except Exception:  # noqa: BLE001
            return _err(400, "bad_image", "Панорамний знімок має бути фото у форматі JPG або PNG.")
    token = secrets.token_urlsafe(18)
    job = A.DATA_DIR / token
    job.mkdir()
    try:
        meta = await run_in_threadpool(A._convert, job, pdf_bytes, pano_bytes)
    except SystemExit as e:
        shutil.rmtree(job, ignore_errors=True)
        return _err(422, "sums_mismatch", "Суми в PDF не сходяться з позиціями — план не створено.", detail=str(e).replace("STOP: ", ""))
    except P.CollapsedBlocks as e:
        shutil.rmtree(job, ignore_errors=True)
        return _err(422, "collapsed_blocks", "У PDF блоки згорнуті: видно лише суми, а послуг немає. "
                    "Розгорніть блоки в ClinicCards і збережіть PDF ще раз.", blocks=[R.clean_title(t) for t in e.titles])
    except ValueError as e:
        shutil.rmtree(job, ignore_errors=True)
        return _err(422, "unreadable", "Не вдалося прочитати цей PDF як план лікування з ClinicCards.", detail=str(e))
    except Exception as e:  # noqa: BLE001
        shutil.rmtree(job, ignore_errors=True)
        return _err(500, "internal", "Не вдалося створити план. Спробуйте ще раз.", detail=f"{type(e).__name__}: {e}")
    plan = json.loads((job / "plan.json").read_text())
    data = await run_in_threadpool(_summary, job, plan, meta, _base(request))
    return JSONResponse(data, status_code=201)


def _job(request):
    from . import app as A
    return A.job_dir(request.path_params["id"])


@need_key
async def get(request):
    from . import app as A
    job = _job(request)
    if not job:
        return _err(404, "gone", "План уже видалено або такого немає.")
    plan = json.loads((job / "plan.json").read_text())
    return JSONResponse(await run_in_threadpool(_summary, job, plan, A.read_meta(job), _base(request)))


@need_key
async def file(request):
    from . import app as A
    job = _job(request)
    if not job:
        return _err(404, "gone", "План уже видалено або такого немає.")
    what = request.path_params["what"]
    if what == "plan.pdf":
        meta = A.read_meta(job)
        return FileResponse(job / meta["pdf"], media_type="application/pdf", filename=meta["pdf"])
    if what == "preview.png":
        return FileResponse(job / "preview.png", media_type="image/png")
    if what == "cabinet.html":
        plan = json.loads((job / "plan.json").read_text())
        out = job / "cabinet.html"
        if not out.exists():
            await run_in_threadpool(render_cabinet, plan, dictionary(), status_from_plan(plan), out)
        return FileResponse(out, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-store"})
    return _err(404, "no_such_file", "Є лише plan.pdf, preview.png і cabinet.html.")


@need_key
async def delete(request):
    job = _job(request)
    if job:
        shutil.rmtree(job, ignore_errors=True)
    return Response(status_code=204)


def routes():
    from starlette.routing import Route
    return [
        Route("/api/v1/plans", create, methods=["POST"]),
        Route("/api/v1/plans/{id}", get, methods=["GET"]),
        Route("/api/v1/plans/{id}", delete, methods=["DELETE"]),
        Route("/api/v1/plans/{id}/{what}", file, methods=["GET"]),
    ]

