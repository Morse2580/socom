---
name: xml-comments-no-double-hyphen
description: generating XML (templates/f-strings) — the '--' in comments trap that makes index silently skip files
metadata:
  type: reference
---

**XML comments cannot contain `--` (double hyphen).** It is not just the `-->`
terminator — any `--` inside a `<!-- ... -->` block makes the document
not-well-formed (`ParseError: not well-formed (invalid token)`).

This bites when generating XML artifacts from f-string/templates whose comments
mention CLI flags: a lesson template comment read `socom lesson retire <id>
--reason ...`, and the `--reason` silently broke every generated `<lesson>`.

**Why it's nasty in SOCOM:** `socom index` (`bin/socom`, `rglob .socom/**.xml`)
catches `ET.ParseError` and **skips** the file with only a stderr line — so a
malformed artifact doesn't crash anything, it just **never reaches retrieval**.
The symptom is "my new artifact won't show up in `socom query`," not an error.

**How to apply:** never put `--` in an XML comment (reword flag examples:
`retire it with a reason` not `--reason`; `re-confirmed` not `-- confirmed`).
When a generated `.xml` artifact mysteriously isn't indexed, first run
`python3 -c "import xml.etree.ElementTree as ET; ET.parse('<file>')"` — a skip
in `socom index` stderr or a ParseError is the tell. Related: [[canon-hash-reads-dot-socom]].
