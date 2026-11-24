#!/usr/bin/env python3
"""Παραγωγή του ενιαίου Word της διπλωματικής από τα Markdown κεφάλαια.

1. pandoc: κείμενο/*.md → προσωρινό .docx
2. python-docx μετεπεξεργασία κατά τον Οδηγό Συγγραφής ΤΜΟΔ και το
   υπόδειγμα του επιβλέποντα:
   - κεφαλίδα σε κάθε σελίδα: «Πανεπιστήμιο Αιγαίου / Τμήμα Μηχανικών
     Οικονομίας & Διοίκησης»· ενιαία αρίθμηση σελίδων κάτω-κέντρο
   - σώμα: Times New Roman 12 pt, διάστιχο 1,5, πλήρης στοίχιση
   - κάθε κεφάλαιο (Επικεφαλίδα 1) σε νέα σελίδα
   - σχήματα κεντραρισμένα με λεζάντα κάτω· πίνακες με τίτλο πάνω
   - πεδία Word για Περιεχόμενα, Κατάλογο Σχημάτων και Κατάλογο Πινάκων
     (ενημερώνονται αυτόματα με το άνοιγμα στο Word: «Ναι» στο μήνυμα
     ενημέρωσης πεδίων, ή Ctrl+A → F9)

Χρήση:  python3 κείμενο/build_docx.py  (από τη ρίζα του repo)
Έξοδος: κείμενο/διπλωματική-σχέδιο-v3.docx
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXTS = ROOT / "κείμενο"
OUT = TEXTS / "διπλωματική-σχέδιο-v3.docx"

CHAPTERS = [
    "00-προκαταρκτικά-περίληψη.md",
    "00b-εισαγωγή-μέθοδος.md",
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
    "11-παραρτήματα.md",
]

HEADER_LINES = ["Πανεπιστήμιο Αιγαίου",
                "Τμήμα Μηχανικών Οικονομίας & Διοίκησης"]

FIELD_MARKERS = {
    "[[TOC]]": r' TOC \o "1-3" \h \z \u ',
    "[[LOF]]": r' TOC \h \z \t "Image Caption,1" ',
    "[[LOT]]": r' TOC \h \z \t "Table Caption,1" ',
}


def run_pandoc(tmp: Path) -> None:
    cmd = ["pandoc", *[str(TEXTS / c) for c in CHAPTERS],
           "--from", "markdown", "--resource-path", str(ROOT), "-o", str(tmp)]
    subprocess.run(cmd, check=True, cwd=ROOT)


def postprocess(tmp: Path) -> None:
    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor

    doc = Document(str(tmp))

    def get_style(name: str):
        """Αναζήτηση στυλ κατά όνομα (παράκαμψη αντιστοίχισης python-docx)."""
        for s in doc.styles:
            if s.name == name:
                return s
        return None

    def ensure_style(name: str):
        st = get_style(name)
        if st is None:
            st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            st.base_style = doc.styles["Normal"]
        return st

    # --- Σώμα κειμένου ------------------------------------------------------
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:cs"), "Times New Roman")
    for nm in ("Normal", "Body Text", "First Paragraph", "Compact"):
        st = get_style(nm)
        if st is None:
            continue
        st.font.name = "Times New Roman"
        st.font.size = Pt(12)
        pf = st.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        if nm != "Compact":
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            pf.space_after = Pt(6)

    # --- Επικεφαλίδες: μαύρες, Times· κάθε κεφάλαιο σε νέα σελίδα ----------
    for name, size in [("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 12),
                       ("Heading 4", 12), ("Title", 18)]:
        st = get_style(name)
        if st is None:
            continue
        st.font.name = "Times New Roman"
        # Αφαίρεση των θεματικών γραμματοσειρών, που υπερισχύουν του font.name
        rf = st.element.get_or_add_rPr().get_or_add_rFonts()
        for att in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            rf.attrib.pop(qn(att), None)
        rf.set(qn("w:cs"), "Times New Roman")
        rf.set(qn("w:eastAsia"), "Times New Roman")
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.italic = name == "Heading 4"
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.space_before = Pt(12)
        st.paragraph_format.space_after = Pt(12)
        if name == "Heading 1":
            st.paragraph_format.page_break_before = True

    # --- Λεζάντες, σχήματα, πίνακες ----------------------------------------
    for nm in ("Image Caption", "Table Caption", "Caption"):
        st = ensure_style(nm)
        st.font.name = "Times New Roman"
        st.font.size = Pt(10)
        st.font.italic = True
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        st.paragraph_format.space_after = Pt(10)
    for nm in ("Captioned Figure", "Figure"):
        st = get_style(nm)
        if st is not None:
            st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            st.paragraph_format.keep_with_next = True

    # Πίνακες: κεντραρισμένοι, γραμματοσειρά 10 pt, απλό διάστιχο
    for tbl in doc.tables:
        tbl.alignment = 1  # center
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                    p.paragraph_format.space_after = Pt(0)
                    for r in p.runs:
                        r.font.size = Pt(10)

    # --- Εξώφυλλο, αφιέρωση, τίτλοι καταλόγων ------------------------------
    specs = {"CoverInstitution": (14, True), "CoverTitle": (16, True),
             "CoverSmall": (12, False), "Dedication": (12, False),
             "TocTitle": (16, True)}
    for name, (size, bold) in specs.items():
        st = ensure_style(name)
        st.font.name = "Times New Roman"
        st.font.size = Pt(size)
        st.font.bold = bold
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        st.paragraph_format.space_after = Pt(14)
    get_style("Dedication").font.italic = True
    get_style("Dedication").paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    get_style("TocTitle").paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # --- Κεφαλίδα & υποσέλιδο ---------------------------------------------
    def add_field(run, instr_text: str, placeholder: str = "") -> None:
        b = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "begin"})
        b.set(qn("w:dirty"), "true")
        i = run._r.makeelement(qn("w:instrText"), {})
        i.set(qn("xml:space"), "preserve")
        i.text = instr_text
        s = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "separate"})
        t = run._r.makeelement(qn("w:t"), {})
        t.text = placeholder
        e = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "end"})
        for el in (b, i, s, t, e):
            run._r.append(el)

    for section in doc.sections:
        hdr = section.header
        hdr.is_linked_to_previous = False
        for p in list(hdr.paragraphs[1:]):
            p._element.getparent().remove(p._element)
        p0 = hdr.paragraphs[0]
        p0.text = ""
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p0.add_run(HEADER_LINES[0])
        r.add_break()
        r2 = p0.add_run(HEADER_LINES[1])
        for rr in (r, r2):
            rr.font.name = "Times New Roman"
            rr.font.size = Pt(10)

        ftr = section.footer
        ftr.is_linked_to_previous = False
        fp = ftr.paragraphs[0]
        fp.text = ""
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = fp.add_run()
        add_field(run, " PAGE ", "1")
        run.font.name = "Times New Roman"
        run.font.size = Pt(10)

    # --- Πεδία Περιεχομένων / Σχημάτων / Πινάκων ----------------------------
    hint = "(Ενημέρωση πεδίου στο Word: δεξί κλικ → Ενημέρωση πεδίου, ή Ctrl+A → F9)"
    for p in doc.paragraphs:
        key = p.text.strip()
        if key in FIELD_MARKERS:
            p.text = ""
            add_field(p.add_run(), FIELD_MARKERS[key], hint)

    # Το Word να προτείνει ενημέρωση όλων των πεδίων κατά το άνοιγμα
    settings = doc.settings.element
    upd = settings.makeelement(qn("w:updateFields"), {qn("w:val"): "true"})
    settings.append(upd)

    doc.save(str(OUT))


def main() -> None:
    tmp = TEXTS / ".tmp_pandoc.docx"
    run_pandoc(tmp)
    postprocess(tmp)
    tmp.unlink(missing_ok=True)
    print(f"OK → {OUT}")


if __name__ == "__main__":
    sys.exit(main())
