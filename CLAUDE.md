# Notes for Claude

Patient-plan converter for FrankoLab (dental clinic + in-house lab, Ivano-Frankivsk). Owners speak Ukrainian;
all patient-facing text is Ukrainian. README.md describes the pipeline and files.

## Always
- Run `python3 check_examples.py` after any change and look at the PDFs in `out/examples/`.
  Money must match the source to the cent; render_plan raises on any mismatch — never weaken that check.
- Never commit patient data (PDFs, panoramas, parsed plans with names). Examples in `examples/` are anonymised.
- Patient text follows the brand tone: plain, calm, no promises or pressure, no caps. `render.AVOID` lists banned words.

## Web app (web/)
- Starlette app: office converter behind one shared password (OFFICE_PASSWORD, HMAC cookie) + patient cabinet (/cabinet, /cabinet/demo).
- Patient files live only in DATA_DIR/<token>/ for TTL_MINUTES; the source PDF is deleted right after parsing. Keep it that way.
- All patient-facing data goes through web/sources.py; the ClinicCards client (web/clinicards_api.py) has placeholder methods
  that raise NotImplementedError until the real endpoint list is known — do not invent endpoints.
- Deploy: Dockerfile + render.yaml (Render, Frankfurt). One Chromium at a time (RENDER_LOCK) to fit a small instance.
- Web pages share the cabinet's look: web/static/app.css tokens = cabinet tokens.

## Confirmed by the clinic
- The lab makes every construction (crowns, temporaries, abutments, splints, caps, aligners, prostheses) → `lab: true`.
- Сегмент = секстант (1: 18–14, 2: 13–23, 3: 24–28, 4: 34–38, 5: 33–43, 6: 44–48).
- Price-list duplicates stay as they are.
- Included in the price: local anaesthesia, rubber dam / OptraGate (plan-wide note); endo — control X-rays and temporary filling;
  surgery — sutures; implant — implant + cover screw; формувач — the healing abutment; bone augmentation — bone material + membrane;
  sinus lift — bone material; soft-tissue augmentation — graft material; implant crowns (temporary and permanent) — Ti-base/abutment,
  screw, fixation; crowns — fixation; All-on-4 / All-on-6 implantation — all four / six implants.
  Sedation price includes the anaesthesiologist and monitoring.
- Sedation memo wins over the "eat before surgery" advice (no food 4 h before sedation). «Лише рідка їжа 30 днів» stays as written.
- Hygiene levels differ by the amount of deposits (м'який наліт < без уточнення < стійкий наліт).
- One set of implants per jaw: the implantation decides it (All-on-6 → six). A prosthesis never adds implants of its own —
  a temporary bridge "in the All-on-4 concept" on six implants is drawn on six (stagechart.implant_sites, render.plan_implant_sites).
- Stages carry over (render.build): a tooth removed earlier is not drawn again; work on a tooth implanted earlier sits on
  that (pale) implant — a plain crown there becomes a crown on the implant; a crown on a removed tooth with no implant is a
  bridge pontic (no root).
- A service given per segment or quadrant (квадрант 1–4 = 18–11, 21–28, 31–38, 41–48) means "somewhere in this area": bone/sinus/soft-tissue work on a segment is drawn only on the
  implant sites of that segment (extraction sites only when the segment gets no implant) (render.py area_fx, stagechart SITE_EFFECTS), never on healthy teeth.

## ClinicCards PDF variants (parse_clinicards.py) — all seen in real plans
- Block titles start at different x in different exports; a white block (empty or folded) is found by its grey outline.
- Row text is any shade of grey: grey rows, a darker list price before a discount, a lighter row with an icon glyph (dropped),
  white text on a blue (booked) row. Notes beside a block ("1 30.03.2026", "Візит не заплановано") are ignored.
- Total lines are groups: "€7 600.00, 9 700.00 €7 450.00" = before discount, then paid; a currency missing from the last group
  pays 0. Fully free rows may total as their list-price sum without "-100%": accepted only when every row of that currency is
  0 and the sum matches exactly (parse_clinicards._zero_free).
- A block with no rows and no sum is skipped; a block with a sum but no rows is folded → CollapsedBlocks (the site names the
  blocks and asks to unfold them in ClinicCards). A stage heading without the word "етап" is the doctor's note: shown under
  "Етап N", as written.

## Visual language (illustrations.py, stagechart.py)
- Stage chart colour code (one hue per family, keep it): crowns/prostheses Storm Blue; temporaries Sky Blue dashed
  (a full-arch prosthesis too: effect superstructure_temp, or any superstructure in a "temporary" category block);
  fillings/restorations sage green; root canals and posts coral; core build-up lavender; gum (soft tissue, crown lengthening) rose;
  bone material sand with hatching; implants, abutments, healing caps metal grey; new implant full metal, existing one paler.
- Tooth shapes (graphics.py): anatomical crowns with relief strokes (incisor lobes, canine labial ridge, premolar buccal ridge,
  molar buccal groove and cusp ridges); soft left-to-right gradient for volume.
- Neutral anatomy; Storm Blue #99aabe = what the procedure does; dashed = future/temporary; hatching = bone material;
  metal grey = implant already in place; translucent gum drawn in front; an implant crown ALWAYS narrows smoothly from the neck down to
  the implant platform (emergence profile, stagechart._implant_crown_path) — never a crown sitting on a thin post.
- Upper-jaw scenes (All-on-4, sinus lift) use panoramic proportions; trays, splint, retainer, denture are drawn from above.
- Brand palette: Rich black #212121, Graphite #474a50, Ice Blue #eaeff5, Storm Blue #99aabe, Soft Sand #d8c3a5,
  Warm Linen #f0e7de, Sky Blue #9ac2f4. Font: Onest (OFL).
