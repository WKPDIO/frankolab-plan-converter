# API конвертера планів — для розробників нового сайту

Конвертер працює окремим сервісом. Новий сайт (кабінет пацієнта) надсилає йому PDF плану лікування з ClinicCards
і отримує:

- готовий PDF для пацієнта;
- готову сторінку кабінету пацієнта (одна HTML-сторінка, все всередині);
- план у JSON — етапи, блоки, послуги з описами, суми, — щоб показати його у власному дизайні сайту.

Адреса сервісу: `https://frankolab-plans.onrender.com` (далі — `BASE`).

## Доступ

Кожен запит — із секретним ключем у заголовку:

```
Authorization: Bearer <CONVERTER_API_KEY>
```

Ключ задається в Render → сервіс `frankolab-plans` → Environment → `CONVERTER_API_KEY` (мінімум 24 символи;
кілька ключів — через кому, щоб замінити ключ без перерви). Без ключа на сервері API вимкнене (відповідь 503).

**Ключ — лише на сервері нового сайту.** Не вставляйте його в JavaScript, який відкривається в браузері пацієнта:
запити до конвертера робить бекенд сайту.

## Створити план

```
POST BASE/api/v1/plans
Content-Type: multipart/form-data

plan  — PDF з ClinicCards (обов'язково, до 25 МБ)
pano  — панорамний знімок JPG/PNG (необов'язково, до 20 МБ)
```

Відповідь `201`:

```json
{
  "id": "Q6lMFwxnq3BKqXE6ZyHh-57v",
  "expires_at": 1794697318,
  "patient": "Прізвище Ім'я", "doctor": "…", "date": "10.10.2026",
  "total": "58 000 грн + €10 460", "done_total": "", "left_total": "",
  "sums": {"UAH": "58000.00", "EUR": "10460.00"},
  "phases": [
    {"num": "01", "label": "Етап 1", "title": "Етап", "timing": "", "duration": "орієнтовно 10–14 днів",
     "note": "", "done": "none", "total": "…",
     "blocks": [
       {"title": "Професійна гігієна порожнини рота", "plain": "Професійне чищення зубів", "done": "none", "total": "…",
        "rows": [
          {"name": "…", "teeth": ["16", "17"], "description": "…", "included": "…", "lab": false,
           "unit_price": "2 500 грн", "discount": "−30%", "qty": "1", "price": "1750.00", "currency": "UAH", "done": "none"}
        ]}
     ]}
  ],
  "missing_descriptions": [],
  "files": {
    "pdf": "BASE/api/v1/plans/<id>/plan.pdf",
    "preview": "BASE/api/v1/plans/<id>/preview.png",
    "cabinet": "BASE/api/v1/plans/<id>/cabinet.html"
  }
}
```

- Назви блоків і послуг — точно як у ClinicCards. `plain` — коротке пояснення блоку, `description` — опис послуги.
- `done`: `all` — виконано, `some` — частково, `none` — ні (з позначок ✓/● у плані ClinicCards).
- `sums` — точні суми по валютах (рядки з двома знаками після крапки); кожна звірена з оригіналом PDF.
- `missing_descriptions` — послуги, для яких у довіднику ще немає опису (план усе одно створюється).

## Забрати файли

```
GET BASE/api/v1/plans/<id>/plan.pdf       — PDF для пацієнта
GET BASE/api/v1/plans/<id>/preview.png    — перша сторінка картинкою
GET BASE/api/v1/plans/<id>/cabinet.html   — кабінет пацієнта однією сторінкою
GET BASE/api/v1/plans/<id>                — той самий JSON ще раз
DELETE BASE/api/v1/plans/<id>             — видалити одразу (204)
```

Теж із ключем. **Файли зберігаються 60 хвилин** (`expires_at`, unix-час), потім видаляються. Тож новий сайт має
одразу забрати PDF (і, якщо треба, кабінет) і зберегти у себе. Оригінальний PDF з ClinicCards конвертер не зберігає
взагалі — видаляє одразу після читання.

## Помилки

Завжди JSON: `{"error": "<код>", "message": "<текст українською для персоналу>", ...}`.

| Код | HTTP | Що сталося | Що робити |
|---|---|---|---|
| `bad_key` | 401 | немає ключа або він невірний | перевірити ключ |
| `api_off` | 503 | на сервері не задано `CONVERTER_API_KEY` | задати в Render |
| `no_file`, `not_pdf`, `bad_upload` | 400 | немає файлу / не PDF | надіслати PDF у полі `plan` |
| `bad_image` | 400 | знімок не JPG/PNG | інший файл або без знімка |
| `too_large` | 413 | PDF > 25 МБ або знімок > 20 МБ | — |
| `collapsed_blocks` | 422 | у PDF згорнуті блоки (є суми, немає послуг); поле `blocks` — їхні назви | розгорнути блоки в ClinicCards, зберегти PDF ще раз |
| `sums_mismatch` | 422 | суми в PDF не сходяться з позиціями; `detail` — де саме | перевірити план у ClinicCards |
| `unreadable` | 422 | це не план ClinicCards (або змінився формат) | надіслати файл розробнику конвертера |
| `gone` | 404 | план уже видалено (минуло 60 хв) | створити ще раз |
| `internal` | 500 | збій | повторити; якщо повторюється — розробнику |

## Приклади

curl:

```bash
curl -H "Authorization: Bearer $CONVERTER_API_KEY" \
     -F "plan=@plan.pdf" -F "pano=@pano.jpg" \
     https://frankolab-plans.onrender.com/api/v1/plans
```

Node.js (18+):

```js
const form = new FormData();
form.append("plan", new Blob([pdfBuffer], { type: "application/pdf" }), "plan.pdf");
const r = await fetch("https://frankolab-plans.onrender.com/api/v1/plans", {
  method: "POST", headers: { Authorization: `Bearer ${process.env.CONVERTER_API_KEY}` }, body: form,
});
const plan = await r.json();
if (!r.ok) throw new Error(plan.message);
const pdf = await (await fetch(plan.files.pdf, { headers: { Authorization: `Bearer ${process.env.CONVERTER_API_KEY}` } })).arrayBuffer();
```

PHP:

```php
$ch = curl_init("https://frankolab-plans.onrender.com/api/v1/plans");
curl_setopt_array($ch, [
  CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true,
  CURLOPT_HTTPHEADER => ["Authorization: Bearer " . getenv("CONVERTER_API_KEY")],
  CURLOPT_POSTFIELDS => ["plan" => new CURLFile($path, "application/pdf", "plan.pdf")],
]);
$plan = json_decode(curl_exec($ch), true);
```

## Що варто знати

- Один план створюється 1–3 секунди на сервері; запити обробляються по одному.
- На безкоштовному тарифі Render сервіс засинає після 15 хвилин без запитів — перший запит після цього чекає
  до хвилини. Для роботи з новим сайтом краще платний тариф (не засинає) або тайм-аут запиту від 120 секунд.
- Сервер у Європі (Frankfurt). Дані пацієнта живуть на ньому лише 60 хвилин.
