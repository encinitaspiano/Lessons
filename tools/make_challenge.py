#!/usr/bin/env python3
"""Build a 3-level Lesson Challenge page (approved Oct 4, 2026 layout).

Usage:  python3 tools/make_challenge.py content.json [more.json ...]
Writes: <slug>-<YYYY-MM-DD>.html in the repo root (served by GitHub Pages).

content.json schema (ASCII only):
{
  "student": "Ziggy",                      # first name as shown to the student
  "slug": "ziggy",                         # lowercase, letters/hyphens only
  "date": "2026-10-01",
  "date_label": "Thursday, October 1, 2026",
  "terms": [                               # "Terms to Know" box, shown first
    {"name": "Staccato", "lang": "Italian", "meaning": "Means \\"detached\\". ...",
     "sym": "",                             # optional: "sharp" | "flat" | "natural" | ""
     "colorshape": ""}                      # optional color-shape note
  ],
  "sections": [                            # detailed lesson summary, in lesson order
    {"heading": "...", "paragraphs": ["..."], "bullets": ["..."], "note": "optional highlighted box"}
  ],
  "practice": ["..."],                     # This week's practice
  "questions": [                           # Level 2, 10-15 questions, 4 options each
    {"q": "...", "o": ["correct", "wrong", "wrong", "wrong"], "a": 0, "e": "why"}
  ],
  "written": ["...", "..."],               # Level 3, 4-6 explain-in-your-own-words prompts
  "wordbank": "sharp, flat, tie, ..."       # music words for Level 3
}
Options are shuffled in the browser, so listing the correct one first is fine.
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "tools" / "template.html").read_text()
SYMS = {"sharp": "&#9839;", "flat": "&#9837;", "natural": "&#9675;"}
e = html.escape


def level1(c):
    out = ['<div class="terms">', '    <h3>Terms to Know</h3>',
           '    <p class="hint">Start here. These are the music words from this lesson. '
           'Some come from Italian, the language of music, so you will see them in music from all over the world.</p>']
    for t in c["terms"]:
        sym = SYMS.get(t.get("sym", ""), "")
        line = '    <div class="term">'
        if sym:
            line += f'<span class="sym">{sym}</span>'
        line += f'<span class="tname">{e(t["name"])}</span><span class="lang">{e(t["lang"])}</span>'
        line += f'\n      <div>{e(t["meaning"])}</div>'
        if t.get("colorshape"):
            line += f'\n      <span class="cs"><b>Color-shape:</b> {e(t["colorshape"])}</span>'
        out.append(line + '</div>')
    out.append('  </div>')
    for s in c["sections"]:
        out.append(f'\n  <h3>{e(s["heading"])}</h3>')
        for p in s.get("paragraphs", []):
            out.append(f'  <p>{e(p)}</p>')
        if s.get("bullets"):
            out.append('  <ul>' + ''.join(f'\n    <li>{e(b)}</li>' for b in s["bullets"]) + '\n  </ul>')
        if s.get("note"):
            out.append(f'  <div class="note">{e(s["note"])}</div>')
    out.append("\n  <h3>This week's practice</h3>\n  <ul>" +
               ''.join(f'\n    <li>{e(p)}</li>' for p in c["practice"]) + '\n  </ul>')
    out.append('  <p class="signoff">Keep an open mind and an open heart, and always create with much love.</p>')
    return "\n".join(out)


def build(path):
    c = json.loads(pathlib.Path(path).read_text())
    assert re.fullmatch(r"[a-z-]+", c["slug"]), "slug must be lowercase letters/hyphens"
    assert 10 <= len(c["questions"]) <= 15, "Level 2 needs 10-15 questions"
    for q in c["questions"]:
        assert len(q["o"]) == 4 and 0 <= q["a"] < 4 and len(set(q["o"])) == 4, q["q"]
    assert 4 <= len(c["written"]) <= 6, "Level 3 needs 4-6 prompts"
    name = c["student"]
    page = (TEMPLATE
            .replace("__TITLE__", e(f"{name} - Lesson Challenge - {c['date']}"))
            .replace("__H1__", e(f"{name}'s Lesson Challenge"))
            .replace("__DATE_LABEL__", e(c["date_label"]))
            .replace("__LEVEL1__", level1(c))
            .replace("__WORDBANK__", e(c["wordbank"]))
            .replace("__STUDENT_JS__", json.dumps(name))
            .replace("__DATE_JS__", json.dumps(c["date"]))
            .replace("__DATE_LABEL_JS__", json.dumps(c["date_label"]))
            .replace("__QUESTIONS__", json.dumps(c["questions"], indent=1, ensure_ascii=True))
            .replace("__WRITTEN__", json.dumps(c["written"], indent=1, ensure_ascii=True)))
    left = re.findall(r"__[A-Z0-9_]+__", page)
    assert not left, f"unfilled placeholders: {left}"
    page.encode("ascii")  # raises if any non-ASCII slipped in
    out = ROOT / f"{c['slug']}-{c['date']}.html"
    out.write_text(page, encoding="ascii")
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(build(p))
