#!/usr/bin/env python3
"""Παραγωγή του ενιαίου Word της διπλωματικής από τα Markdown κεφάλαια.

1. pandoc: κείμενο/*.md → προσωρινό .docx
2. python-docx μετεπεξεργασία κατά το πρότυπο του Πανεπιστημίου:
   - κεφαλίδα σε κάθε σελίδα: «Πανεπιστήμιο Αιγαίου / Τμήμα Μηχανικών
     Οικονομίας & Διοίκησης» (όπως το υπόδειγμα του επιβλέποντα)
   - υποσέλιδο με αρίθμηση σελίδων (πεδίο PAGE)
   - σώμα: Times New Roman 12 pt, διάστιχο 1,5, πλήρης στοίχιση
   - στυλ εξωφύλλου (CoverTitle/CoverInstitution/CoverSmall/Dedication)
   - αντικατάσταση του δείκτη [[TOC]] με πραγματικό πεδίο πίνακα
     περιεχομένων Word (δεξί κλικ → Update Field για ενημέρωση)

Χρήση:  python3 κείμενο/build_docx.py  (από τη ρίζα του repo)
Έξοδος: κείμενο/διπλωματική-σχέδιο-v2.docx
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXTS = ROOT / "κείμενο"
OUT = TEXTS / "διπλωματική-σχέδιο-v2.docx"

CHAPTERS = [
    "00-προκαταρκτικά-περίληψη.md",
    "01-μετάδοση-θερμότητας.md",
    "02-αντλίες-θερμότητας.md",
    "03-ηλιακή-φωτοβολταϊκά.md",
    "04-κολυμβητήρια-κλίμα.md",
    "05-νομοθεσία.md",
    "06-ποσειδώνιο-δεδομένα.md",
    "07-μοντέλο-βαθμονόμηση.md",
    "08-μελέτη-περίπτωσης.md",
    "09-οικονομική-συμπεράσματα.md",
    "10-βιβλιογραφία.md",
]

HEADER_LINES = ["Πανεπιστήμιο Αιγαίου",
                "Τμήμα Μηχανικών Οικονομίας & Διοίκησης"]


def run_pandoc(tmp: Path) -> None:
    cmd = ["pandoc", *[str(TEXTS / c) for c in CHAPTERS],
           "--from", "markdown", "-o", str(tmp)]
    subprocess.run(cmd, check=True, cwd=ROOT)


def postprocess(tmp: Path) -> None:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.oxml.ns import qn
    from docx.shared import Pt

    doc = Document(str(tmp))

    # --- Βασικά στυλ σώματος ------------------------------------------------
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.element.rPr.rFonts.set(qn("w:cs"), "Times New Roman")
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.space_after = Pt(6)

    # Το pandoc βάζει τις παραγράφους σώματος σε "Body Text"/"First Paragraph"
    def get_style_early(name):
        for s in doc.styles:
            if s.name == name:
                return s
        return None
    for nm in ("Body Text", "First Paragraph"):
        st = get_style_early(nm)
        if st is not None:
            st.font.name = "Times New Roman"
            st.font.size = Pt(12)
            st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def get_style(name: str):
        """Αναζήτηση στυλ κατά όνομα (παράκαμψη BabelFish του python-docx)."""
        for s in doc.styles:
            if s.name == name:
                return s
        return None

    from docx.shared import RGBColor
    for name, size, bold in [("Heading 1", 16, True), ("Heading 2", 14, True),
                             ("Heading 3", 12, True), ("Title", 18, True)]:
        st = get_style(name)
        if st is None:
            continue
        st.font.name = "Times New Roman"
        st.font.size = Pt(size)
        st.font.bold = bold
        st.font.color.rgb = RGBColor(0, 0, 0)

    # --- Στυλ εξωφύλλου (δημιουργούνται αν δεν υπάρχουν) --------------------
    from docx.enum.style import WD_STYLE_TYPE
    cover_specs = {"CoverInstitution": (14, True), "CoverTitle": (16, True),
                   "CoverSmall": (12, False), "Dedication": (12, False)}
    for name, (size, bold) in cover_specs.items():
        try:
            st = doc.styles[name]
        except KeyError:
            st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            st.base_style = doc.styles["Normal"]
        st.font.name = "Times New Roman"
        st.font.size = Pt(size)
        st.font.bold = bold
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        st.paragraph_format.space_after = Pt(14)
    doc.styles["Dedication"].font.italic = True
    doc.styles["Dedication"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # --- Κεφαλίδα & υποσέλιδο σε όλες τις ενότητες --------------------------
    for section in doc.sections:
        hdr = section.header
        hdr.is_linked_to_previous = False
        for p in list(hdr.paragraphs[1:]):
            p._element.getparent().remove(p._element)
        p0 = hdr.paragraphs[0]
        p0.text = ""
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p0.add_run(HEADER_LINES[0] + "\n" + HEADER_LINES[1])
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)

        ftr = section.footer
        ftr.is_linked_to_previous = False
        fp = ftr.paragraphs[0]
        fp.text = ""
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = fp.add_run()
        fld_begin = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "begin"})
        instr = run._r.makeelement(qn("w:instrText"), {})
        instr.text = "PAGE"
        fld_end = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "end"})
        run._r.append(fld_begin)
        run._r.append(instr)
        run._r.append(fld_end)
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)

    # --- Αντικατάσταση [[TOC]] με πεδίο πίνακα περιεχομένων -----------------
    for p in doc.paragraphs:
        if p.text.strip() == "[[TOC]]":
            p.text = ""
            run = p.add_run()
            b = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "begin"})
            b.set(qn("w:dirty"), "true")
            i = run._r.makeelement(qn("w:instrText"), {})
            i.set(qn("xml:space"), "preserve")
            i.text = r' TOC \o "1-2" \h \z \u '
            s = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "separate"})
            t = run._r.makeelement(qn("w:t"), {})
            t.text = "(Δεξί κλικ → Ενημέρωση πεδίου για τον πίνακα περιεχομένων)"
            e = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "end"})
            for el in (b, i, s, t, e):
                run._r.append(el)
            break

    doc.save(str(OUT))


def main() -> None:
    tmp = TEXTS / ".tmp_pandoc.docx"
    run_pandoc(tmp)
    postprocess(tmp)
    tmp.unlink(missing_ok=True)
    print(f"OK → {OUT}")


if __name__ == "__main__":
    sys.exit(main())
