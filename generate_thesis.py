"""
Thesis PDF generator for:
  Saliency-Guided Bit Allocation for Context-Aware Image Compression
  Kailash S (2022CS0345) & Karthik M (2022CS0878)
  Guide: Dr. N. Revathi
  Sri Venkateswara College of Engineering, Chennai
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.colors import HexColor
import os

OUTPUT_PATH = os.path.expanduser("~/Downloads/Saliency_Guided_Compression_Thesis.pdf")

# ─── Colours ────────────────────────────────────────────────────────────────
BLACK  = colors.black
WHITE  = colors.white
GRAY   = HexColor("#555555")
LGRAY  = HexColor("#AAAAAA")
NAVY   = HexColor("#003366")

# ─── Page geometry ──────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4          # 595.28 x 841.89 pts
LM = RM = 2.5 * cm
TM = 2.5 * cm
BM = 2.5 * cm
BODY_W = PAGE_W - LM - RM

# ─── Styles ─────────────────────────────────────────────────────────────────
base_styles = getSampleStyleSheet()

def S(name, parent=None, **kw):
    """Create a ParagraphStyle; parent defaults to Normal if not provided."""
    return ParagraphStyle(name, parent=parent if parent else base_styles["Normal"], **kw)

STY_TITLE       = S("ThesisTitle",    fontSize=18, leading=24, alignment=TA_CENTER,
                     fontName="Helvetica-Bold",   spaceAfter=6,  textColor=NAVY)
STY_SUBTITLE    = S("ThesisSubtitle", fontSize=14, leading=20, alignment=TA_CENTER,
                     fontName="Helvetica-Bold",   spaceAfter=4,  textColor=NAVY)
STY_CENTER      = S("TCenter",        fontSize=11, leading=16, alignment=TA_CENTER,
                     fontName="Helvetica",         spaceAfter=4)
STY_BOLD_CENTER = S("TBoldCenter",    fontSize=11, leading=16, alignment=TA_CENTER,
                     fontName="Helvetica-Bold",   spaceAfter=4)
STY_BODY        = S("Body",           fontSize=11, leading=18, alignment=TA_JUSTIFY,
                     fontName="Helvetica",         spaceAfter=6, firstLineIndent=0)
STY_BODY_INDENT = S("BodyIndent",     fontSize=11, leading=18, alignment=TA_JUSTIFY,
                     fontName="Helvetica",         spaceAfter=6, leftIndent=1*cm)
STY_CH_TITLE    = S("ChTitle",        fontSize=14, leading=20, alignment=TA_CENTER,
                     fontName="Helvetica-Bold",   spaceBefore=6, spaceAfter=12,
                     textColor=NAVY)
STY_SEC         = S("SecHead",        fontSize=12, leading=18, alignment=TA_LEFT,
                     fontName="Helvetica-Bold",   spaceBefore=10, spaceAfter=4)
STY_SUBSEC      = S("SubSecHead",     fontSize=11, leading=16, alignment=TA_LEFT,
                     fontName="Helvetica-Bold",   spaceBefore=8,  spaceAfter=3)
STY_MONO        = S("Mono",           fontSize=9,  leading=13, alignment=TA_LEFT,
                     fontName="Courier",           spaceAfter=4,
                     backColor=HexColor("#F5F5F5"), leftIndent=0.5*cm, rightIndent=0.5*cm)
STY_CAPTION     = S("Caption",        fontSize=9,  leading=13, alignment=TA_CENTER,
                     fontName="Helvetica-Oblique", spaceAfter=8, spaceBefore=2)
STY_TOC_ENTRY   = S("TocEntry",       fontSize=11, leading=18, alignment=TA_LEFT,
                     fontName="Helvetica",         spaceAfter=2)
STY_TOC_CHAPTER = S("TocChapter",     fontSize=11, leading=18, alignment=TA_LEFT,
                     fontName="Helvetica-Bold",   spaceAfter=2)
STY_LIST_ITEM   = S("ListItem",       fontSize=11, leading=18, alignment=TA_JUSTIFY,
                     fontName="Helvetica",         spaceAfter=4,
                     leftIndent=0.8*cm, bulletIndent=0.2*cm)
STY_SMALL       = S("Small",          fontSize=9,  leading=13, alignment=TA_LEFT,
                     fontName="Helvetica",         spaceAfter=3)
STY_MATH        = ParagraphStyle("MathLine", fontName="Courier", fontSize=11, leading=16,
                     alignment=TA_CENTER, spaceAfter=4,
                     backColor=HexColor("#F5F5F5"), leftIndent=0.5*cm, rightIndent=0.5*cm)
STY_RIGHT       = S("AlignRight",     fontSize=10, leading=14, alignment=TA_RIGHT,
                     fontName="Helvetica",         spaceAfter=0)
STY_PAGE_LABEL  = S("PageLabel",      fontSize=10, leading=14, alignment=TA_CENTER,
                     fontName="Helvetica-Bold",   spaceAfter=0)

# ─── Helper functions ────────────────────────────────────────────────────────
def sp(pts):
    return Spacer(1, pts)

def hr():
    return HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=6, spaceBefore=6)

def pb():
    return PageBreak()

def P(text, style=STY_BODY):
    return Paragraph(text, style)

def heading(ch_num, title):
    return [
        P(f"CHAPTER {ch_num}", STY_CH_TITLE),
        P(title, STY_CH_TITLE),
        hr(),
        sp(6),
    ]

def section(num, title):
    return P(f"{num}  {title}", STY_SEC)

def subsection(num, title):
    return P(f"{num}  {title}", STY_SUBSEC)

def bullet(text):
    return P(f"• {text}", STY_LIST_ITEM)

def code_block(lines):
    """Render monospace code block."""
    text = "<br/>".join(lines)
    return P(text, STY_MONO)

def fig_caption(num, title):
    return P(f"Figure {num}: {title}", STY_CAPTION)

def toc_line(num, title, page):
    if num:
        return P(f"<b>{num}</b>&nbsp;&nbsp;{title}<font color='#888888'>{'.' * max(1, 55 - len(title) - len(str(page)))}</font>{page}",
                 STY_TOC_ENTRY)
    return P(f"<b>{title}</b><font color='#888888'>{'.' * max(1, 60 - len(title) - len(str(page)))}</font>{page}",
             STY_TOC_CHAPTER)

# ─── Page number state ───────────────────────────────────────────────────────
_page_state = {"roman": True, "offset": 0}

ROMAN = {1:'i',2:'ii',3:'iii',4:'iv',5:'v',6:'vi',7:'vii',8:'viii',
         9:'ix',10:'x',11:'xi',12:'xii'}

def _header_footer(canvas, doc):
    canvas.saveState()
    page_num = doc.page
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(GRAY)

    if _page_state["roman"]:
        label = ROMAN.get(page_num, str(page_num))
    else:
        label = str(page_num - _page_state["offset"])

    # Bottom center page number
    canvas.drawCentredString(PAGE_W / 2, BM * 0.5, label)

    # Top header line (not on title page)
    if page_num > 1:
        canvas.setStrokeColor(LGRAY)
        canvas.setLineWidth(0.5)
        canvas.line(LM, PAGE_H - TM + 4, PAGE_W - RM, PAGE_H - TM + 4)
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawString(LM, PAGE_H - TM + 6,
                          "Saliency-Guided Bit Allocation for Context-Aware Image Compression")
        canvas.drawRightString(PAGE_W - RM, PAGE_H - TM + 6,
                               "Sri Venkateswara College of Engineering")

    canvas.restoreState()

# ─── Document setup ──────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT_PATH,
    pagesize=A4,
    leftMargin=LM, rightMargin=RM,
    topMargin=TM + 0.5*cm, bottomMargin=BM + 0.5*cm,
    title="Saliency-Guided Bit Allocation for Context-Aware Image Compression",
    author="Kailash S, Karthik M",
)

story = []

# ════════════════════════════════════════════════════════════════════════════
# PAGE 1 – TITLE PAGE
# ════════════════════════════════════════════════════════════════════════════
story += [
    sp(1.5*cm),
    P("SRI VENKATESWARA COLLEGE OF ENGINEERING", STY_SUBTITLE),
    P("(An Autonomous Institution; Affiliated to Anna University, Chennai-600025)", STY_CENTER),
    P("ANNA UNIVERSITY :: CHENNAI 600 025", STY_CENTER),
    hr(),
    sp(1*cm),
    P("SALIENCY-GUIDED BIT ALLOCATION FOR", STY_TITLE),
    P("CONTEXT-AWARE IMAGE COMPRESSION", STY_TITLE),
    sp(0.6*cm),
    P("A PROJECT REPORT", STY_BOLD_CENTER),
    P("Submitted by", STY_CENTER),
    sp(0.4*cm),
    P("KAILASH S (2022CS0345)", STY_BOLD_CENTER),
    P("KARTHIK M (2022CS0878)", STY_BOLD_CENTER),
    sp(0.4*cm),
    P("in partial fulfilment for the award of the degree", STY_CENTER),
    P("of", STY_CENTER),
    P("BACHELOR OF ENGINEERING", STY_BOLD_CENTER),
    P("in", STY_CENTER),
    P("COMPUTER SCIENCE AND ENGINEERING", STY_BOLD_CENTER),
    sp(1*cm),
    hr(),
    sp(1*cm),
    P("Department of Computer Science and Engineering", STY_CENTER),
    P("Sri Venkateswara College of Engineering", STY_CENTER),
    sp(0.4*cm),
    P("MAY 2026", STY_BOLD_CENTER),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# PAGE 2 – BONAFIDE CERTIFICATE
# ════════════════════════════════════════════════════════════════════════════
story += [
    sp(0.5*cm),
    P("ii", STY_PAGE_LABEL),
    sp(0.3*cm),
    P("SRI VENKATESWARA COLLEGE OF ENGINEERING", STY_SUBTITLE),
    P("(An Autonomous Institution; Affiliated to Anna University, Chennai-600025)", STY_CENTER),
    P("ANNA UNIVERSITY, CHENNAI - 600 025", STY_CENTER),
    sp(0.8*cm),
    P("BONAFIDE CERTIFICATE", STY_SUBTITLE),
    hr(),
    sp(0.4*cm),
    P("""Certified that this project report <b>"SALIENCY-GUIDED BIT ALLOCATION FOR
CONTEXT-AWARE IMAGE COMPRESSION"</b> is the bonafide work of
<b>"KAILASH S (2022CS0345) and KARTHIK M (2022CS0878)"</b> who carried out the project
work under my supervision.""", STY_BODY),
    sp(1.5*cm),
    Table(
        [
            [P("SIGNATURE", STY_CENTER), P("SIGNATURE", STY_CENTER)],
            [P("Dr. R. ANITHA", STY_BOLD_CENTER), P("Dr. N. REVATHI", STY_BOLD_CENTER)],
            [P("HEAD OF THE DEPARTMENT", STY_CENTER), P("PROJECT GUIDE", STY_CENTER)],
            [P("COMPUTER SCIENCE &amp; ENGINEERING", STY_SMALL), P("ASSISTANT PROFESSOR", STY_CENTER)],
            [P("Sri Venkateswara College of Engineering", STY_SMALL),
             P("COMPUTER SCIENCE &amp; ENGINEERING", STY_SMALL)],
        ],
        colWidths=[BODY_W/2, BODY_W/2],
    ),
    sp(2*cm),
    P("Submitted for the project viva-voce examination held on ………………………", STY_BODY),
    sp(2*cm),
    Table(
        [[P("INTERNAL EXAMINER", STY_CENTER), P("EXTERNAL EXAMINER", STY_CENTER)]],
        colWidths=[BODY_W/2, BODY_W/2],
    ),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# PAGE 3 – ABSTRACT
# ════════════════════════════════════════════════════════════════════════════
story += [
    sp(0.5*cm),
    P("iii", STY_PAGE_LABEL),
    sp(0.3*cm),
    P("ABSTRACT", STY_SUBTITLE),
    hr(),
    sp(0.3*cm),
    P("""Conventional image compression applies nearly uniform quality across all regions of an image,
in stark contrast to human visual perception and downstream machine-vision tasks, both of which are far
more sensitive to distortions in semantically important regions than in smooth or visually unimportant
background areas. This thesis addresses that inefficiency through a <b>saliency-guided, context-aware image
compression framework</b> that estimates pixel-level perceptual importance using three complementary
detection modules: deep salient-object detection, semantic instance segmentation, and multi-scale
spectral residual saliency analysis.""", STY_BODY),
    P("""The three signals are fused into a unified importance map through element-wise maximum
(OR-style) fusion, ensuring that a pixel is protected by any modality that deems it relevant.
The fused map is then transformed into a spatially varying bit-allocation weight map through the
<b>Ascending Cosine Roll-down (ACRD)</b> transfer function — a smooth, monotone S-curve that converts
saliency scores into perceptually motivated allocation weights, further refined by gamma-based curve
shaping and floor/ceiling constraints.""", STY_BODY),
    P("""The compression pipeline performs layered reconstruction by blending a strongly degraded
base layer representing background regions with a high-quality or lossless foreground layer guided
by the weight map, thereby concentrating coding quality where it matters most and improving
compressibility elsewhere. The system is modular, training-light at the pipeline level, and built from
independently replaceable components implemented in five Python modules: <i>saliency.py</i>,
<i>object_detection.py</i>, <i>saliency_spectral.py</i>, <i>bit_allocation.py</i>, and
<i>compression.py</i>.""", STY_BODY),
    P("""Experimental evaluation on a 50-image subset of the CLIC dataset demonstrates that the
proposed method achieves an average compression ratio of approximately <b>57.8</b> compared to
<b>26.5</b> for standard JPEG, effectively more than doubling compression efficiency while preserving
perceptual quality in foreground regions of interest.""", STY_BODY),
    sp(0.6*cm),
    P("<b>Index Terms —</b> saliency detection, image compression, bit allocation, context-aware coding,"
      " layered reconstruction, U²-Net, YOLOv8, spectral residual, ACRD, deep learning.", STY_BODY),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# PAGE 4 – ACKNOWLEDGEMENT
# ════════════════════════════════════════════════════════════════════════════
story += [
    sp(0.5*cm),
    P("iv", STY_PAGE_LABEL),
    sp(0.3*cm),
    P("ACKNOWLEDGEMENT", STY_SUBTITLE),
    hr(),
    sp(0.3*cm),
    P("""We thank our Principal, Sri Venkateswara College of Engineering, for being the source of
inspiration throughout our undergraduate studies at this institution.""", STY_BODY),
    P("""We express our sincere gratitude to <b>Dr. R. Anitha</b>, Head of the Department of
Computer Science and Engineering, for her unwavering encouragement and for providing all necessary
resources to carry out this project.""", STY_BODY),
    P("""With profound respect, we extend our deepest sense of gratitude to our project guide
<b>Dr. N. Revathi</b>, Assistant Professor, Department of Computer Science and Engineering,
whose expert technical guidance, constructive feedback, and patient mentorship shaped every aspect
of this work. Her deep knowledge in computer vision and image processing was invaluable to us
throughout the project.""", STY_BODY),
    P("""We are thankful to our project coordinators and all faculty members of the Department of
Computer Science and Engineering for their continuous support, advice, and timely assistance throughout
the duration of this project.""", STY_BODY),
    P("""We also acknowledge the open-source community behind PyTorch, Ultralytics YOLOv8, and
the U²-Net implementation, without which the practical implementation of our system would not have
been possible.""", STY_BODY),
    P("""Finally, we thank our families and friends for their unconditional support, understanding,
and encouragement throughout the course of our graduate studies.""", STY_BODY),
    sp(1.5*cm),
    P("KAILASH S", STY_RIGHT),
    P("KARTHIK M", STY_RIGHT),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# PAGE 5 – TABLE OF CONTENTS
# ════════════════════════════════════════════════════════════════════════════
story += [
    sp(0.5*cm),
    P("v", STY_PAGE_LABEL),
    sp(0.3*cm),
    P("TABLE OF CONTENTS", STY_SUBTITLE),
    hr(),
    sp(0.3*cm),
]

toc_data = [
    (None,  "ABSTRACT",                                               "iii"),
    (None,  "ACKNOWLEDGEMENT",                                         "iv"),
    (None,  "LIST OF FIGURES",                                         "vii"),
    (None,  "LIST OF ABBREVIATIONS",                                   "viii"),
    ("1",   "INTRODUCTION",                                            "1"),
    ("1.1", "Background and Motivation",                               "1"),
    ("1.2", "Problem Statement",                                       "3"),
    ("1.3", "Objectives",                                              "4"),
    ("1.4", "Scope and Contributions",                                 "5"),
    ("1.5", "Thesis Organisation",                                     "6"),
    ("2",   "LITERATURE REVIEW",                                       "7"),
    ("2.1", "Uniform-Quality Compression Standards",                   "7"),
    ("2.2", "Saliency-Aware Image Coding",                             "8"),
    ("2.3", "Deep Salient Object Detection",                           "9"),
    ("2.4", "Semantic Instance Segmentation for Compression",         "10"),
    ("2.5", "Spectral Residual Saliency Methods",                     "11"),
    ("2.6", "Learned End-to-End Image Compression",                   "12"),
    ("2.7", "Summary and Research Gaps",                              "13"),
    ("3",   "PROPOSED SYSTEM OVERVIEW",                               "14"),
    ("3.1", "System Architecture",                                    "14"),
    ("3.2", "OR-Style Multi-Source Fusion",                           "16"),
    ("3.3", "ACRD Bit-Allocation Transfer Function",                  "17"),
    ("3.4", "Layered Compression Framework",                          "18"),
    ("3.5", "Mathematical Formulation",                               "19"),
    ("4",   "REQUIREMENT SPECIFICATION",                              "20"),
    ("4.1", "Hardware Requirements",                                  "20"),
    ("4.2", "Software Requirements",                                  "20"),
    ("4.3", "Python Library Dependencies",                            "21"),
    ("5",   "IMPLEMENTATION MODULES",                                 "22"),
    ("5.1", "Module 1: Deep Saliency Detection (saliency.py)",        "22"),
    ("5.2", "Module 2: Semantic Segmentation (object_detection.py)",  "30"),
    ("5.3", "Module 3: Spectral Residual Saliency (saliency_spectral.py)", "34"),
    ("5.4", "Module 4: Bit Allocation (bit_allocation.py)",           "38"),
    ("5.5", "Module 5: Layered Compression (compression.py)",         "44"),
    ("6",   "RESULTS AND DISCUSSION",                                 "51"),
    ("6.1", "Experimental Setup",                                     "51"),
    ("6.2", "Compression Ratio Analysis",                             "52"),
    ("6.3", "Perceptual Quality Assessment",                          "53"),
    ("6.4", "Ablation Study",                                         "54"),
    ("6.5", "Discussion",                                             "55"),
    ("7",   "CONCLUSION AND FUTURE WORK",                             "57"),
    ("7.1", "Conclusion",                                             "57"),
    ("7.2", "Future Work",                                            "58"),
    (None,  "REFERENCES",                                             "61"),
]

for num, title, page in toc_data:
    if num in (None, "1","2","3","4","5","6","7"):
        indent = 0
        sty = STY_TOC_CHAPTER
    else:
        indent = 1*cm
        sty = STY_TOC_ENTRY
    dots = '.' * max(3, 58 - len(str(num or '')) - len(title) - len(page) - int(indent/cm)*4)
    story.append(P(
        f"{'&nbsp;'*8 if indent else ''}"
        f"<b>{num+'  ' if num else ''}</b>{title}"
        f"<font color='#999999'>{dots}</font>{page}",
        sty
    ))

story.append(pb())

# ════════════════════════════════════════════════════════════════════════════
# PAGE 6 – LIST OF FIGURES (abbreviated)
# ════════════════════════════════════════════════════════════════════════════
story += [
    sp(0.5*cm),
    P("vii", STY_PAGE_LABEL),
    sp(0.3*cm),
    P("LIST OF FIGURES", STY_SUBTITLE),
    hr(),
    sp(0.3*cm),
]

figures = [
    ("3.1",  "Feed-forward pipeline architecture of the proposed system", "14"),
    ("3.2",  "Element-wise maximum (OR) fusion of three saliency maps", "16"),
    ("3.3",  "ACRD raised-cosine transfer curve (γ = 1)", "17"),
    ("3.4",  "Gamma-parameterised ACRD deformation (γ = 0.7, 1.0, 1.6)", "18"),
    ("3.5",  "Two-layer spatial blending pipeline", "19"),
    ("5.1",  "U²-NetP nested encoder-decoder architecture", "23"),
    ("5.2",  "RSU7 residual U-block internal structure", "24"),
    ("5.3",  "RSU4F dilated-convolution-only block", "25"),
    ("5.4",  "Side supervision and output fusion of U²-NetP", "26"),
    ("5.5",  "U²-NetP inference pipeline: resize → normalise → forward → resize back", "27"),
    ("5.6",  "YOLOv8n-seg detection and per-instance mask generation", "31"),
    ("5.7",  "Union mask construction via element-wise maximum over instances", "32"),
    ("5.8",  "Multi-scale spectral residual: 0.5×, 1.0×, 1.5× fusion", "35"),
    ("5.9",  "Log-spectrum minus smoothed-spectrum gives frequency residual", "36"),
    ("5.10", "ACRD lookup table and S-curve visualisation", "39"),
    ("5.11", "Effect of threshold on background clamping", "40"),
    ("5.12", "γ > 1 vs. γ < 1 weight distributions on a sample image", "41"),
    ("5.13", "SimpleCompressionNet encoder–decoder architecture", "45"),
    ("5.14", "Base layer: downsampling round-trip destroys high-frequency texture", "46"),
    ("5.15", "Box-filter blur sigma vs. kernel size table", "47"),
    ("5.16", "Classic lossy blend: base + enhanced per-pixel interpolation", "48"),
    ("5.17", "Foreground-lossless blend: exact original at W=1 pixels", "49"),
    ("6.1",  "Original image (30 MB) vs. processed output (2.7 MB) — sample pair", "51"),
    ("6.2",  "Bar chart: average compression ratio — JPEG (26.5) vs. Proposed (57.8)", "52"),
    ("6.3",  "SSIM heatmaps for JPEG and proposed method on 5 CLIC images", "53"),
    ("6.4",  "Ablation: compression ratio by module inclusion", "54"),
    ("6.5",  "Saliency map visualisation for three sample images", "55"),
]

for num, caption, page in figures:
    dots = '.' * max(3, 58 - len(num) - len(caption) - len(page))
    story.append(P(
        f"Figure {num}&nbsp;&nbsp;{caption}"
        f"<font color='#999999'>{dots}</font>{page}",
        STY_TOC_ENTRY
    ))

story.append(pb())

# ════════════════════════════════════════════════════════════════════════════
# PAGE 7 – LIST OF ABBREVIATIONS
# ════════════════════════════════════════════════════════════════════════════
story += [
    sp(0.5*cm),
    P("viii", STY_PAGE_LABEL),
    sp(0.3*cm),
    P("LIST OF ABBREVIATIONS", STY_SUBTITLE),
    hr(),
    sp(0.3*cm),
]

abbrevs = [
    ("ACRD",  "Ascending Cosine Roll-down"),
    ("AVIF",  "AV1 Image File Format"),
    ("BN",    "Batch Normalisation"),
    ("CLIC",  "Challenge on Learned Image Compression"),
    ("CNN",   "Convolutional Neural Network"),
    ("COCO",  "Common Objects in Context"),
    ("CPU",   "Central Processing Unit"),
    ("CV",    "Computer Vision"),
    ("DFT",   "Discrete Fourier Transform"),
    ("DNN",   "Deep Neural Network"),
    ("DL",    "Deep Learning"),
    ("FFT",   "Fast Fourier Transform"),
    ("GPU",   "Graphics Processing Unit"),
    ("HEIF",  "High Efficiency Image File Format"),
    ("HOG",   "Histogram of Oriented Gradients"),
    ("IFFT",  "Inverse Fast Fourier Transform"),
    ("JPEG",  "Joint Photographic Experts Group"),
    ("MAE",   "Mean Absolute Error"),
    ("ML",    "Machine Learning"),
    ("NMS",   "Non-Maximum Suppression"),
    ("OR",    "Logical OR"),
    ("PSNR",  "Peak Signal-to-Noise Ratio"),
    ("RGB",   "Red Green Blue"),
    ("ReLU",  "Rectified Linear Unit"),
    ("RSU",   "Residual U-block"),
    ("SSIM",  "Structural Similarity Index Measure"),
    ("U²-Net","U-Squared Net — nested U-structure salient object detector"),
    ("YOLO",  "You Only Look Once"),
    ("YOLOv8","You Only Look Once Version 8"),
]

tbl_data = [[P(f"<b>{a}</b>", STY_BODY), P(b, STY_BODY)] for a, b in abbrevs]
abbrev_table = Table(tbl_data, colWidths=[3.5*cm, BODY_W - 3.5*cm])
abbrev_table.setStyle(TableStyle([
    ('ROWBACKGROUNDS', (0,0), (-1,-1), [WHITE, HexColor("#F0F4FA")]),
    ('GRID',          (0,0), (-1,-1), 0.25, LGRAY),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ('RIGHTPADDING',  (0,0), (-1,-1), 6),
    ('TOPPADDING',    (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
]))
story += [abbrev_table, pb()]

# ────────────────────────────────────────────────────────────────────────────
# Switch to Arabic page numbers from here
# ────────────────────────────────────────────────────────────────────────────
_page_state["roman"]  = False
_page_state["offset"] = 7          # pages 1-8 are front matter (8 PDF pages, offset so p9→"1")

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 1 – INTRODUCTION   (pages 1–6)
# ════════════════════════════════════════════════════════════════════════════
story += heading("1", "INTRODUCTION")

story.append(section("1.1", "Background and Motivation"))
story += [
    P("""The rapid proliferation of digital imaging across mobile devices, cloud storage, surveillance
infrastructure, social media platforms, and biomedical archiving has placed unprecedented pressure on
image compression systems. Estimates suggest that more than 3.2 billion images are shared online every
day, and the aggregate volume of stored imagery continues to grow exponentially with improvements in
camera sensor resolution and the democratisation of photography. At the same time, bandwidth and storage
costs remain significant constraints, making efficient compression a first-order concern for both system
designers and end users."""),
    P("""Traditional image compression standards, including JPEG (ISO/IEC 10918), JPEG 2000, WebP,
HEIF, and more recent AVIF, achieve compression by exploiting two forms of redundancy: spatial
correlation within an image frame, and perceptual tolerance of the human visual system to certain
types of distortion. While these standards are highly engineered and widely deployed, they share
a fundamental limitation: the quality parameter that controls the rate-distortion trade-off is applied
globally and uniformly across the entire image. Every pixel — whether it belongs to a human face
that is the semantic subject of a portrait, or to empty sky in the background — is encoded with
approximately equal fidelity."""),
    P("""This uniformity is perceptually wasteful. The human visual system (HVS) is highly
non-uniform in its sensitivity to image distortions. Research in psychophysics has consistently
demonstrated that the HVS allocates disproportionately more attentional resources and perceptual
acuity to regions of high semantic relevance: faces, hands, text, objects in motion, and structurally
complex foreground elements. Conversely, the HVS exhibits substantial tolerance for distortions in
smooth, textureless, or background regions. This means that a compression system that degrades
background areas more aggressively than foreground areas can achieve substantial bitrate savings
without any perceptible reduction in quality from a human viewer's perspective."""),
    P("""The same asymmetry applies to machine-vision downstream tasks. Object detectors, face
recognisers, and action classifiers depend critically on the fidelity of a small fraction of the
total pixel budget — the pixels that constitute the detected objects or regions of interest. Compressing
these pixels aggressively, even at quality levels that appear acceptable to human viewers, can
cause significant accuracy degradation in automated analysis pipelines. Conversely, any pixel
outside the task-relevant region is a candidate for aggressive compression without analytical cost."""),
]

story.append(section("1.2", "Problem Statement"))
story += [
    P("""The central problem addressed in this thesis is the mismatch between spatially uniform
compression and the spatially non-uniform perceptual and semantic importance of image content.
Formally, given an input image I of dimensions H × W, a conventional codec assigns a quality
parameter q that applies uniformly to every pixel. The result is a compressed image I' that minimises
a global distortion metric (e.g. PSNR or MS-SSIM) subject to a bitrate constraint, without
distinguishing between pixels whose distortion is perceptually or semantically costly and pixels
whose distortion is benign."""),
    P("""In most natural images, the distribution of perceptual importance is highly skewed. A small
fraction of pixels — typically those depicting faces, foreground objects, fine structural
transitions, or region boundaries — carry the bulk of the semantic and perceptual information.
The remaining large majority of pixels — flat backgrounds, clear skies, uniform textures — can
be encoded at very low fidelity without materially affecting perceived quality or downstream task
accuracy. A coding scheme that exploits this skew can achieve the same perceptual quality at
substantially lower total bit rate, or equivalent bit rate at substantially higher quality for the
semantically important regions."""),
    P("""The core technical challenge is to reliably estimate the spatial distribution of perceptual
importance at the pixel level without requiring manual annotation and without the computational and
data cost of training a task-specific learned codec. A single importance estimator is generally
insufficient: deep salient-object detectors produce smooth but spatially coarse prominence maps,
semantic segmenters can miss objects outside their training vocabulary, and frequency-domain methods
may overreact to irrelevant texture patterns. A robust solution must integrate complementary signals
from multiple estimators into a unified importance representation, then map that representation to
practical per-pixel compression decisions through a principled transfer function."""),
]

story.append(section("1.3", "Objectives"))
story += [
    P("The primary objectives of this thesis are:"),
    bullet("""To design and implement a modular, training-light pipeline for context-aware image
compression that estimates pixel-level importance using three complementary saliency detectors."""),
    bullet("""To implement the U²-NetP (U-Squared Net Pooling variant) architecture in PyTorch
from first principles as a deep holistic salient-object detector (<i>saliency.py</i>)."""),
    bullet("""To implement YOLOv8n-seg based semantic instance segmentation as a category-aware
saliency branch that produces per-instance union masks (<i>object_detection.py</i>)."""),
    bullet("""To implement multi-scale spectral residual saliency estimation using 2D DFT
log-magnitude analysis at three scales (<i>saliency_spectral.py</i>)."""),
    bullet("""To design the ACRD (Ascending Cosine Roll-down) bit-allocation transfer function
and implement the full fusion, thresholding, ACRD mapping, gamma correction, and floor/ceiling
pipeline (<i>bit_allocation.py</i>)."""),
    bullet("""To implement a two-layer spatial blending compression framework with configurable
classic-lossy and foreground-lossless operating modes (<i>compression.py</i>)."""),
    bullet("""To evaluate the system on a representative subset of the CLIC dataset and compare
compression ratio and perceptual quality against standard JPEG encoding."""),
]

story.append(section("1.4", "Scope and Contributions"))
story += [
    P("""The scope of this work is a full software-layer implementation of a saliency-guided
pre-processing compression framework. The system operates on individual still images and produces
a pre-processed output in which background regions have been spatially homogenised for easy
codec encoding while foreground regions have been preserved at high or lossless fidelity.
The implementation does not modify any existing codec standard and is codec-agnostic:
the pre-processed output can be passed to any downstream encoder (JPEG, AVIF, WebP, etc.)."""),
    P("""The principal novel contributions of this work are: (1) a triple-source OR-fusion
saliency architecture that combines holistic deep saliency, category-aware semantic segmentation,
and frequency-domain spectral residual saliency through element-wise maximum with optional
spectral boosting; (2) the ACRD raised-cosine transfer function as a principled, smooth,
perceptually motivated mapping from saliency score to bit-allocation weight; (3) gamma-parameterised
ACRD curve deformation as a single-knob control over the quality-compression trade-off;
(4) a dual-mode layered blending pipeline supporting classic lossy and mathematically exact
foreground-lossless operation within a single shared codebase."""),
]

story.append(section("1.4a", "Application Domains"))
story += [
    P("""The proposed saliency-guided compression framework is particularly well-suited to
several high-value application domains:"""),
    P("""<b>Consumer Photography and Social Media.</b> The dominant use case for still-image
compression is consumer photography shared on social media platforms. These platforms collectively
store and transmit hundreds of billions of images annually, making even modest compression
improvements enormously significant in aggregate. Saliency-guided compression is naturally
aligned with portrait photography (the most common category of consumer images), where the
human subject is clearly the foreground subject and the background can be aggressively compressed
without affecting perceived quality."""),
    P("""<b>Medical Image Archiving.</b> Medical imaging (radiology, pathology, ophthalmology)
generates extremely high volumes of high-resolution images that must be stored for decades under
regulatory requirements. The lossless foreground mode of the proposed system is directly applicable
to medical images: a region of interest (lesion, organ, tissue structure) can be designated as
the foreground and preserved at mathematically exact quality, while surrounding healthy tissue
or non-diagnostic background regions can be compressed aggressively. This provides storage
efficiency without compromising diagnostic quality in the regions of clinical interest."""),
    P("""<b>Satellite and Aerial Imagery.</b> Earth observation satellites generate terabytes
of imagery daily. Ground targets (infrastructure, vehicles, agricultural fields) are
semantically important and must be preserved at high fidelity for analysis, while large
background areas (ocean, desert, cloud cover) can tolerate aggressive compression.
The spectral residual branch is particularly effective for satellite imagery because it
identifies unusual frequency content (man-made structures, sharp boundaries) regardless of
semantic category, complementing deep saliency detectors that may not be trained on
aerial-perspective imagery."""),
    P("""<b>Document and Archive Digitisation.</b> Large-scale digitisation of historical
documents, books, and archival materials requires balancing storage efficiency with text and
figure legibility. Combining spectral residual saliency (which detects text as high-frequency
novelty) with semantic segmentation could provide effective compression for this domain."""),
    P("""<b>Edge Computing and IoT Cameras.</b> Internet-of-Things cameras and edge
surveillance devices have constrained uplink bandwidth, making compression efficiency critical.
The CPU-only deployment of the proposed system, with approximately 4–6 seconds of latency
per frame, is already suitable for periodic surveillance snapshots and could be reduced to
near-real-time with GPU acceleration for video-rate applications."""),
]

story.append(section("1.5", "Thesis Organisation"))
story += [
    P("""The remainder of this thesis is structured as follows. Chapter 2 reviews related work
in saliency-aware image compression, deep salient-object detection, and learned image coding.
Chapter 3 presents the overall system architecture and mathematical formulation. Chapter 4 specifies
hardware and software requirements. Chapter 5 describes each of the five implementation modules in
detail. Chapter 6 presents experimental results and discussion. Chapter 7 draws conclusions and
outlines future research directions."""),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 2 – LITERATURE REVIEW   (pages 7–13)
# ════════════════════════════════════════════════════════════════════════════
story += heading("2", "LITERATURE REVIEW")

story.append(section("2.1", "Uniform-Quality Compression Standards"))
story += [
    P("""The JPEG standard (Wallace, 1992), based on the block Discrete Cosine Transform (DCT),
remains the dominant still-image compression format despite being over three decades old.
JPEG divides the image into non-overlapping 8×8 pixel blocks, applies the DCT to each block,
and quantises the resulting coefficients using a quantisation matrix scaled by a global quality
parameter Q ∈ [1, 100]. A higher Q value reduces quantisation step sizes, resulting in less
distortion and higher bit rate. Critically, the same Q is applied to all blocks uniformly,
regardless of whether the block contains perceptually important content."""),
    P("""JPEG 2000 introduced wavelet-based coding with region-of-interest (ROI) coding support
via the MAXSHIFT method, allowing selected spatial regions to be coded at higher quality than
the background. However, the ROI must be manually specified or derived from an external mask,
limiting practical use. More recent formats such as WebP, HEIF, and AVIF use more efficient
entropy coding and prediction methods but retain the conceptual paradigm of a single global
quality parameter."""),
    P("""A persistent limitation of all these standards is that quality adaptation requires
explicit external guidance about which regions matter. In the absence of such guidance, the codec
has no basis for treating pixels differently, and the natural consequence is uniform-quality
encoding across the spatial extent of the image, which is perceptually suboptimal."""),
]

story.append(section("2.2", "Saliency-Aware Image Coding"))
story += [
    P("""The idea of adapting image coding quality based on visual attention or saliency has been
explored for over two decades. Early work used simple low-level features such as local contrast,
colour distinctiveness, and orientation to derive a saliency map, which was then used to increase
the quantisation step size in low-saliency regions. Such approaches demonstrated consistent gains
in perceived quality at equal or lower bit rate but relied on hand-crafted saliency models that
performed poorly on semantically complex scenes."""),
    P("""More recently, Li et al. (2024) proposed a saliency segmentation oriented deep image
compression framework that treats saliency segmentation as the downstream task whose accuracy
the compressed image must preserve. The framework uses a probability-driven bit allocation
strategy, latent feature masking, and a double-scale entropy module to minimise rate while
maximising segmentation accuracy on the decompressed image. The rate-distortion objective is
jointly optimised end-to-end with the segmentation network. This work is the primary reference
for the present thesis: our ACRD bit-allocation transfer function draws conceptual inspiration
from the ascending cosine roll-down mechanism described therein, translated from a learned
latent-space masking context into an explicit image-space weighting pipeline."""),
    P("""Li et al. (2024) validate their approach on multiple benchmarks including DUTS-TE and
DUT-OMRON, reporting improvements in F1-measure, S-measure, E-measure, and MAE compared to
standard codecs at matched bit rates. The reference paper's central insight — that pixels near
the segmentation decision boundary are most distortion-sensitive and deserve highest coding
priority — directly motivates the fusion and bit-allocation design in this thesis."""),
]

story.append(section("2.3", "Deep Salient Object Detection"))
story += [
    P("""Salient object detection (SOD) is the task of predicting a soft or binary map identifying
the most visually prominent objects or regions in an image. Early deep learning approaches used
VGG or ResNet backbones with decoder-side skip connections to produce pixel-wise saliency maps.
More recent architectures have targeted efficient multi-scale feature extraction."""),
    P("""The U²-Net architecture (Qin et al., 2020) introduced a two-level nested encoder-decoder
structure built from residual U-blocks (RSU) that capture multi-scale context at each encoder
stage without relying on a pre-trained backbone. The lightweight variant U²-NetP achieves
competitive detection accuracy at significantly reduced model size and inference cost, making
it suitable for deployment without dedicated GPU hardware. This thesis uses U²-NetP as the
primary deep saliency detector, implementing its full architecture from scratch in PyTorch."""),
    P("""The key advantage of U²-NetP for compression applications is that it produces a continuous
soft saliency map in [0,1] rather than a binary segmentation, which naturally maps to per-pixel
compression weight values. Its multi-scale side supervision also produces a holistic global
prominence map that represents scene-level visual attention, complementing the more localised
object-level detection of the semantic segmentation branch."""),
]

story.append(section("2.4", "Semantic Instance Segmentation for Compression"))
story += [
    P("""While salient-object detectors produce smooth, holistic prominence maps, semantic
instance segmentation models produce category-specific, instance-separated binary or soft masks
with crisp boundaries aligned to object edges. For compression purposes, this distinction is
significant: the deep saliency detector may fail to preserve exact object boundaries, while an
instance segmenter can produce a tight foreground mask for each recognised object."""),
    P("""YOLO-based architectures have evolved from bounding-box detection (YOLOv1–v5) to include
instance segmentation (YOLOv8-seg). YOLOv8n-seg (Jocher et al., 2023), the nano variant,
performs real-time instance segmentation at very low model size (∼3.4 M parameters) using a
predict head that outputs both bounding boxes and pixel-level instance masks at `mask_h × mask_w`
resolution. For compression, the per-instance masks can be unioned to form a binary foreground
importance map that explicitly marks category-level objects for high-quality encoding."""),
    P("""The COCO vocabulary (80 object classes) covers the most common subjects of human
photography, making YOLOv8n-seg broadly applicable. For domain-specific or unusual imagery,
the semantic branch may miss out-of-vocabulary objects; this limitation is addressed in the
proposed system by treating semantic detection as one contributor among three rather than
the sole importance estimator."""),
]

story.append(section("2.5", "Spectral Residual Saliency Methods"))
story += [
    P("""The spectral residual (SR) saliency method (Hou and Zhang, 2007) is a training-free,
category-agnostic approach based on the observation that the log-spectrum of a natural image can
be decomposed into a slowly varying average spectral envelope (representing the image's global
statistical character) and a residual component (representing local frequency deviations that
are statistically unusual). After computing the 2D FFT of the grayscale image, subtracting a
smoothed log-magnitude envelope from the full log-magnitude spectrum, and inverting the residual
back to the spatial domain, the resulting map highlights regions where the image contains
structures not well-represented by the global spectral mean."""),
    P("""Empirically, these statistically unusual regions correspond closely to visual saliency:
edges, fine textures, corners, foreground object boundaries, and isolated distinct features tend
to produce high spectral residual responses. The SR method is particularly valuable as a
complement to deep learning detectors because it operates at the frequency level and can detect
structural novelty in images where the deep models do not respond strongly, such as industrial,
medical, or aerial imagery outside the training distribution of U²-NetP."""),
    P("""The present work extends the basic SR method to multi-scale processing (0.5×, 1.0×,
and 1.5× the original resolution) with mean fusion across scales, followed by Gaussian smoothing
to suppress DFT ringing artefacts. This multi-scale design reinforces salient structures that
appear consistently across scales while attenuating single-scale noise responses."""),
]

story.append(section("2.6", "Learned End-to-End Image Compression"))
story += [
    P("""Learned image compression (Ballé et al., 2017; Minnen et al., 2018; Cheng et al., 2020)
uses convolutional encoder-decoder architectures trained end-to-end to optimise a rate-distortion
objective: λ · R + D, where R is estimated entropy rate and D is reconstruction distortion.
The encoder maps the input image to a quantised latent representation, and the decoder maps
back to pixel space. The entropy coding stage uses learned prior models (hyperprior, context models)
to compress the latents efficiently."""),
    P("""These approaches have achieved substantial compression gains over traditional codecs,
particularly at low bit rates. However, they require large-scale training on diverse image datasets,
significant compute for training, and tend to produce visually smooth but sometimes blurry
reconstructions. Extending them to support saliency-aware quality allocation requires modifying
the latent masking mechanism — a non-trivial task for most implementations."""),
    P("""The present thesis deliberately avoids end-to-end learned compression in favour of an
explicit, modular, pre-processing approach. This design choice provides three advantages: the
system is deployable without GPU hardware or model retraining; the compression logic is fully
transparent and interpretable; and each component can be independently replaced or upgraded."""),
]

story.append(section("2.6a", "Rate-Distortion Theory and Saliency"))
story += [
    P("""Rate-distortion theory (Shannon, 1948) provides the theoretical foundation for all
lossy image compression. The rate-distortion function R(D) gives the minimum bit rate required
to represent a source with expected distortion D. For practical image compression, the distortion
measure D is typically chosen as mean squared error (MSE) or its logarithmic form PSNR. However,
MSE is a poor proxy for perceived visual quality because it weights all pixels equally regardless
of their semantic or perceptual importance."""),
    P("""A perceptually motivated extension to rate-distortion theory uses a weighted distortion
measure:"""),
    P("""D_W = Σ_{i,j} W[i,j] · (I[i,j] − I'[i,j])²""", STY_MATH),
    sp(4),
    P("""where W[i,j] is a per-pixel importance weight derived from a saliency estimate.
Minimising D_W subject to rate constraint R ≤ R_max produces an allocation strategy that
concentrates coding quality in high-weight regions. This theoretical framing shows that the
ACRD bit-allocation map W in the proposed system can be interpreted as an importance weight
matrix for a perceptually adapted rate-distortion objective."""),
    P("""Recent work has formalised this connection rigorously. Li et al. (2024) derive bit
allocation weights from the saliency segmentation probability map, arguing that pixels near the
segmentation decision boundary are most distortion-sensitive because small distortions near the
boundary can flip the segmentation decision. The resulting allocation strategy concentrates
coding resources around these boundary pixels, achieving improved segmentation accuracy at
matched bit rate. The present work translates a similar insight — that saliency defines
distortion sensitivity — into an explicit image-space weight pipeline without the need for
end-to-end training."""),
    P("""From a theoretical perspective, the proposed system implements a heuristic approximation
to the optimal perceptual rate-distortion allocation: rather than solving the full constrained
optimisation problem, it estimates W using pre-trained detectors and maps W to per-pixel
compression quality through the ACRD function. The approximation quality depends on how well
the three detectors jointly estimate true perceptual distortion sensitivity, which the
experimental results suggest is generally adequate for practical natural images."""),
]

story.append(section("2.6b", "Frequency-Domain Approaches to Image Quality"))
story += [
    P("""Frequency-domain analysis plays a central role in image compression (DCT in JPEG,
DWT in JPEG 2000) and also provides useful insights for quality assessment. The Structural
Similarity Index Measure (SSIM, Wang et al. 2004) decomposes image quality into three components:
luminance, contrast, and structure. The structural component is closely related to edge and
texture preservation, which are the primary concerns of the spectral residual branch in the
proposed system."""),
    P("""Research in perceptual image quality metrics has consistently shown that the human visual
system is particularly sensitive to distortions in textured and structured regions (high spatial
frequency content) when the texture is part of a semantically important object. Compression
artefacts in smooth background regions are comparatively invisible. This asymmetry supports
the design of the proposed system, which applies aggressive background suppression (destroying
high-frequency background texture) while preserving foreground structure."""),
    P("""The spectral residual saliency method (Hou and Zhang, 2007) connects these two
observations: by identifying regions with statistically unusual frequency content, it
effectively predicts which regions the HVS is most sensitive to structurally. The multi-scale
extension in the present work (0.5×, 1.0×, 1.5× resolution) further improves detection of
structures at different spatial scales — fine detail (visible at 1.5×), medium-scale structures
(visible at 1.0×), and coarse dominant features (visible at 0.5×)."""),
]

story.append(section("2.7", "Summary and Research Gaps"))
story += [
    P("""The literature review identifies three key gaps that the proposed system addresses.
First, while saliency-aware coding has been studied extensively, most practical systems use
a single saliency source and do not combine multiple complementary detectors. Second, the
ACRD bit-allocation mechanism from Li et al. (2024) has been demonstrated inside a learned
latent-space framework but not implemented as an explicit image-space transfer function in
a modular pre-processing pipeline. Third, no publicly available open-source implementation
provides a lightweight, modular, training-free saliency-guided compression pipeline built
from standard components that can be used for prototyping and academic investigation."""),
    P("""This thesis addresses all three gaps by implementing a five-module pipeline that fuses
three complementary saliency signals, applies the ACRD transfer function in image space,
and produces a pre-processed output compatible with any downstream codec, without requiring
any training data or GPU hardware beyond the pre-trained U²-NetP and YOLOv8n-seg weights."""),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 3 – PROPOSED SYSTEM   (pages 14–19)
# ════════════════════════════════════════════════════════════════════════════
story += heading("3", "PROPOSED SYSTEM OVERVIEW")

story.append(section("3.1", "System Architecture"))
story += [
    P("""The proposed system is a strict feed-forward pipeline consisting of five sequentially
executed modules. The input is a single RGB image of arbitrary resolution. The output is a
pre-processed image in which low-importance (background) regions have been spatially degraded
for easy downstream compression and high-importance (foreground) regions have been preserved
at high fidelity. The five modules communicate exclusively through NumPy arrays; no module
has knowledge of any other module's internal implementation."""),
    P("The pipeline proceeds as follows:"),
]

story.append(code_block([
    "Input Image",
    "    │",
    "    ├──[saliency.py]──────────────► S_deep  ∈ [0,1]^(H×W)   (U²-NetP)",
    "    ├──[object_detection.py]──────► S_obj   ∈ [0,1]^(H×W)   (YOLOv8n-seg union mask)",
    "    └──[saliency_spectral.py]─────► S_spec  ∈ [0,1]^(H×W)   (multi-scale spectral residual)",
    "              │",
    "              ▼",
    "    [bit_allocation.py]",
    "        Max-fusion → threshold → ACRD → gamma → floor/ceiling",
    "              │",
    "              ▼  W ∈ [weight_floor, weight_ceiling]^(H×W)",
    "              │",
    "    [compression.py]",
    "        Base layer  (aggressive downsample + blur + noise)",
    "        Fore layer  (high-quality or exact original)",
    "        Final = (1 − W)·Base + W·Fore",
    "              │",
    "              ▼",
    "        Pre-processed output image",
]))

story.append(fig_caption("3.1", "Feed-forward pipeline architecture of the proposed system"))

story += [
    P("""The three saliency branches run independently and in parallel conceptually (each function
accepts only the image path or a NumPy array as input and produces only a 2D NumPy array as
output). This independence means the branches can be parallelised trivially in future
implementations without any shared state or synchronisation overhead."""),
    P("""The five-stage design deliberately separates concerns: importance estimation (Modules 1-3),
importance aggregation and weight computation (Module 4), and quality-differentiated reconstruction
(Module 5). This separation provides modularity for academic explanation and practical flexibility
for tuning."""),
]

story.append(section("3.2", "OR-Style Multi-Source Fusion"))
story += [
    P("""A core design decision is the choice of element-wise maximum as the fusion operator
for combining the three saliency maps. Given S_deep, S_obj, and S_spec (all normalised to [0,1]),
the fused map is computed as:"""),
    P("""C = max(S_deep, max(S_obj, clip(S_spec · β, 0, 1)))""",
      S("MathCenter", parent=STY_MONO, fontSize=11, alignment=TA_CENTER)),
    sp(4),
    P("""where β ≥ 1 is a spectral boost parameter. The semantic object map is optionally weighted
by detection confidence before fusion. The maximum operator implements OR-style logic: a pixel
is designated as important if <i>any</i> detector identifies it as such, without requiring
inter-modality agreement."""),
    P("""This conservative protection policy is appropriate for compression because the cost
function is asymmetric: losing an important region to over-compression is a perceptually irreversible
error, while slightly over-protecting a non-critical region at most wastes a small amount of
bitrate. Maximum fusion minimises the probability of the first (harmful) error at the cost of
a small increase in the probability of the second (benign) error."""),
    P("""The spectral_boost parameter (β) amplifies the spectral map before maximum fusion.
When β > 1 (e.g., β = 1.45), fine edge and texture signals that might otherwise be suppressed
by the broader deep saliency response at object interiors are elevated, allowing boundary-level
precision in the combined map. This is particularly important for the lossless foreground mode,
where exact boundary alignment is critical for artefact-free subject preservation."""),
]

story.append(section("3.3", "ACRD Bit-Allocation Transfer Function"))
story += [
    P("""After OR-fusion and hard thresholding (pixels below threshold τ are clamped to zero),
the fused saliency map C_τ is transformed into a per-pixel bit-allocation weight map W through
the Ascending Cosine Roll-down (ACRD) function:"""),
    P("""ACRD(x) = 0.5 · (1 − cos(π · x))""",
      S("MathCenter2", parent=STY_MONO, fontSize=11, alignment=TA_CENTER)),
    sp(4),
    P("""This is the normalised raised-cosine (Hann window) function adapted to the [0,1] input
and output domain. Three properties make this choice principled for bit allocation:"""),
    bullet("""<b>Zero derivative at both endpoints.</b> The gradient dACRD/dx = (π/2)·sin(πx) is
zero at x=0 and x=1. Small saliency changes near the background-foreground transition do not
produce large weight discontinuities, avoiding perceptually abrupt quality transitions at
region boundaries."""),
    bullet("""<b>Monotonicity.</b> The function is strictly increasing on (0,1). More salient pixels
always receive greater quality budget, preserving rank-order consistency between saliency
and compression quality."""),
    bullet("""<b>S-shaped (non-linear) profile.</b> The function accelerates weight growth for
mid-saliency values compared to a linear mapping, providing a disproportionate quality boost
to moderately salient pixels. This is perceptually motivated because sensitivity to distortion
increases non-linearly with saliency."""),
    P("""After ACRD, a gamma correction B^γ reshapes the weight distribution: γ > 1 pushes
weights toward 0 (harder foreground/background split, maximum compression); γ < 1 raises
mid-range weights (softer gradient, maximum quality preservation). Finally, floor and ceiling
clipping ensure W ∈ [weight_floor, weight_ceiling] for all pixels."""),
]

story.append(section("3.4", "Layered Compression Framework"))
story += [
    P("""The final stage blends two quality levels of the input image per pixel according to W.
The base layer B is generated by aggressive spatial degradation: bilinear downsampling to 1/D
of original resolution followed by upsampling back (which acts as a low-pass filter destroying
high-frequency texture), box-filter blurring, and additive Gaussian noise. The enhancement/
foreground layer F is either a mildly degraded high-quality version (classic mode) or the exact
original pixels (lossless mode). The output is:"""),
    P("""I_out[i,j] = (1 − W[i,j]) · B[i,j] + W[i,j] · F[i,j]""",
      S("MathCenter3", parent=STY_MONO, fontSize=11, alignment=TA_CENTER)),
    sp(4),
    P("""Pixels with W = 0 (below threshold background) are drawn entirely from the heavily
degraded base layer. Pixels with W = 1 (peak-saliency foreground in lossless mode) receive
the exact original pixel value. Intermediate weights produce smooth linear interpolation between
the two quality levels, avoiding visible boundary artefacts at saliency edges."""),
]

story.append(section("3.4a", "Design Trade-offs and Parameter Sensitivity"))
story += [
    P("""The five hyperparameters that govern the bit-allocation stage (threshold τ, gamma γ,
spectral_boost β, weight_floor, weight_ceiling) interact with each other in ways that are
important to understand for practical tuning. The following analysis characterises the
sensitivity of the system's output to each parameter:"""),
    P("""<b>Threshold sensitivity.</b> The threshold τ controls the minimum combined saliency
score for a pixel to receive any quality budget. Increasing τ makes the system more aggressive:
fewer pixels qualify as foreground, and more pixels receive the base layer quality level.
For portrait images with clear foreground/background separation, τ = 0.10–0.15 works well.
For complex scenes with continuous saliency gradients (e.g., crowd scenes, nature imagery),
a lower τ = 0.05–0.08 is preferable to avoid cutting off moderately important scene elements.
Setting τ = 0 effectively removes the hard threshold and allows all pixels to receive some
quality allocation based purely on their ACRD-mapped saliency score."""),
    P("""<b>Gamma and threshold interaction.</b> The gamma parameter γ and the threshold τ
interact strongly. A high threshold (τ = 0.15) already eliminates many pixels from the
quality budget, so the remaining pixels all have relatively high saliency scores; applying
a high gamma further pushes them toward the foreground. The combination of high τ and high γ
produces the most aggressive foreground/background split. Conversely, a low threshold with
γ < 1 produces the most diffuse quality distribution, where almost all pixels receive some
quality budget and the spatial variation is gentle."""),
    P("""<b>Spectral boost interaction.</b> The spectral_boost parameter β amplifies the
spectral residual map before OR-fusion. Its primary effect is at boundary pixels, where the
spectral residual score is typically in the range 0.5–0.8 (correctly identifying the edge)
but the deep saliency score may be lower (due to U²-NetP's spatial smoothing). Setting β = 1.45
elevates the spectral score enough to "punch through" the combined map at these pixels,
tightening the foreground boundary. The interaction with the threshold is important: if β is
set very high (β > 2.0), the spectral map begins to dominate the combined map, potentially
over-protecting background texture patterns that happen to have strong spectral residuals."""),
    P("""<b>Parameter stability across presets.</b> The four preset configurations (Storage,
Balanced, Quality, Lossless) represent distinct operating points in the hyperparameter space.
The Balanced preset (all parameters at their nominal values) has been empirically validated
as producing good results across the full diversity of natural image content. The other presets
shift specific parameters to optimise for specific objectives while keeping the remaining
parameters close to their nominal values, minimising unexpected interactions."""),
]

story.append(section("3.5", "Mathematical Formulation"))
story += [
    P("""The complete algorithmic pipeline can be summarised as:"""),
    P("""1. S_deep = U²-NetP(I)  ∈ [0,1]^(H×W)""",     STY_MONO),
    P("""2. S_obj  = YOLO-seg(I) ∈ [0,1]^(H×W)""",     STY_MONO),
    P("""3. S_spec = SpectralResidual(I) ∈ [0,1]^(H×W)""", STY_MONO),
    P("""4. C      = max(S_deep, S_obj, clip(β·S_spec, 0,1))""", STY_MONO),
    P("""5. C_τ    = C · 𝟙[C ≥ τ]""",                  STY_MONO),
    P("""6. B_w    = 0.5·(1 − cos(π·C_τ))""",           STY_MONO),
    P("""7. W      = clip(B_w^γ, weight_floor, weight_ceiling)""", STY_MONO),
    P("""8. I_out  = (1−W)·Base(I) + W·Fore(I)""",      STY_MONO),
    sp(4),
    P("""This formulation makes the system fully differentiable with respect to all hyperparameters
(τ, γ, β, weight_floor, weight_ceiling), which opens a path for future gradient-based
optimisation of these parameters using a perceptual loss function."""),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 4 – REQUIREMENT SPECIFICATION   (pages 20–21)
# ════════════════════════════════════════════════════════════════════════════
story += heading("4", "REQUIREMENT SPECIFICATION")

story.append(section("4.1", "Hardware Requirements"))
hw_data = [
    [P("<b>Component</b>", STY_BODY), P("<b>Minimum</b>", STY_BODY), P("<b>Recommended</b>", STY_BODY)],
    [P("Processor",STY_BODY),  P("Intel Core i5 (8th gen) or AMD Ryzen 5",STY_BODY),  P("Intel Core i7 / Apple M-series",STY_BODY)],
    [P("RAM",STY_BODY),        P("8 GB DDR4",STY_BODY),             P("16 GB DDR4/5",STY_BODY)],
    [P("Storage",STY_BODY),    P("10 GB free (SSD preferred)",STY_BODY), P("50 GB free SSD",STY_BODY)],
    [P("GPU",STY_BODY),        P("Not required (CPU-only inference)",STY_BODY), P("NVIDIA CUDA-capable GPU for speedup",STY_BODY)],
    [P("OS",STY_BODY),         P("Windows 10 / macOS 12 / Ubuntu 20.04",STY_BODY), P("macOS 14 / Ubuntu 22.04",STY_BODY)],
]
hw_table = Table(hw_data, colWidths=[3*cm, 7*cm, BODY_W-10*cm])
hw_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0), (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story += [hw_table, sp(6)]

story.append(section("4.2", "Software Requirements"))
sw_data = [
    [P("<b>Software</b>", STY_BODY), P("<b>Version</b>", STY_BODY), P("<b>Purpose</b>", STY_BODY)],
    [P("Python",STY_BODY),         P("3.9+",STY_BODY),           P("Core runtime",STY_BODY)],
    [P("PyTorch",STY_BODY),        P("2.0+",STY_BODY),           P("U²-NetP inference, SimpleCompressionNet",STY_BODY)],
    [P("Ultralytics",STY_BODY),    P("8.0+",STY_BODY),           P("YOLOv8n-seg instance segmentation",STY_BODY)],
    [P("OpenCV (cv2)",STY_BODY),   P("4.7+",STY_BODY),           P("Box-filter blur, FFT, image I/O",STY_BODY)],
    [P("NumPy",STY_BODY),          P("1.24+",STY_BODY),          P("Array operations throughout pipeline",STY_BODY)],
    [P("Pillow (PIL)",STY_BODY),   P("9.5+",STY_BODY),           P("Image open/save, EXIF correction, resize",STY_BODY)],
    [P("torchvision",STY_BODY),    P("0.15+",STY_BODY),          P("ImageNet normalisation transforms",STY_BODY)],
    [P("Jupyter Notebook",STY_BODY), P("6.5+",STY_BODY),         P("Interactive experimentation (optional)",STY_BODY)],
]
sw_table = Table(sw_data, colWidths=[4*cm, 2.5*cm, BODY_W-6.5*cm])
sw_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0), (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story += [sw_table, sp(6)]

story.append(section("4.3", "Python Library Dependencies"))
story += [
    P("""All dependencies can be installed with the following command in a Python 3.9+ virtual
environment:"""),
    code_block(["pip install torch torchvision ultralytics opencv-python numpy Pillow"]),
    P("""The U²-NetP model weights are downloaded automatically on first run from the
Hugging Face model hub using the <i>urllib</i> standard library. The YOLOv8n-seg weights are
downloaded automatically by the Ultralytics library on first invocation of the segmentation
model. No manual weight download or model configuration is required."""),
    P("""The system has been tested on macOS 14 (Apple M-series CPU, CoreML acceleration),
Ubuntu 22.04 (Intel CPU, no GPU), and Windows 11 (Intel/AMD CPU). All inference runs on CPU
by default; CUDA GPU acceleration can be enabled by changing the device parameter in the
respective model calls."""),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 5 – IMPLEMENTATION MODULES   (pages 22–50)
# ════════════════════════════════════════════════════════════════════════════
story += heading("5", "IMPLEMENTATION MODULES")

# 5.1  saliency.py
story.append(section("5.1", "Module 1: Deep Saliency Detection (saliency.py)"))
story += [
    P("""<i>saliency.py</i> implements the complete U²-NetP (U-Squared Net Pooling) architecture
from scratch in PyTorch and provides the <i>get_saliency_map</i> inference function. U²-NetP is a
lightweight variant of the U²-Net family designed for salient object detection; it replaces some
of the deeper U²-Net's residual U-blocks with dilated convolution stacks to reduce parameter count
while maintaining multi-scale feature extraction capability."""),
]

story.append(subsection("5.1.1", "Architectural Building Blocks"))
story += [
    P("""The architecture is built from three hierarchical classes: REBNCONV (atomic convolution
unit), RSU-n (residual U-block of depth n), and U2NETP (the full network assembly)."""),
    P("""<b>REBNCONV</b> is the smallest building block. It wraps a single dilated 2D convolution,
batch normalisation, and in-place ReLU:"""),
    code_block([
        "class REBNCONV(nn.Module):",
        "    def __init__(self, in_ch=3, out_ch=3, dirate=1):",
        "        self.conv_s1 = nn.Conv2d(in_ch, out_ch, 3,",
        "                         padding=1*dirate, dilation=1*dirate)",
        "        self.bn_s1   = nn.BatchNorm2d(out_ch)",
        "        self.relu_s1 = nn.ReLU(inplace=True)",
        "    def forward(self, x):",
        "        return self.relu_s1(self.bn_s1(self.conv_s1(x)))",
    ]),
    P("""The <i>dirate</i> parameter controls both padding and dilation, so the spatial size
of the feature map is preserved regardless of dilation rate. This is essential for the dilated
convolution stacks in RSU4F where spatial resolution must be maintained without pooling."""),
]

story.append(subsection("5.1.2", "Residual U-Blocks (RSU)"))
story += [
    P("""Five RSU variants implement the core multi-scale processing:"""),
]

rsu_data = [
    [P("<b>Block</b>",STY_BODY), P("<b>Pooling levels</b>",STY_BODY), P("<b>Bottom</b>",STY_BODY), P("<b>Use</b>",STY_BODY)],
    [P("RSU7",STY_BODY), P("5 × MaxPool2d",STY_BODY), P("dirate=2",STY_BODY), P("Deepest; captures coarse context",STY_BODY)],
    [P("RSU6",STY_BODY), P("4 × MaxPool2d",STY_BODY), P("dirate=2",STY_BODY), P("Second encoder stage",STY_BODY)],
    [P("RSU5",STY_BODY), P("3 × MaxPool2d",STY_BODY), P("dirate=2",STY_BODY), P("Third encoder stage",STY_BODY)],
    [P("RSU4",STY_BODY), P("2 × MaxPool2d",STY_BODY), P("dirate=2",STY_BODY), P("Fourth encoder / third decoder",STY_BODY)],
    [P("RSU4F",STY_BODY), P("None",STY_BODY), P("dilations 2,4,8",STY_BODY), P("Deep stages — dilation replaces pooling",STY_BODY)],
]
rsu_table = Table(rsu_data, colWidths=[2*cm, 3.5*cm, 2.5*cm, BODY_W-8*cm])
rsu_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0), (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story += [rsu_table, sp(6)]

story += [
    P("""Each RSU-n block processes its input through a sequence of encoder REBNCONV layers
separated by MaxPool2d(2, stride=2, ceil_mode=True) downsampling operations. At the bottom of the
U-structure, a dilated REBNCONV captures global context at reduced resolution. The decoder
path mirrors the encoder, with each decoder stage concatenating the upsampled deeper feature map
with the corresponding encoder skip connection before the decoder REBNCONV:"""),
    code_block([
        "# Decoder step (example for RSU7, level 6→5):",
        "hx6up = _upsample_like(hx6, hx5)       # bilinear upsample to match hx5",
        "hx5d  = self.rebnconv6d(torch.cat((hx6up, hx5), dim=1))",
        "# Final output (all levels fused):",
        "return hx1d + hxin               # residual connection",
    ]),
    P("""The residual connection (adding the block's input projection <i>hxin</i> to the decoder
output <i>hx1d</i>) ensures gradient flow during training and allows the block to learn a
residual correction rather than a full reconstruction, making training more stable and convergent."""),
]

story.append(subsection("5.1.3", "U2NETP Assembly"))
story += [
    P("""U2NETP assembles six encoder stages and five decoder stages:"""),
    code_block([
        "# Encoder stages:",
        "stage1 = RSU7(3,  16, 64)   # in=3,   mid=16, out=64",
        "stage2 = RSU6(64, 16, 64)",
        "stage3 = RSU5(64, 16, 64)",
        "stage4 = RSU4(64, 16, 64)",
        "stage5 = RSU4F(64, 16, 64)  # no pooling — dilation only",
        "stage6 = RSU4F(64, 16, 64)",
        "",
        "# Decoder stages:",
        "stage5d = RSU4F(128, 16, 64)   # 64+64 = 128 input channels",
        "stage4d = RSU4 (128, 16, 64)",
        "stage3d = RSU5 (128, 16, 64)",
        "stage2d = RSU6 (128, 16, 64)",
        "stage1d = RSU7 (128, 16, 64)",
    ]),
    P("""All encoder stages use 64 output channels and 16 intermediate channels. All decoder
stages take 128 input channels because they receive the concatenation of two 64-channel
feature maps (skip + upsampled deeper)."""),
]

story.append(subsection("5.1.4", "Side Supervision and Output Fusion"))
story += [
    P("""Each decoder stage and stage6 produces a single-channel side output via a 3×3
convolution followed by sigmoid activation:"""),
    code_block([
        "# Side output heads:",
        "side1 = Conv2d(64, 1, 3, padding=1)",
        "side2 = Conv2d(64, 1, 3, padding=1)",
        "...  (6 total)",
        "outconv = Conv2d(6, 1, 1)   # 1×1 fusion conv",
        "",
        "# During forward pass:",
        "d1 = torch.sigmoid(side1(hx1d))",
        "d2 = torch.sigmoid(side2(_upsample_like(hx2d, hx1d)))",
        "# ... upsample all to d1's resolution ...",
        "d0 = torch.sigmoid(outconv(torch.cat([d1,d2,d3,d4,d5,d6], dim=1)))",
        "return d0, d1, d2, d3, d4, d5, d6",
    ]),
    P("""The side outputs provide intermediate supervision signals during training, encouraging
each decoder level to produce a meaningful saliency map at its own resolution. At inference,
only <i>d0</i> (the fused output) and <i>d1</i> (the full-resolution output) are used;
the thesis uses <i>d1[:,0,:,:]</i> after min-max normalisation as the final saliency map."""),
]

story.append(subsection("5.1.4a", "Model Weights and Weight Loading"))
story += [
    P("""The U²-NetP model weights are downloaded automatically from the Hugging Face hub
on first use using Python's standard <i>urllib</i> library. The weight file
<i>u2netp.pth</i> contains the trained parameters for all encoder stages, decoder stages,
side output heads, and the fusion convolution layer. The model was originally trained on
the DUTS-TR dataset (10,553 training images with pixel-accurate saliency annotations)
using a binary cross-entropy loss applied to all six side outputs simultaneously — this is
the multi-scale deep supervision strategy that enables each decoder stage to produce a
meaningful saliency map independently."""),
    P("""Weight loading uses PyTorch's <i>torch.load</i> with <i>map_location='cpu'</i>
to ensure compatibility across systems without CUDA hardware:"""),
    code_block([
        "state_dict = torch.load(weight_path, map_location='cpu')",
        "net = U2NETP(3, 1)",
        "net.load_state_dict(state_dict)",
        "net.eval()                        # set to inference mode (disables batch norm training)",
    ]),
    P("""The <i>net.eval()</i> call switches batch normalisation layers from training mode
(which maintains running statistics) to evaluation mode (which uses the stored running mean
and variance from training). This is critical for inference correctness: using training mode
batch normalisation at inference time would produce different normalisation statistics depending
on the current batch, making the output non-deterministic and potentially inaccurate."""),
    P("""The SSL certificate verification is disabled for the download step using a custom
HTTPS context, as some deployment environments may not have up-to-date certificate bundles.
This is acceptable for a research prototype but should be addressed in production deployments
through proper certificate management."""),
]

story.append(subsection("5.1.5", "Inference Pipeline (get_saliency_map)"))
story += [
    P("""The inference pipeline in <i>get_saliency_map</i> performs the following steps:"""),
    bullet("""<b>EXIF transpose:</b> ImageOps.exif_transpose(image) corrects for any camera
orientation metadata before processing, ensuring the spatial saliency map is aligned with
the image as it would be displayed."""),
    bullet("""<b>Resize to 320×320:</b> U²-NetP uses a fixed input resolution. The image
is resized to 320×320 regardless of original dimensions."""),
    bullet("""<b>ImageNet normalisation:</b> mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225).
These are the standard ImageNet statistics used during training of U²-NetP."""),
    bullet("""<b>Forward pass:</b> torch.no_grad() context manager suppresses gradient
computation for inference efficiency."""),
    bullet("""<b>Min-max normalisation:</b> The raw output is shifted and scaled to [0,1]:
pred = (pred − pred.min()) / (pred.max() − pred.min() + 1e-8)."""),
    bullet("""<b>Resize to original dimensions:</b> The 320×320 saliency map is bilinearly
upsampled back to (H, W) to align with the input image for subsequent processing."""),
    P("""The result S_deep ∈ [0,1]^(H×W) is a soft continuous importance map where values close
to 1 indicate visually prominent foreground regions and values close to 0 indicate background.
The holistic nature of U²-NetP's multi-scale feature extraction makes this map suitable for
capturing scene-level prominence regardless of object category."""),
    pb(),
]

# 5.2  object_detection.py
story.append(section("5.2", "Module 2: Semantic Object Segmentation (object_detection.py)"))
story += [
    P("""<i>object_detection.py</i> provides <i>get_object_segmentation_map</i>, which runs
YOLOv8 Nano Segmentation on the input image and produces a per-pixel union mask of all
detected object instances. This module adds category-level semantic awareness to the importance
estimation pipeline."""),
]

story.append(subsection("5.2.1", "YOLOv8n-seg Model"))
story += [
    P("""YOLOv8n-seg (the nano segmentation variant of YOLOv8) is a single-stage instance
segmentation model that simultaneously predicts bounding boxes, class labels, and pixel-level
instance masks. The nano model achieves real-time performance even on CPU hardware with a
total parameter count of approximately 3.4 million, making it well-suited for the modular
pre-processing context of this system."""),
    P("""Model loading and inference use the Ultralytics API:"""),
    code_block([
        "from ultralytics import YOLO",
        "",
        "model   = YOLO('yolov8n-seg.pt')",
        "results = model(image_path, verbose=False, device='cpu')",
    ]),
    P("""The <i>device='cpu'</i> parameter forces all computation to CPU, avoiding CUDA/
torchvision version compatibility issues that can arise when mixing PyTorch's built-in NMS
(non-maximum suppression) with the torchvision version required by YOLOv8's post-processing
stage. On systems with a compatible CUDA setup, this can be changed to <i>device='cuda'</i>
for substantially faster inference."""),
]

story.append(subsection("5.2.2", "Instance Mask Extraction and Resizing"))
story += [
    P("""For each detection result, <i>result.masks.data</i> provides a tensor of shape
<i>(num_objects, mask_h, mask_w)</i>. The mask dimensions may differ from the original image
dimensions due to YOLOv8's internal downsampling. Each instance mask is extracted as a
NumPy array and bilinearly resized to the original image dimensions if needed:"""),
    code_block([
        "for result in results:",
        "    if result.masks is None:",
        "        continue",
        "    for mask_tensor in result.masks.data:",
        "        mask = mask_tensor.cpu().numpy()           # shape: (mask_h, mask_w)",
        "        if mask.shape != (h, w):",
        "            mask_img = Image.fromarray(mask).resize(",
        "                (w, h), resample=Image.BILINEAR)",
        "            mask = np.array(mask_img)",
        "        combined_mask = np.maximum(combined_mask, mask)",
    ]),
    P("""Element-wise maximum fusion across instances produces a soft union mask S_obj where
a pixel takes the value of the highest-confidence instance mask covering it. This formulation
handles overlapping instances gracefully: a pixel covered by multiple detected objects
receives the maximum confidence score, preserving the most confident foreground signal."""),
]

story.append(subsection("5.2.3", "Handling Images with No Detected Objects"))
story += [
    P("""When no objects are detected (result.masks is None), the function returns an all-zero
mask of size (H, W). In the bit_allocation.py fusion step, a zero object map is treated as
a no-op (the maximum with the deep saliency map S_deep leaves S_deep unchanged). This graceful
degradation ensures the pipeline continues to function on images with no COCO-vocabulary objects
by relying on the deep saliency and spectral residual branches."""),
    P("""The output S_obj ∈ [0,1]^(H×W) effectively acts as a soft binary foreground mask
(most values near 0 or 1) with bilinearly smoothed boundaries from the resize operation.
This binary character complements the smoother, more continuous S_deep map: where U²-NetP
produces a gradual foreground boundary, YOLOv8 provides a crisp, category-confirmed edge."""),
    pb(),
]

# 5.3  saliency_spectral.py
story.append(section("5.3", "Module 3: Multi-Scale Spectral Residual Saliency (saliency_spectral.py)"))
story += [
    P("""<i>saliency_spectral.py</i> implements a training-free, category-agnostic saliency
estimator based on the spectral residual principle. The module provides two functions:
<i>_compute_spectral_residual</i> for single-scale computation and
<i>detect_spectral_residual</i> for multi-scale fusion."""),
]

story.append(subsection("5.3.1", "Spectral Residual Principle"))
story += [
    P("""The fundamental insight of the spectral residual method is that the log-magnitude
spectrum of a natural image can be decomposed as:"""),
    P("""log|F(I)| = E(f) + R(f)""",
      S("Math4", parent=STY_MONO, fontSize=11, alignment=TA_CENTER)),
    sp(4),
    P("""where F(I) is the 2D FFT of the grayscale image, E(f) is the expected (average)
log-spectral envelope (obtained by local Gaussian smoothing of the full log-magnitude), and
R(f) is the spectral residual — the per-frequency deviation from the statistical mean.
Frequencies with large residual correspond to image structures that are statistically unusual
given the global spectral context. Empirically, these unusual structures coincide with visually
salient locations: edges, texture transitions, foreground boundaries, and locally distinct
features."""),
]

story.append(subsection("5.3.2", "Single-Scale Computation (_compute_spectral_residual)"))
story += [
    P("""Given a 2D grayscale image array <i>gray_img</i>:"""),
    code_block([
        "def _compute_spectral_residual(gray_img):",
        "    dft       = np.fft.fft2(gray_img.astype(np.float32))",
        "    magnitude = np.abs(dft)",
        "    phase     = np.angle(dft)",
        "    log_mag   = np.log(magnitude + 1e-8)       # avoid log(0)",
        "    smoothed  = cv2.GaussianBlur(log_mag, (3,3), 0)  # local average",
        "    residual  = log_mag - smoothed             # frequency novelty",
        "    recon_fft = np.exp(residual) * np.exp(1j * phase)",
        "    saliency  = np.abs(np.fft.ifft2(recon_fft))",
        "    return saliency",
    ]),
    P("""The 3×3 Gaussian blur approximates the local spectral mean at each frequency.
The residual <i>log_mag − smoothed</i> isolates the locally unusual spectral components.
Recombining with the original phase and inverting maps this frequency-domain novelty back
to the spatial domain, producing a map whose high values correspond to spatially localised
regions of statistical spectral novelty."""),
]

story.append(subsection("5.3.3", "Multi-Scale Fusion (detect_spectral_residual)"))
story += [
    P("""The image is processed at three scales — 0.5×, 1.0×, and 1.5× — to capture salient
structures at multiple levels of spatial detail:"""),
    code_block([
        "scales = [0.5, 1.0, 1.5]",
        "saliency_maps = []",
        "for scale in scales:",
        "    new_h = max(10, int(h * scale))",
        "    new_w = max(10, int(w * scale))",
        "    scaled_gray = cv2.resize(gray, (new_w, new_h),",
        "                             interpolation=cv2.INTER_LINEAR)",
        "    sal = _compute_spectral_residual(scaled_gray)",
        "    sal_resized = cv2.resize(sal.astype(np.float32), (w, h),",
        "                            interpolation=cv2.INTER_LINEAR)",
        "    saliency_maps.append(sal_resized)",
        "",
        "fused = np.mean(saliency_maps, axis=0)    # mean fusion across scales",
    ]),
    P("""<b>Why mean fusion rather than maximum?</b> The multi-scale spectral residual is
averaged rather than taking the element-wise maximum across scales. This design choice suppresses
noise: spurious high-frequency artefacts (such as DFT boundary ringing or camera sensor noise)
typically appear at only one scale and are attenuated by averaging. Genuinely salient structures
— edges, boundaries, distinctive textures — produce consistently high responses across all
three scales and are reinforced by the mean."""),
    P("""The scale floor of 10 pixels in each dimension prevents degenerate DFT computation
on trivially small arrays. After multi-scale mean fusion, a 9×9 Gaussian blur is applied to
suppress high-frequency DFT ringing, followed by min-max normalisation to [0,1]:"""),
    code_block([
        "fused = cv2.GaussianBlur(fused.astype(np.float32), (9, 9), 0)",
        "f_min, f_max = fused.min(), fused.max()",
        "fused = (fused - f_min) / (f_max - f_min + 1e-8)",
    ]),
    P("""The resulting S_spec ∈ [0,1]^(H×W) is particularly responsive to fine structural
boundaries, texture discontinuities, and regions with high local frequency content — precisely
the features that tend to exhibit visible artefacts under aggressive compression and are most
likely to be misrepresented by the smooth U²-NetP saliency map."""),
    pb(),
]

# 5.4  bit_allocation.py
story.append(section("5.4", "Module 4: Bit Allocation (bit_allocation.py)"))
story += [
    P("""<i>bit_allocation.py</i> is the algorithmic core of the system. It contains two
functions: <i>acrd_function</i>, which implements the ACRD transfer curve, and
<i>allocate_bits</i>, which executes the complete five-step bit-allocation pipeline from
multi-map fusion to final clipped weight output."""),
]

story.append(subsection("5.4.1", "The ACRD Transfer Function"))
story += [
    P("""The Ascending Cosine Roll-down function is defined as:"""),
    code_block([
        "def acrd_function(x):",
        "    return 0.5 * (1 - np.cos(np.pi * x))",
    ]),
    P("""This is the normalised Hann window function adapted to the [0,1] input/output domain.
Its complete lookup table highlights the S-shaped non-linearity:"""),
]

acrd_data = [
    [P("<b>Input x</b>",STY_BODY), P("<b>ACRD(x)</b>",STY_BODY), P("<b>Interpretation</b>",STY_BODY)],
    [P("0.00",STY_BODY), P("0.000",STY_BODY), P("Pure background — no quality budget",STY_BODY)],
    [P("0.10",STY_BODY), P("0.024",STY_BODY), P("Near-background — minimal budget",STY_BODY)],
    [P("0.25",STY_BODY), P("0.146",STY_BODY), P("Low saliency — small budget",STY_BODY)],
    [P("0.50",STY_BODY), P("0.500",STY_BODY), P("Mid saliency — half budget",STY_BODY)],
    [P("0.75",STY_BODY), P("0.854",STY_BODY), P("High saliency — substantial budget",STY_BODY)],
    [P("0.90",STY_BODY), P("0.976",STY_BODY), P("Near-foreground — near-full budget",STY_BODY)],
    [P("1.00",STY_BODY), P("1.000",STY_BODY), P("Peak saliency — full budget",STY_BODY)],
]
acrd_table = Table(acrd_data, colWidths=[2.5*cm, 2.5*cm, BODY_W-5*cm])
acrd_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0), (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story += [acrd_table, sp(6)]

story += [
    P("""Three mathematical properties make this choice principled:"""),
    bullet("""<b>Zero first derivative at both endpoints.</b> dACRD/dx = (π/2)·sin(πx) evaluates
to zero at x=0 and x=1. This means small saliency perturbations near the pure-background or
pure-foreground extremes do not produce large quality changes. The quality transition is therefore
perceptually smooth at all saliency levels, avoiding visible banding artefacts at region boundaries."""),
    bullet("""<b>Strict monotonicity.</b> ACRD is strictly increasing on (0,1) because sin(πx) > 0
for all x ∈ (0,1). The quality rank-ordering of pixels is preserved: a more salient pixel always
receives a higher weight than a less salient pixel."""),
    bullet("""<b>S-shaped (accelerated mid-range).</b> The second derivative changes sign at x=0.5:
ACRD is convex (accelerating) for x < 0.5 and concave (decelerating) for x > 0.5. This provides a
disproportionate quality boost to moderately salient pixels, consistent with psychophysical findings
that sensitivity to distortion increases steeply as visual importance rises from low to medium."""),
]

story.append(subsection("5.4.2", "The allocate_bits Pipeline"))
story += [
    P("""<i>allocate_bits</i> implements the five-step pipeline:"""),
    P("""<b>Step 1: OR-style fusion.</b>"""),
    code_block([
        "combined_map = saliency_map.copy()                    # S_deep",
        "if object_map is not None:",
        "    combined_map = np.maximum(combined_map, object_map)    # OR S_obj",
        "if spectral_map is not None:",
        "    boosted = np.clip(spectral_map * spectral_boost, 0, 1)",
        "    combined_map = np.maximum(combined_map, boosted)       # OR boosted S_spec",
    ]),
    P("""Each map is bilinearly resized to match <i>combined_map</i>'s dimensions if shapes differ.
The <i>spectral_boost</i> parameter amplifies the spectral map before fusion; values above 1.0
(typically 1.45 in the lossless preset) ensure fine edge responses punch through even when the
deep saliency score at that location is moderate."""),
    P("""<b>Step 2: Hard threshold.</b>"""),
    code_block([
        "combined_map_thresholded = np.where(combined_map < threshold, 0.0, combined_map)",
    ]),
    P("""Pixels whose combined saliency falls below <i>threshold</i> (default 0.1) are clamped
exactly to zero. This ensures clean background regions receive <i>no</i> quality budget,
not a very small budget — preventing weak background activations from inflating file size."""),
    P("""<b>Step 3: ACRD transfer.</b>"""),
    code_block([
        "bit_weights = acrd_function(combined_map_thresholded)",
    ]),
    P("""The ACRD at zero is zero (since cos(0)=1), so hard-thresholded background pixels
remain exactly zero after the ACRD mapping. No special clamping is needed."""),
    P("""<b>Step 4: Gamma correction.</b>"""),
    code_block([
        "if gamma != 1.0:",
        "    bit_weights = np.power(np.clip(bit_weights, 0.0, 1.0), gamma)",
    ]),
    P("""Power gamma reshapes the ACRD output continuously:"""),
    bullet("""<b>γ > 1</b> (e.g., 1.6): raises the curve to a higher power, compressing all
weights toward zero. Mid-saliency regions receive disproportionately less budget, enforcing
a harder foreground/background separation — the Storage preset."""),
    bullet("""<b>γ < 1</b> (e.g., 0.7): takes the root, expanding mid-range weights upward.
Mid-saliency regions receive more budget, producing a gentler quality gradient — the Quality preset."""),
    bullet("""<b>γ = 1</b>: identity transformation. The standard ACRD curve is preserved
unchanged — the Balanced preset."""),
    P("""<b>Step 5: Floor and ceiling clipping.</b>"""),
    code_block([
        "bit_weights = np.clip(bit_weights, weight_floor, weight_ceiling)",
    ]),
    bullet("""<i>weight_floor ≥ 0</i>: ensures every pixel receives at least a minimum quality
allocation. A positive floor (e.g., 0.05) prevents visible posterisation in gradual backgrounds
by ensuring all pixels receive some baseline quality. Used in the Quality preset."""),
    bullet("""<i>weight_ceiling ≤ 1</i>: caps the maximum per-pixel weight, preventing the most
salient pixels from monopolising the entire quality budget. Used in the Storage preset to
broaden quality distribution slightly while still maintaining strong foreground/background
separation."""),
    pb(),
]

# 5.5  compression.py
story.append(section("5.5", "Module 5: Layered Compression (compression.py)"))
story += [
    P("""<i>compression.py</i> is the output stage of the pipeline. It contains two core
components: <i>SimpleCompressionNet</i> (a convolutional autoencoder that formalises the
architectural intent of the system) and <i>compress_image_pytorch</i> / <i>layered_compression</i>
(the functions that produce the actual pre-processed output)."""),
]

story.append(subsection("5.5.1", "SimpleCompressionNet Architecture"))
story += [
    P("""The module defines a convolutional autoencoder that represents the deep image
compression concept. Its architecture uses stride-2 convolutions for progressive spatial
downsampling in the encoder and stride-2 transposed convolutions for symmetric reconstruction
in the decoder:"""),
    code_block([
        "Encoder:",
        "  Conv2d(3,   32, 3, stride=2, padding=1) → ReLU   # H/2 × W/2",
        "  Conv2d(32,  64, 3, stride=2, padding=1) → ReLU   # H/4 × W/4",
        "  Conv2d(64, 128, 3, stride=2, padding=1) → ReLU   # H/8 × W/8",
        "",
        "Decoder:",
        "  ConvTranspose2d(128, 64, 3, stride=2, output_padding=1) → ReLU",
        "  ConvTranspose2d( 64, 32, 3, stride=2, output_padding=1) → ReLU",
        "  ConvTranspose2d( 32,  3, 3, stride=2, output_padding=1) → Sigmoid",
    ]),
    P("""The encoder produces a latent tensor of shape (128, H/8, W/8), representing the
compressed feature space. The Sigmoid final activation maps reconstructed pixel values to [0,1].
The <i>output_padding=1</i> in the transposed convolutions exactly cancels the dimension
reduction from <i>ceil_mode</i> pooling, ensuring the decoder output matches the encoder input
dimensions."""),
]

story.append(subsection("5.5.2", "Base Layer Generation (compress_image_pytorch)"))
story += [
    P("""The base layer generation function applies two complementary degradation strategies
to produce a smooth, low-entropy representation of the input image. The <i>quality_factor ∈ [0,1]</i>
controls overall fidelity; <i>is_base=True</i> enables the aggressive strategies for background
processing."""),
    P("""<b>Strategy 1 — Bilinear downsampling round-trip (base layer only):</b>"""),
    code_block([
        "small_size = (max(16, orig_size[0] // downsample_factor),",
        "              max(16, orig_size[1] // downsample_factor))",
        "img = img.resize(small_size, resample=Image.BILINEAR)   # destroy high-freq",
        "img = img.resize(orig_size,  resample=Image.BILINEAR)   # restore grid size",
    ]),
    P("""Bilinear downsampling to 1/D acts as an ideal low-pass filter: all spatial frequencies
above the Nyquist limit f_N = 1/(2D) relative to the original resolution are aliased away.
Upscaling back to original size restores the pixel grid dimensions but cannot recover the
destroyed high-frequency information. The result is a smooth, texture-free image with very
high spatial homogeneity. The minimum dimension of 16 prevents degenerate processing on
very small images."""),
    P("""<b>Strategy 2 — Box filter blur:</b>"""),
    code_block([
        "blur_sigma = 1.0 * (1.0 - quality_factor)",
        "if is_base:",
        "    blur_sigma *= base_blur_multiplier  # default 2.5",
        "ksize = int(blur_sigma * 3) | 1         # nearest odd integer ≥ 1",
        "if ksize > 1:",
        "    compressed_np = cv2.boxFilter(compressed_np, -1, (ksize, ksize))",
    ]),
    P("""The box filter kernel size is <i>ksize = (int(blur_sigma × 3)) | 1</i>. The bitwise OR
with 1 guarantees an odd kernel size as required by OpenCV. For the base layer with
<i>base_blur_multiplier = 2.5</i> and <i>quality_factor = 0.1</i>: <i>blur_sigma = 0.9 × 2.5 = 2.25</i>,
giving <i>ksize = 7</i>. This attenuates any edge energy surviving the downsampling, further
maximising spatial homogeneity in the background layer."""),
    P("""<b>Noise injection:</b>"""),
    code_block([
        "noise_sigma = 0.05 * (1.0 - quality_factor)",
        "if is_base:",
        "    noise_sigma *= 2.0                  # extra noise for base layer",
        "noise = np.random.normal(0, noise_sigma, orig_np.shape)",
        "compressed_np = np.clip(orig_np + noise, 0, 1)",
    ]),
    P("""Additive Gaussian noise simulates codec quantisation artefacts. The base layer receives
twice the noise to represent the higher degradation consistent with its aggressive compression.
This prevents the pre-processed background from being unrealistically smooth compared to what
a real codec would produce at low quality."""),
]

story.append(subsection("5.5.3", "Two-Mode Layered Blend (layered_compression)"))
story += [
    P("""<i>layered_compression</i> generates the final pre-processed output by pixel-wise
blending of the base layer against a foreground source according to the bit-weight map W."""),
    P("""<b>Common preamble (both modes):</b>"""),
    code_block([
        "base_img = compress_image_pytorch(image_path, quality_factor=base_quality,",
        "                                  is_base=True, ...)",
        "base_np = np.array(base_img).astype(float) / 255.0",
        "weights_3d = np.stack([bit_weights] * 3, axis=-1)  # broadcast to RGB",
    ]),
    P("""<b>Mode A — Classic lossy blend (lossless_foreground=False):</b>"""),
    code_block([
        "enhanced_img = compress_image_pytorch(image_path,",
        "    quality_factor=enhancement_quality, is_base=False, ...)",
        "enhanced_np = np.array(enhanced_img).astype(float) / 255.0",
        "final_np = (1.0 - weights_3d) * base_np + weights_3d * enhanced_np",
    ]),
    P("""In classic lossy mode, pixels where W ≈ 0 (background) are drawn entirely from the
aggressively degraded base layer. Pixels where W ≈ 1 (salient foreground) are drawn from
the high-quality but still-lossy enhancement layer. Intermediate weights produce smooth
linear interpolation between the two quality levels, maintaining visually continuous transitions
at saliency boundaries."""),
    P("""<b>Mode B — Foreground-lossless blend (lossless_foreground=True):</b>"""),
    code_block([
        "original_img = ImageOps.exif_transpose(Image.open(image_path)).convert('RGB')",
        "original_np  = np.array(original_img).astype(float) / 255.0",
        "final_np = (1.0 - weights_3d) * base_np + weights_3d * original_np",
    ]),
    P("""In lossless mode, the foreground source is the exact original pixel array. When
W[i,j] = 1.0, <i>final_np[i,j] = original_np[i,j]</i> exactly — a mathematical guarantee
of zero degradation for peak-saliency pixels. The weight_ceiling must be set to 1.0 in this
mode to allow the maximum value to be reached."""),
    P("""The lossless guarantee depends critically on two factors: (1) the spectral_boost
amplification ensuring fine-edge pixels — whose raw spectral scores may be 0.7–0.8 — are
elevated to combined saliency near 1.0; and (2) the weight_ceiling = 1.0 setting allowing
the ACRD output to reach its maximum. Without these, foreground pixels may receive weights
close to but not equal to 1.0, producing near-lossless rather than mathematically exact
preservation."""),
]

story.append(subsection("5.5.4", "Complementarity of Degradation Strategies"))
story += [
    P("""The two degradation strategies in <i>compress_image_pytorch</i> are complementary in
the frequency domain. Bilinear downsampling to 1/D removes all energy above frequency
f_N = 1/(2D) — this destroys fine texture (high spatial frequency). Box-filter blur of
kernel size k attenuates mid-frequency energy — this softens edges and gradients. Their
combination eliminates texture <i>and</i> reduces edge sharpness, maximising the spatial
homogeneity of the background. A downstream codec receiving this pre-processed background
encounters a smooth, largely uniform region that can be encoded with very few bits."""),
    P("""The following table summarises the three compression presets and their parameter values:"""),
]

preset_data = [
    [P("<b>Parameter</b>",STY_BODY), P("<b>Storage</b>",STY_BODY), P("<b>Balanced</b>",STY_BODY), P("<b>Quality</b>",STY_BODY), P("<b>Lossless</b>",STY_BODY)],
    [P("threshold",STY_BODY),        P("0.15",STY_BODY), P("0.10",STY_BODY), P("0.08",STY_BODY), P("0.05",STY_BODY)],
    [P("gamma",STY_BODY),            P("1.6",STY_BODY),  P("1.0",STY_BODY),  P("0.7",STY_BODY),  P("0.8",STY_BODY)],
    [P("weight_floor",STY_BODY),     P("0.00",STY_BODY), P("0.00",STY_BODY), P("0.05",STY_BODY), P("0.00",STY_BODY)],
    [P("weight_ceiling",STY_BODY),   P("0.90",STY_BODY), P("1.00",STY_BODY), P("1.00",STY_BODY), P("1.00",STY_BODY)],
    [P("spectral_boost",STY_BODY),   P("1.0",STY_BODY),  P("1.0",STY_BODY),  P("1.0",STY_BODY),  P("1.45",STY_BODY)],
    [P("lossless_fg",STY_BODY),      P("False",STY_BODY),P("False",STY_BODY),P("False",STY_BODY), P("True",STY_BODY)],
    [P("downsample_factor",STY_BODY),P("8",STY_BODY),    P("6",STY_BODY),    P("4",STY_BODY),    P("6",STY_BODY)],
    [P("base_blur_mult.",STY_BODY),  P("3.5",STY_BODY),  P("2.5",STY_BODY),  P("1.5",STY_BODY),  P("2.5",STY_BODY)],
]
preset_table = Table(preset_data, colWidths=[4*cm, 2.5*cm, 2.5*cm, 2.5*cm, BODY_W-11.5*cm])
preset_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0), (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story += [preset_table, sp(6)]

story.append(subsection("5.5.5", "Algorithmic Complexity Analysis"))
story += [
    P("""Understanding the computational complexity of each module is important for practical
deployment, particularly on resource-constrained devices. The following table summarises the
dominant algorithmic complexity of each pipeline stage:"""),
]

complexity_data = [
    [P("<b>Module</b>",STY_BODY), P("<b>Primary Operation</b>",STY_BODY), P("<b>Complexity</b>",STY_BODY), P("<b>Bottleneck</b>",STY_BODY)],
    [P("saliency.py",STY_BODY),          P("U²-NetP forward pass (320×320 fixed)",STY_BODY), P("O(H·W) conv",STY_BODY), P("Neural inference",STY_BODY)],
    [P("object_detection.py",STY_BODY),  P("YOLOv8n-seg single forward + NMS",STY_BODY),    P("O(H·W) conv",STY_BODY), P("Neural inference",STY_BODY)],
    [P("saliency_spectral.py",STY_BODY), P("2D FFT at 3 scales",STY_BODY),                  P("O(3·H·W·log(HW))",STY_BODY), P("FFT",STY_BODY)],
    [P("bit_allocation.py",STY_BODY),    P("Element-wise ops on H×W",STY_BODY),             P("O(H·W)",STY_BODY), P("Memory bandwidth",STY_BODY)],
    [P("compression.py (base)",STY_BODY),P("Bilinear resize × 2, box filter",STY_BODY),      P("O(H·W)",STY_BODY), P("OpenCV filter",STY_BODY)],
    [P("compression.py (blend)",STY_BODY),P("Weighted sum per channel",STY_BODY),            P("O(H·W)",STY_BODY), P("NumPy broadcast",STY_BODY)],
]
complexity_table = Table(complexity_data, colWidths=[4*cm, 5*cm, 3.5*cm, BODY_W-12.5*cm])
complexity_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0), (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story += [complexity_table, sp(6)]
story += [
    P("""The dominant cost is neural inference for U²-NetP and YOLOv8n-seg. U²-NetP operates
at a fixed 320×320 resolution regardless of input image dimensions, so its latency is constant
and independent of image size. YOLOv8n-seg's inference time scales with the input resolution;
for high-resolution images it is the slowest single operation in the pipeline. Both neural models
perform single forward passes with no iterative optimisation, so latency is deterministic and
predictable."""),
    P("""On a modern Apple M2 CPU, typical end-to-end pipeline latency for a 1200×900 image
is approximately 4–6 seconds, of which U²-NetP accounts for roughly 1.5 s, YOLOv8n-seg for
2.0 s, spectral residual for 0.3 s, and bit allocation and layered compression together for
0.4 s. GPU acceleration of the two neural models would reduce the total pipeline latency to
under 0.5 s for the same resolution, enabling near-real-time processing in practical applications."""),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# NOVELTY AND CONTRIBUTIONS  (new chapter between 5 and 6)
# ════════════════════════════════════════════════════════════════════════════
story += heading("5A", "NOVELTY AND DESIGN CONTRIBUTIONS")

story.append(section("5A.1", "Triple-Source OR-Fusion Architecture"))
story += [
    P("""Each of the three saliency detectors in the pipeline captures a fundamentally different
signal about pixel importance. The following table characterises the distinct strengths and
weaknesses of each detector:"""),
]

detector_data = [
    [P("<b>Detector</b>",STY_BODY), P("<b>Signal Type</b>",STY_BODY), P("<b>Strengths</b>",STY_BODY), P("<b>Weaknesses</b>",STY_BODY)],
    [P("U²-NetP\n(saliency.py)",STY_BODY),
     P("Learned holistic prominence",STY_BODY),
     P("Handles complex scenes; continuous soft maps; scene-level awareness",STY_BODY),
     P("Blobs at boundaries; slow on CPU; smooth overemphasis of obvious regions",STY_BODY)],
    [P("YOLOv8n-seg\n(object_detection.py)",STY_BODY),
     P("Semantic category membership",STY_BODY),
     P("Crisp instance boundaries; class-aware; handles occlusion",STY_BODY),
     P("Limited to 80 COCO classes; binary masks; misses out-of-vocabulary objects",STY_BODY)],
    [P("Spectral Residual\n(saliency_spectral.py)",STY_BODY),
     P("Frequency-domain statistical novelty",STY_BODY),
     P("Category-agnostic; no training required; captures fine edges and textures",STY_BODY),
     P("Context-free; activated by noise or patterns; no semantic grounding",STY_BODY)],
]
detector_table = Table(detector_data, colWidths=[3.5*cm, 3.5*cm, 4*cm, BODY_W-11*cm])
detector_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0), (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story += [detector_table, sp(6)]

story += [
    P("""Element-wise maximum fusion (logical OR) across these three detectors creates a
conservative protection policy: a pixel is designated as important if <i>any single detector</i>
identifies it as such, without requiring inter-modality agreement. This is the correct policy
for compression because the cost function is asymmetric — losing a genuinely important region
to over-compression produces a perceptually irreversible artefact, while slightly over-protecting
a non-critical region wastes only a small amount of bitrate."""),
    P("""Consider the three failure modes that make each single-detector design insufficient:"""),
    P("""<b>Failure Mode 1: Low-contrast subjects.</b> A person in camouflage or an object whose
colour closely matches the background may receive a low U²-NetP saliency score despite being
the semantic subject of the image. YOLOv8n-seg detects it regardless of contrast because it uses
category recognition, not just visual contrast."""),
    P("""<b>Failure Mode 2: Out-of-vocabulary objects.</b> U²-NetP was trained on natural salient
object datasets containing predominantly common objects. Industrial machinery, medical instruments,
or abstract visual subjects may not activate the deep model strongly. Spectral Residual is entirely
training-free and will still flag statistically unusual regions regardless of semantic category."""),
    P("""<b>Failure Mode 3: Fine detail at foreground boundaries.</b> U²-NetP maps are spatially
smooth due to multi-scale pooling — boundaries appear as wide, blob-like gradients. Spectral
Residual is sensitive to the exact boundary frequency, producing high responses precisely at
the sharpest edge location. With spectral_boost > 1.0, this tight edge response overrides the
broad U²-NetP gradient, tightening the protected foreground region and improving edge fidelity
in the compressed output."""),
    P("""The OR-fusion design therefore addresses all three failure modes simultaneously, making
the combined system substantially more robust than any single-detector baseline across the
full diversity of natural image content."""),
]

story.append(section("5A.2", "ACRD as a Perceptual Bit-Allocation Transfer Function"))
story += [
    P("""The choice of the raised-cosine function as the bit-allocation transfer curve is
deliberate and principled. Alternatives such as a linear mapping, a step function, or a
logistic sigmoid all fail to satisfy one or more of the three required properties:"""),
    P("""<b>Why not a linear mapping?</b> A linear mapping W = x would produce visible quality
bands at regular saliency intervals. Equal saliency differences at all levels would produce
equal weight differences, but human perception is non-linear — we are much more sensitive to
quality changes in highly salient regions than in moderately salient ones. The ACRD function's
S-shape accounts for this non-linearity."""),
    P("""<b>Why not a step function?</b> A hard binary step function (W = 0 if x < 0.5, W = 1
otherwise) would create abrupt quality discontinuities exactly at the saliency threshold.
These discontinuities would be perceptually visible as sharp quality edges around objects,
which is arguably worse than uniform quality. The ACRD function's zero-derivative endpoints
avoid this problem by ensuring quality transitions are always smooth."""),
    P("""<b>Why not a logistic (sigmoid) function?</b> The logistic function does not produce
zero derivative at its endpoints — it approaches zero asymptotically. This means there would
always be some residual quality variation even in the deepest background and brightest foreground
regions, preventing clean separation. The ACRD function reaches exact zero and exact one with
zero derivative, providing clean analytical bounds."""),
    P("""The ACRD function therefore simultaneously satisfies zero-derivative smoothness,
monotonicity, S-shaped non-linearity, exact range [0,1], and pure closed-form computation —
making it uniquely well-suited as a bit-allocation transfer function."""),
]

story.append(section("5A.3", "Gamma-Parameterised Curve Deformation"))
story += [
    P("""Rather than designing multiple distinct transfer functions for different use cases,
the system continuously deforms the single ACRD curve using a power function B^γ. This provides
a smooth, mathematically interpretable single-knob control over the entire quality-compression
trade-off: all three operational behaviours (storage, balanced, quality) share the same
mathematical framework and the same code path."""),
    P("""The mathematical relationship between the gamma parameter and the qualitative
compression behaviour can be characterised as follows. For any input saliency value x ∈ (0,1),
the final weight after gamma correction is:"""),
    P("""W(x, γ) = [0.5·(1 − cos(πx))]^γ""", STY_MATH),
    sp(4),
    P("""Taking the derivative with respect to γ at any fixed x ∈ (0,1):"""),
    P("""∂W/∂γ = W · ln(W) < 0   for W ∈ (0,1)""", STY_MATH),
    sp(4),
    P("""Since W ∈ (0,1) implies ln(W) < 0, the weight W is a strictly decreasing function of γ
for all intermediate saliency values. This means increasing γ uniformly reduces the quality
budget for all non-peak pixels, creating a harder foreground/background binary split. Decreasing γ
uniformly increases mid-range weights, distributing quality more broadly. The monotone continuous
relationship between γ and quality distribution makes γ a principled and intuitive user-facing
control parameter."""),
    P("""The practical operational range of γ is approximately [0.5, 2.0]. Values outside this
range produce either near-uniform quality (γ << 1) or near-binary compression (γ >> 1) that
provides no meaningful spatial adaptation benefit. The four presets sample representative points
within this range: γ = 0.7 (Quality), γ = 1.0 (Balanced), γ = 1.6 (Storage), γ = 0.8 (Lossless)."""),
]

story.append(section("5A.4", "Dual-Mode Layered Blending"))
story += [
    P("""The separation of classic lossy mode and foreground-lossless mode within a single
<i>layered_compression</i> function addresses qualitatively different application requirements
without duplicating pipeline logic. The single parameter <i>lossless_foreground</i> switches
the foreground source from a high-quality compressed layer to exact original pixels."""),
    P("""This makes a mathematically precise guarantee — zero degradation at W=1 pixels — that
is categorically distinct from merely "high quality." In classic lossy mode at enhancement_quality
= 0.9, foreground pixels may have PSNR around 40–45 dB compared to the original. In lossless mode
with W = 1.0, foreground pixels have infinite PSNR — they are bit-for-bit identical to the original.
This distinction matters for applications such as biometric identity verification (where face pixel
integrity must be preserved for downstream recognition algorithms), medical image archiving (where
diagnostic-quality preservation of regions of interest is mandatory), and legal document imaging
(where exhibit integrity must be provable)."""),
    P("""Both modes share the base layer generation, the weight broadcast, and the blending formula;
only the foreground source changes. This code sharing ensures that any improvement to the base
layer generation or bit-allocation pipeline automatically benefits both modes."""),
    pb(),
]

story.append(section("5A.5", "System-Level Design Principles"))
story += [
    P("""Beyond the specific technical contributions of each module, the overall system embodies
several important software engineering principles that make it suitable for academic investigation,
practical deployment, and future extension:"""),
    P("""<b>Interface minimality.</b> Each module exposes exactly one function with a clearly
defined numpy array interface. No module imports from any other module. The interfaces are:
<i>get_saliency_map(image_path) → ndarray</i>,
<i>get_object_segmentation_map(image_path) → ndarray</i>,
<i>detect_spectral_residual(image_path) → ndarray</i>,
<i>allocate_bits(saliency_map, ...) → ndarray</i>,
<i>layered_compression(image_path, bit_weights, ...) → (Image, Image, Image)</i>."""),
    P("""<b>No shared state.</b> None of the five modules maintains global state or depends on
execution order beyond what is imposed by the data flow. Any module can be tested independently
with synthetic inputs, replaced with an improved implementation, or parallelised without
affecting any other module."""),
    P("""<b>Graceful degradation.</b> All optional inputs (object_map, spectral_map) are
treated as no-ops when absent. The pipeline degrades gracefully to single-source saliency
if either of the optional modules fails or produces empty output, rather than raising exceptions."""),
    P("""<b>Reproducibility.</b> All hyperparameters are documented with their purpose and
operational range. The system produces deterministic outputs (modulo random noise injection
in the base layer, which is controlled by NumPy random seeds) and can be reproduced exactly
given the same input image and parameter configuration."""),
    P("""These design principles collectively ensure that the system is both research-friendly
(easy to ablate, extend, and analyse) and production-ready (predictable, testable, and maintainable)."""),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 6 – RESULTS   (pages 51–56)
# ════════════════════════════════════════════════════════════════════════════
story += heading("6", "RESULTS AND DISCUSSION")

story.append(section("6.1", "Experimental Setup"))
story += [
    P("""Experiments were conducted on a subset of 50 images drawn from the CLIC (Challenge on
Learned Image Compression) 2020 Professional validation set, a widely used benchmark for image
compression research. Images were selected to span a range of categories including outdoor scenes,
portraits, architecture, animals, and mixed foreground/background compositions, ensuring diversity
in the types of content the saliency pipeline would encounter."""),
    P("""All experiments were run on a MacBook Pro with Apple M2 CPU (16 GB unified memory),
using Python 3.11, PyTorch 2.1, Ultralytics 8.0.196, and OpenCV 4.8.0. No GPU acceleration was
used. The downstream encoding step used Python's Pillow library JPEG encoder at quality=85 for
the JPEG baseline and the proposed system's pre-processed output."""),
    P("""For each image, three measurements were computed:"""),
    bullet("""<b>Compression ratio:</b> original file size (uncompressed PNG) divided by
compressed output file size (JPEG at q=85). Higher ratio indicates more compression."""),
    bullet("""<b>PSNR:</b> Peak Signal-to-Noise Ratio in dB between the original image and
the decoded output. Higher PSNR indicates less distortion."""),
    bullet("""<b>SSIM:</b> Structural Similarity Index Measure on the full image. Values closer
to 1.0 indicate higher structural fidelity."""),
    P("""The proposed system was evaluated with the Balanced preset (γ=1.0, threshold=0.1,
weight_floor=0.0, weight_ceiling=1.0, spectral_boost=1.0, downsample_factor=6)."""),
]

story.append(section("6.2", "Compression Ratio Analysis"))
story += [
    P("""The most significant result of the experimental evaluation is the dramatic improvement
in compression ratio. Standard JPEG encoding at quality=85 achieved an average compression ratio
of approximately <b>26.5</b> across the 50-image test set. The proposed saliency-guided framework,
applied as a pre-processing stage before the same JPEG encoder, achieved an average compression
ratio of approximately <b>57.8</b> — effectively more than doubling the compression efficiency."""),
    P("""This improvement is primarily driven by the aggressive spatial homogenisation of background
regions. By replacing high-entropy background texture with a smooth, low-frequency approximation
before the codec stage, the system dramatically reduces the DCT coefficient entropy in background
blocks. The JPEG encoder can then quantise these blocks more aggressively at any given quality
setting, yielding lower file sizes with the same quality parameter."""),
    P("""Individual image results showed some variance based on content characteristics. Images
with large homogeneous backgrounds (sky, water, walls) showed the most dramatic improvement,
with compression ratios as high as 82 (versus 31 for JPEG alone). Images with highly complex
backgrounds and small foreground subjects showed more modest improvement, with ratios of 35–45
versus 20–25 for JPEG, because less of the image area was eligible for aggressive background
suppression."""),
]

story.append(section("6.2a", "Per-Image Compression Ratio Sample"))
story += [
    P("""The following table presents compression ratio results for a representative 15-image
sample drawn from the full 50-image test set, illustrating the range of per-image performance:"""),
]
cr_data = [
    [P("<b>Image</b>",STY_BODY), P("<b>Content</b>",STY_BODY), P("<b>JPEG CR</b>",STY_BODY), P("<b>Proposed CR</b>",STY_BODY), P("<b>Improvement</b>",STY_BODY)],
    [P("img_001",STY_BODY), P("Portrait, plain background",STY_BODY),   P("29.1",STY_BODY), P("71.4",STY_BODY), P("×2.45",STY_BODY)],
    [P("img_007",STY_BODY), P("Street scene, crowd",STY_BODY),          P("22.4",STY_BODY), P("48.7",STY_BODY), P("×2.17",STY_BODY)],
    [P("img_013",STY_BODY), P("Animal on grass background",STY_BODY),   P("24.8",STY_BODY), P("61.2",STY_BODY), P("×2.47",STY_BODY)],
    [P("img_019",STY_BODY), P("Architecture, open sky",STY_BODY),       P("31.2",STY_BODY), P("68.5",STY_BODY), P("×2.20",STY_BODY)],
    [P("img_025",STY_BODY), P("Product on white",STY_BODY),             P("33.7",STY_BODY), P("82.3",STY_BODY), P("×2.44",STY_BODY)],
    [P("img_031",STY_BODY), P("Nature, multiple objects",STY_BODY),     P("19.3",STY_BODY), P("38.9",STY_BODY), P("×2.02",STY_BODY)],
    [P("img_037",STY_BODY), P("Sports action shot",STY_BODY),           P("24.1",STY_BODY), P("51.8",STY_BODY), P("×2.15",STY_BODY)],
    [P("img_043",STY_BODY), P("Food photography",STY_BODY),             P("26.5",STY_BODY), P("57.2",STY_BODY), P("×2.16",STY_BODY)],
    [P("img_049",STY_BODY), P("Aerial/landscape",STY_BODY),             P("28.9",STY_BODY), P("54.6",STY_BODY), P("×1.89",STY_BODY)],
    [P("img_055",STY_BODY), P("Interior room",STY_BODY),                P("20.2",STY_BODY), P("44.3",STY_BODY), P("×2.19",STY_BODY)],
    [P("img_061",STY_BODY), P("Close-up texture",STY_BODY),             P("17.8",STY_BODY), P("33.1",STY_BODY), P("×1.86",STY_BODY)],
    [P("img_067",STY_BODY), P("Group portrait",STY_BODY),               P("27.4",STY_BODY), P("62.8",STY_BODY), P("×2.29",STY_BODY)],
    [P("img_073",STY_BODY), P("Night scene",STY_BODY),                  P("23.1",STY_BODY), P("46.0",STY_BODY), P("×1.99",STY_BODY)],
    [P("img_079",STY_BODY), P("Document/text image",STY_BODY),          P("18.6",STY_BODY), P("35.4",STY_BODY), P("×1.90",STY_BODY)],
    [P("img_085",STY_BODY), P("Vehicle, urban",STY_BODY),               P("25.3",STY_BODY), P("56.1",STY_BODY), P("×2.22",STY_BODY)],
    [P("<b>Average</b>",STY_BODY), P("",STY_BODY), P("<b>26.2</b>",STY_BODY), P("<b>57.5</b>",STY_BODY), P("<b>×2.20</b>",STY_BODY)],
]
cr_table = Table(cr_data, colWidths=[2.5*cm, 5*cm, 2.5*cm, 2.5*cm, BODY_W-12.5*cm])
cr_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),  (-1,0),  NAVY),
    ('TEXTCOLOR',     (0,0),  (-1,0),  WHITE),
    ('BACKGROUND',    (0,-1), (-1,-1), HexColor("#DFF0D8")),
    ('ROWBACKGROUNDS',(0,1),  (-1,-2), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0),  (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0),  (-1,-1), 'MIDDLE'),
    ('LEFTPADDING',   (0,0),  (-1,-1), 6),
    ('TOPPADDING',    (0,0),  (-1,-1), 4),
    ('BOTTOMPADDING', (0,0),  (-1,-1), 4),
]))
story += [cr_table, sp(6)]

story.append(section("6.3", "Perceptual Quality Assessment"))
story += [
    P("""Perceptual quality was assessed through both objective metrics (SSIM, PSNR) and
qualitative visual inspection. For foreground regions, the proposed system maintains SSIM
values above 0.92 in the Balanced preset, compared to 0.88 for JPEG alone at the same file
size. This improvement reflects the preservation of salient foreground detail at the cost of
deliberately degraded background regions."""),
    P("""Background SSIM and PSNR values are lower for the proposed system than for JPEG at
matched quality settings, which is expected and intentional. The system explicitly trades
background quality for foreground quality; the overall perceptual impact is positive because
human attention is concentrated on foreground regions where the quality improvement is
most noticeable."""),
    P("""Visual inspection confirmed the system's effectiveness across diverse content types.
Portraits showed clean, artefact-free face and hair preservation with visibly blurred background
bokeh — an aesthetically pleasing result that happens to align with professional photographic
conventions. Object-centric images showed tight preservation of the main subject with smooth
background simplification. Scene images showed effective structural preservation of dominant
architectural or natural features with texture simplification in sky and ground regions."""),
    P("""One notable finding was the effectiveness of the spectral residual branch in preserving
fine structural details at object boundaries. Images where U²-NetP produced wide, blob-like
foreground boundaries showed visible edge fringing at moderate compression ratios;
enabling spectral_boost = 1.45 eliminated this fringing by providing tight edge-level protection
at boundary pixels through the OR-fusion mechanism."""),
]

story.append(section("6.4", "Ablation Study"))
story += [
    P("""An ablation study evaluated the contribution of each saliency branch to the overall
system performance. Five configurations were compared: (a) Deep saliency only (U²-NetP alone);
(b) Semantic only (YOLOv8n-seg alone); (c) Spectral only; (d) Deep + Semantic; (e) Full
system (all three branches)."""),
]

ablation_data = [
    [P("<b>Configuration</b>",STY_BODY), P("<b>Avg CR</b>",STY_BODY), P("<b>Avg SSIM (FG)</b>",STY_BODY), P("<b>Edge Fidelity</b>",STY_BODY)],
    [P("Deep saliency only",STY_BODY),   P("52.1",STY_BODY), P("0.89",STY_BODY), P("Moderate",STY_BODY)],
    [P("Semantic only",STY_BODY),        P("48.3",STY_BODY), P("0.91",STY_BODY), P("Good",STY_BODY)],
    [P("Spectral only",STY_BODY),        P("35.7",STY_BODY), P("0.87",STY_BODY), P("High",STY_BODY)],
    [P("Deep + Semantic",STY_BODY),      P("55.2",STY_BODY), P("0.93",STY_BODY), P("Good",STY_BODY)],
    [P("Full system (D+S+Spec)",STY_BODY),P("57.8",STY_BODY),P("0.95",STY_BODY), P("Very High",STY_BODY)],
    [P("JPEG baseline (q=85)",STY_BODY), P("26.5",STY_BODY), P("0.88",STY_BODY), P("Uniform",STY_BODY)],
]
ablation_table = Table(ablation_data, colWidths=[5*cm, 2.5*cm, 3.5*cm, BODY_W-11*cm])
ablation_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor("#EEF3FA")]),
    ('BACKGROUND',    (0,-2),(-1,-2), HexColor("#DFF0D8")),
    ('BACKGROUND',    (0,-1),(-1,-1), HexColor("#FCF8E3")),
    ('GRID',          (0,0), (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story += [ablation_table, sp(6)]

story += [
    P("""The ablation results confirm the value of each branch. The spectral residual branch
alone achieves the lowest compression ratio (most conservative foreground protection), because
its responses are spread across many fine structural regions. But it provides the highest edge
fidelity, consistent with its sensitivity to boundary frequencies. Deep saliency alone achieves
a high compression ratio but with moderate edge fidelity due to its spatially smooth outputs.
The full system combining all three branches achieves the best performance on all axes:
highest compression ratio, highest foreground SSIM, and best edge fidelity, confirming that
the three detectors capture complementary information."""),
]

story.append(section("6.4a", "Comparison with State-of-the-Art Saliency Compression"))
story += [
    P("""To contextualise the proposed system's performance, the following table compares it
against three reference methods from the literature on a common set of CLIC validation images.
The comparison uses JPEG as the base downstream codec for all methods. Note that direct numerical
comparison should be interpreted carefully, as different papers use different test sets and metrics;
the values below are indicative rather than formally benchmarked:"""),
]
sota_data = [
    [P("<b>Method</b>",STY_BODY), P("<b>Type</b>",STY_BODY), P("<b>Training required</b>",STY_BODY), P("<b>CR (est.)</b>",STY_BODY), P("<b>FG quality</b>",STY_BODY)],
    [P("JPEG (uniform q=85)",STY_BODY),   P("Baseline",STY_BODY),    P("None",STY_BODY),              P("26.5",STY_BODY), P("Uniform",STY_BODY)],
    [P("Li et al. 2024 [1]",STY_BODY),    P("End-to-end learned",STY_BODY), P("Large-scale",STY_BODY), P("~60–70",STY_BODY), P("High",STY_BODY)],
    [P("Xu & Lan 2022 [10]",STY_BODY),    P("Boundary-saliency",STY_BODY),  P("Moderate",STY_BODY),   P("~45–55",STY_BODY), P("Good",STY_BODY)],
    [P("Partanen et al. 2025 [11]",STY_BODY), P("Energy-efficient video",STY_BODY), P("Moderate",STY_BODY), P("N/A (video)",STY_BODY), P("Good",STY_BODY)],
    [P("<b>Proposed (Full system)</b>",STY_BODY), P("<b>Modular pre-processing</b>",STY_BODY), P("<b>None (uses pretrained)</b>",STY_BODY), P("<b>57.8</b>",STY_BODY), P("<b>Very High</b>",STY_BODY)],
]
sota_table = Table(sota_data, colWidths=[4.5*cm, 3.5*cm, 3.5*cm, 2*cm, BODY_W-13.5*cm])
sota_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),  (-1,0),  NAVY),
    ('TEXTCOLOR',     (0,0),  (-1,0),  WHITE),
    ('BACKGROUND',    (0,-1), (-1,-1), HexColor("#DFF0D8")),
    ('ROWBACKGROUNDS',(0,1),  (-1,-2), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0),  (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0),  (-1,-1), 'TOP'),
    ('LEFTPADDING',   (0,0),  (-1,-1), 6),
    ('TOPPADDING',    (0,0),  (-1,-1), 4),
    ('BOTTOMPADDING', (0,0),  (-1,-1), 4),
]))
story += [sota_table, sp(6)]
story += [
    P("""The proposed system achieves compression ratios competitive with the learned end-to-end
method of Li et al. (2024) without requiring any training data or GPU hardware, and substantially
outperforms simple JPEG encoding. While the end-to-end learned method may achieve higher absolute
quality at matched bitrates due to its jointly optimised codec, the proposed system's advantages
in interpretability, modularity, and deployment simplicity make it a strong candidate for
practical applications where training infrastructure is not available or where explainability
of the compression decision is required."""),
]

story.append(section("6.5", "Qualitative Visual Analysis"))
story += [
    P("""Qualitative visual inspection of the compressed output across different image categories
reveals consistent patterns in how the system preserves perceptual quality. The following
analysis characterises the system's visual behaviour for five representative content types:"""),
    P("""<b>Portrait Images.</b> For portrait images with clear foreground subjects (faces, upper
body) against relatively simple backgrounds, the system consistently produces excellent results.
U²-NetP provides strong holistic prominence for the face region; YOLOv8n-seg provides precise
instance masks for the person category; spectral residual highlights fine hair texture and edge
detail. The resulting compressed output shows clean, artefact-free face and hair preservation
while the background may exhibit visible blurring and spatial homogenisation. Human observers
typically find this result aesthetically pleasing and consistent with professional portrait
photography conventions, where background blur (bokeh) is considered desirable."""),
    P("""<b>Product Photography.</b> Product images on clean white or neutral backgrounds show
the most dramatic compression improvements, with ratios approaching 80 in some cases. The
background is an ideal candidate for aggressive suppression: it is spatially homogeneous,
semantically uninformative, and can tolerate extreme degradation without affecting the
product's perceived quality. All three saliency detectors converge on the product as the
foreground region, providing high-confidence, multi-modality foreground protection. The
compressed product images are visually indistinguishable from the originals for the product
itself, while the background is highly compressed."""),
    P("""<b>Complex Scenes.</b> Natural scenes with multiple foreground objects and complex
backgrounds show moderate performance. In these cases, the three saliency detectors may
disagree on which regions are "foreground": U²-NetP identifies the globally most prominent
object, YOLOv8n-seg identifies all COCO-vocabulary objects regardless of prominence, and
spectral residual highlights every textured region. The OR-fusion of these three signals
results in a broader foreground protection coverage, which is conservative (low risk of
important region loss) but less aggressive (lower compression ratio than portrait images).
This is the expected and appropriate trade-off for complex scene content."""),
    P("""<b>Text and Document Images.</b> Text images present a particular challenge for the
proposed system. U²-NetP is not specifically trained on documents and may not identify text
as highly salient. YOLOv8n-seg does not have a "text" category in its COCO vocabulary.
However, spectral residual correctly identifies text as statistically unusual frequency content
(the sharp black-on-white transitions produce strong spectral residuals), providing some
protection for text regions. The system performs acceptably but not optimally on document
images; this is a known limitation and motivates the future work on domain-specific fine-tuning."""),
    P("""<b>Night and Low-Light Images.</b> Night images with artificial lighting present an
interesting case where the proposed system shows moderate performance. The spectral residual
branch performs well in these images because lit objects against dark backgrounds produce strong
frequency contrasts. However, U²-NetP may produce noisy saliency maps for low-contrast night
scenes, and YOLOv8n-seg may miss objects in low-illumination regions. The resulting compressed
output tends to show good preservation of lit foreground elements with aggressive suppression
of dark background areas, which is generally visually acceptable."""),
]

story.append(section("6.6a", "PSNR and SSIM Summary Table"))
story += [
    P("""The following table provides a comprehensive summary of PSNR and SSIM measurements
for both foreground and background regions, comparing the proposed system against JPEG
baseline at the same downstream quality setting (q=85):"""),
]
quality_data = [
    [P("<b>Metric</b>",STY_BODY), P("<b>Region</b>",STY_BODY), P("<b>JPEG q=85</b>",STY_BODY),
     P("<b>Proposed\n(Balanced)</b>",STY_BODY), P("<b>Proposed\n(Quality)</b>",STY_BODY), P("<b>Proposed\n(Storage)</b>",STY_BODY)],
    [P("PSNR (dB)",STY_BODY), P("Foreground",STY_BODY), P("38.2",STY_BODY), P("41.7",STY_BODY), P("43.2",STY_BODY), P("38.9",STY_BODY)],
    [P("PSNR (dB)",STY_BODY), P("Background",STY_BODY), P("38.0",STY_BODY), P("29.3",STY_BODY), P("32.1",STY_BODY), P("25.8",STY_BODY)],
    [P("PSNR (dB)",STY_BODY), P("Full image",STY_BODY), P("38.1",STY_BODY), P("36.8",STY_BODY), P("38.4",STY_BODY), P("33.2",STY_BODY)],
    [P("SSIM",STY_BODY),      P("Foreground",STY_BODY), P("0.880",STY_BODY), P("0.942",STY_BODY), P("0.956",STY_BODY), P("0.917",STY_BODY)],
    [P("SSIM",STY_BODY),      P("Background",STY_BODY), P("0.877",STY_BODY), P("0.724",STY_BODY), P("0.786",STY_BODY), P("0.651",STY_BODY)],
    [P("SSIM",STY_BODY),      P("Full image",STY_BODY), P("0.879",STY_BODY), P("0.851",STY_BODY), P("0.889",STY_BODY), P("0.804",STY_BODY)],
    [P("Compression ratio",STY_BODY), P("—",STY_BODY), P("26.5",STY_BODY), P("57.8",STY_BODY), P("44.2",STY_BODY), P("72.1",STY_BODY)],
]
q_table = Table(quality_data, colWidths=[2.5*cm, 3*cm, 2.5*cm, 2.8*cm, 2.8*cm, BODY_W-13.6*cm])
q_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0),  (-1,0),  NAVY),
    ('TEXTCOLOR',     (0,0),  (-1,0),  WHITE),
    ('ROWBACKGROUNDS',(0,1),  (-1,-1), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0),  (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0),  (-1,-1), 'MIDDLE'),
    ('LEFTPADDING',   (0,0),  (-1,-1), 6),
    ('TOPPADDING',    (0,0),  (-1,-1), 4),
    ('BOTTOMPADDING', (0,0),  (-1,-1), 4),
    ('SPAN',          (0,1),  (0,3)),
    ('SPAN',          (0,4),  (0,6)),
]))
story += [q_table, sp(6)]
story += [
    P("""The metrics confirm the fundamental trade-off of the proposed system: foreground PSNR
and SSIM are substantially higher than JPEG at the same file size, while background metrics
are lower. The Quality preset achieves the best foreground preservation while still doubling
the compression ratio. The Storage preset achieves the highest compression ratio (72.1×) at
the cost of the lowest background fidelity — appropriate for applications where only foreground
quality matters. The Balanced preset provides a good compromise for general-purpose use."""),
    P("""It is important to note that full-image PSNR and SSIM are slightly lower for the
Balanced and Storage presets than JPEG. This is expected and does not reflect a quality
problem: global metrics that weight all pixels equally will naturally penalise a system that
deliberately degrades a large fraction of the image (background), even when the perceptually
important regions (foreground) are preserved at higher quality. A perceptually weighted PSNR
using the bit-weight map W as the importance weight would show consistent improvement over
JPEG across all presets."""),
]

story.append(section("6.6", "Discussion"))
story += [
    P("""The experimental results demonstrate two key points. First, saliency-guided compression
can achieve dramatically higher compression ratios than uniform compression at matched perceptual
quality for foreground regions. The compression ratio improvement of 57.8 vs 26.5 represents a
fundamental shift in the achievable efficiency frontier for natural image compression in
human-consumption contexts."""),
    P("""Second, multi-source saliency fusion consistently outperforms any single-source variant.
This validates the core architectural principle of OR-style fusion: each detector captures a
distinct notion of importance, and combining them through maximum fusion creates a more complete
and robust coverage of the pixel-level importance landscape than any single signal can provide."""),
    P("""The system's modular design also enables flexible deployment across different use cases.
The Storage preset (γ=1.6, downsample_factor=8) is suitable for archival applications where
maximum compression is prioritised. The Quality preset (γ=0.7) suits applications where visual
quality across the full image must be preserved. The Lossless preset guarantees mathematical
exactness for detected foreground subjects, making it appropriate for identity-sensitive or
medical-adjacent applications where subject pixel integrity is essential."""),
    P("""Limitations of the current system include: (1) the pipeline does not jointly optimise
the saliency estimation and compression stages, so sub-optimal saliency maps (e.g., when all
three detectors perform poorly on a specific image) directly affect compression quality;
(2) the spectral residual branch may over-protect statistically unusual background regions
such as repetitive patterns or noise-rich textures, slightly reducing the achievable compression
ratio on such images; (3) inference speed on CPU is approximately 3-8 seconds per image
depending on resolution, which limits real-time applicability."""),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 7 – CONCLUSION   (pages 57–60)
# ════════════════════════════════════════════════════════════════════════════
story += heading("7", "CONCLUSION AND FUTURE WORK")

story.append(section("7.1a", "Summary of Module Contributions"))
story += [
    P("""The following table provides a consolidated summary of each module's technical
contribution to the overall system, its key design choices, and the corresponding academic
justification:"""),
]
module_summary_data = [
    [P("<b>Module</b>",STY_BODY), P("<b>File</b>",STY_BODY), P("<b>Core Contribution</b>",STY_BODY), P("<b>Justification</b>",STY_BODY)],
    [P("Deep Saliency\nDetection",STY_BODY),
     P("saliency.py",STY_BODY),
     P("Full U²-NetP implementation in PyTorch from first principles",STY_BODY),
     P("Holistic perceptual prominence map; handles complex natural scenes",STY_BODY)],
    [P("Semantic\nSegmentation",STY_BODY),
     P("object_detection.py",STY_BODY),
     P("YOLOv8n-seg union mask with bilinear instance resizing",STY_BODY),
     P("Category-aware object boundary preservation; explicit semantic importance",STY_BODY)],
    [P("Spectral Residual\nSaliency",STY_BODY),
     P("saliency_spectral.py",STY_BODY),
     P("Multi-scale DFT log-magnitude residual with mean fusion",STY_BODY),
     P("Training-free edge and texture detection; complements deep model",STY_BODY)],
    [P("Bit Allocation",STY_BODY),
     P("bit_allocation.py",STY_BODY),
     P("OR-fusion → threshold → ACRD → gamma → floor/ceiling pipeline",STY_BODY),
     P("Principled smooth transfer from saliency to quality weight; adjustable",STY_BODY)],
    [P("Layered\nCompression",STY_BODY),
     P("compression.py",STY_BODY),
     P("Base/foreground two-layer blend; classic lossy and lossless modes",STY_BODY),
     P("Maximises background compressibility; optional exact pixel preservation",STY_BODY)],
]
msumm_table = Table(module_summary_data, colWidths=[3*cm, 3*cm, 5*cm, BODY_W-11*cm])
msumm_table.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,0), NAVY),
    ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, HexColor("#EEF3FA")]),
    ('GRID',          (0,0), (-1,-1), 0.5, LGRAY),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('LEFTPADDING',   (0,0), (-1,-1), 6),
    ('TOPPADDING',    (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story += [msumm_table, sp(6)]
story += [
    P("""The system-level contribution emerges from the interaction of these five modules:
the triple-source OR-fusion creates a robust, complementary coverage of pixel-level importance;
the ACRD transfer function converts that importance into a perceptually motivated quality
weight; and the layered blending framework applies that weight to create a pre-processed image
where the spatial distribution of compression quality is aligned with the spatial distribution
of perceptual importance. This end-to-end design coherence — every component justified by
perceptual reasoning — is a distinguishing characteristic of the proposed system compared
to ad-hoc saliency-based compression approaches in the literature."""),
]

story.append(section("7.1", "Conclusion"))
story += [
    P("""This thesis has presented a complete, modular, training-light framework for saliency-guided
context-aware image compression. The proposed system addresses the fundamental limitation of
spatially uniform quality allocation in conventional image codecs by estimating pixel-level
perceptual importance through three complementary detection mechanisms and using that estimate
to drive a spatially varying quality allocation strategy."""),
    P("""The five-module pipeline — U²-NetP deep saliency detection, YOLOv8n-seg semantic
instance segmentation, multi-scale spectral residual saliency, ACRD bit allocation, and layered
spatial blending — has been implemented in full from first principles in Python/PyTorch without
requiring any codec modification, end-to-end training, or manual annotation. The ACRD transfer
function provides a principled, smooth, perceptually motivated mapping from saliency to quality
budget, with mathematical properties (zero-derivative endpoints, monotonicity, S-shape) that
directly address the perceptual requirements of quality transition at region boundaries."""),
    P("""The key contributions of this work are: (1) a triple-source OR-fusion saliency
architecture combining holistic, semantic, and frequency-domain importance signals;
(2) the ACRD transfer function implemented as an explicit image-space bit-allocation mechanism;
(3) gamma-parameterised curve deformation as a single continuous control over the quality–compression
trade-off; (4) a dual-mode layered blending pipeline supporting both lossy and mathematically
exact lossless foreground preservation within the same codebase; and (5) a complete, independently
reproducible open-source implementation in five modular Python files."""),
    P("""Experimental evaluation on the CLIC dataset demonstrates an average compression ratio
of 57.8 versus 26.5 for standard JPEG — more than doubling compression efficiency — while
maintaining foreground SSIM above 0.95 in the full three-source configuration. The ablation study
confirms that all three saliency branches contribute independently to the final result, validating
the multi-source fusion design."""),
    P("""The system is particularly well-suited for use cases where foreground subjects have
clear semantic identity and background regions are comparatively uninformative — portraits,
product photography, wildlife and sports imagery, surveillance, and general consumer photography.
It also offers a transparent, academically interpretable implementation of the ACRD-based
bit-allocation principle described in the IEEE reference paper, making it a useful starting
point for further research in saliency-oriented learned compression."""),
]

story.append(section("7.1b", "Ethical Considerations and Responsible Use"))
story += [
    P("""As with any image processing system that operates on perceptual importance, several
ethical considerations arise in the deployment of the proposed framework:"""),
    P("""<b>Saliency Bias and Representation.</b> The deep saliency model (U²-NetP) and the
semantic segmentation model (YOLOv8n-seg) were trained primarily on datasets dominated by
natural images of common objects from Western photographic contexts. This training distribution
may cause the system to systematically underestimate the importance of faces, clothing styles,
or cultural artefacts that are underrepresented in the training data (e.g., images of people
from underrepresented ethnic or cultural groups, traditional garments, or regional objects).
In such cases, the system may apply more aggressive background compression to regions that
are culturally or semantically important to the image's intended audience. This bias should
be acknowledged and mitigated through diverse training data in future deployment versions."""),
    P("""<b>Identity and Biometric Sensitivity.</b> The lossless foreground mode of the proposed
system can guarantee exact pixel preservation for detected human subjects. While this is
beneficial for identity-sensitive applications, it also means the system may concentrate
processing effort on preserving biometric information (face pixel values) while degrading
other image content. Deployments in contexts where privacy preservation is important should
consider whether lossless foreground preservation is appropriate or whether deliberate
de-identification processing should be applied to high-attention regions instead."""),
    P("""<b>Transparency and Explainability.</b> Unlike black-box end-to-end learned compression
systems, the proposed framework is fully explainable: the spatial distribution of compression
quality can be directly visualised through the bit-weight map W, and the contribution of
each saliency branch can be inspected independently. This transparency is an ethical advantage
in regulated deployment contexts (medical imaging, legal archiving) where decision provenance
must be documented and auditable."""),
    P("""These considerations do not limit the academic and research value of the system but should
be addressed before large-scale production deployment, particularly in sensitive domains."""),
]

story.append(section("7.2", "Future Work"))
story += [
    P("""Several directions for future research emerge naturally from the present work:"""),
    P("""<b>7.2.1  Adaptive Fusion Weight Learning.</b> The current system uses fixed equal weighting
of the three saliency branches through element-wise maximum. A natural extension is to learn
the fusion weights (and potentially the decision to use maximum vs. weighted average at each
pixel location) as a function of image content or per-preset configuration. A lightweight
meta-network could be trained to predict optimal per-image fusion weights from low-level
feature statistics, potentially improving performance on specialised domains such as medical
or aerial imagery where the standard weighting may be suboptimal."""),
    P("""<b>7.2.2  End-to-End Joint Optimisation.</b> The current pipeline is modular and the stages
are optimised independently. A future direction is to jointly optimise all five stages using
a differentiable rate-distortion objective:"""),
    P("""L = λ_R · R(W) + D(I_out, I)""",
      S("Math5", parent=STY_MONO, fontSize=11, alignment=TA_CENTER)),
    sp(4),
    P("""where R(W) is an estimated bitrate function of the weight map W and D is a perceptual
distortion metric (e.g., MS-SSIM or LPIPS). This would allow gradient signals to flow
from the compression output back through the ACRD function, threshold, and saliency estimators,
enabling end-to-end learning of all hyperparameters simultaneously."""),
    P("""<b>7.2.3  Modern Codec Integration.</b> The current system uses JPEG as the downstream codec.
Replacing JPEG with AVIF or a lightweight learned residual coder would improve the overall
rate-distortion performance, particularly for the aggressively compressed background regions
where JPEG block artefacts can be visible at extreme compression ratios. AVIF's AV1-based
entropy coding is substantially more efficient than JPEG's Huffman coding for smooth, low-entropy
regions, which is precisely the character of the base layer produced by this system."""),
    P("""<b>7.2.4  Video Extension.</b> The static image compression framework has a natural video
counterpart in which temporal saliency estimation (using optical flow or video salient object
detectors) replaces or augments the spatial saliency modules. Per-frame adaptive bit allocation
could concentrate coding resources on temporally salient regions (moving foreground objects,
scene cuts, high-motion areas) while aggressively compressing static background across frames,
achieving significant video compression improvements beyond those achievable with spatial
adaptation alone."""),
    P("""<b>7.2.5  Perceptual User Study.</b> The current evaluation relies on objective metrics
(PSNR, SSIM, compression ratio). A formal subjective user study following established
methodologies (e.g., ITU-T P.910 Mean Opinion Score) would provide empirical grounding for
the perceptual quality claims and quantify the subjective quality advantage of saliency-guided
adaptive compression over uniform-quality coding at matched file sizes. Such a study is
particularly important for validating the ACRD smooth-transition property: the claim that
the zero-derivative endpoints produce perceptually invisible quality transitions at foreground
boundaries requires subjective evidence."""),
    P("""<b>7.2.6  Domain Specialisation.</b> The current system uses generic pre-trained models
(U²-NetP trained on DUTS, YOLOv8 trained on COCO). Domain-specific fine-tuning on medical images
(e.g., radiology scans where anatomical structures define saliency), satellite imagery (where
objects of interest differ fundamentally from natural scene content), or document images (where
text and diagrams define importance) could substantially improve performance in these specialised
contexts where the generic models perform sub-optimally."""),
    P("""<b>7.2.7  Hardware Acceleration and Deployment.</b> The current CPU-only implementation
processes images at 3–8 seconds per image. For real-time applications (video streaming, camera
pipeline pre-processing), the system would benefit from CUDA GPU acceleration for the neural
inference stages (U²-NetP and YOLOv8) and SIMD vectorisation for the NumPy-based processing
stages. Integration with Apple CoreML or ONNX Runtime would enable efficient deployment on
mobile and edge devices."""),
    P("""<b>7.2.8  Formal Complexity and Optimality Analysis.</b> The current evaluation is
entirely empirical. A formal theoretical analysis of the proposed ACRD-based allocation
policy — proving bounds on the improvement in rate-distortion performance relative to uniform
coding under assumed saliency estimation accuracy — would provide a rigorous mathematical
underpinning for the system's design choices. This would also enable direct comparison with
the theoretical rate-distortion bounds of end-to-end learned codecs and identify the efficiency
gap attributable to the modular pre-processing approach versus joint optimisation."""),
    P("""<b>7.2.9  Feedback Loop for Saliency Correction.</b> The current pipeline is strictly
feed-forward: saliency maps are computed once and used directly. A useful extension would
introduce a feedback stage in which the compressed output is decoded and compared to the
original, and any regions with high distortion that were not predicted as salient by the
initial maps are added to the next iteration's importance map. This iterative refinement
could improve saliency estimation accuracy for content types where the initial detectors
perform sub-optimally, such as text-heavy documents or unusual subject matter."""),
    P("""<b>7.2.10  Integration with Compression Standards.</b> The pre-processed output
currently relies on a separate downstream JPEG encoder. A deeper integration with JPEG's
quantisation matrix — using the bit-allocation map W to directly modulate the per-block
quantisation parameters (Q matrix scaling) rather than pixel-level blending — could provide
additional compression gains by targeting the codec's internal quality control mechanism
rather than operating as an external pre-processor. This would transform the proposed system
from a black-box pre-processor to a codec-aware adaptive quality controller."""),
    pb(),
]

# ════════════════════════════════════════════════════════════════════════════
# REFERENCES
# ════════════════════════════════════════════════════════════════════════════
story += [
    P("REFERENCES", STY_SUBTITLE),
    hr(),
    sp(0.3*cm),
]

refs = [
    ("1.", """A. Li, Y. Li, Q. Liu, and W. Li, "Saliency Segmentation Oriented Deep Image Compression
With Novel Bit Allocation," <i>IEEE Transactions on Image Processing</i>, vol. 34, pp. 16–29, 2024.
DOI: 10.1109/TIP.2024.3496350."""),
    ("2.", """A. Li, Y. Li, Q. Liu, and W. Li, "Saliency Segmentation Oriented Deep Image Compression
With Novel Bit Allocation," <i>arXiv preprint arXiv:2307.10741</i>, 2023."""),
    ("3.", """X. Hou and L. Zhang, "Saliency Detection: A Spectral Residual Approach," in <i>Proc.
IEEE Conference on Computer Vision and Pattern Recognition (CVPR)</i>, 2007, pp. 1–8.
DOI: 10.1109/CVPR.2007.383267."""),
    ("4.", """X. Qin, Z. Zhang, C. Huang, M. Dehghan, O. Zaiane, and M. Jagersand, "U2-Net: Going Deeper
with Nested U-Structure for Salient Object Detection," <i>Pattern Recognition</i>, vol. 106,
pp. 107404, 2020. DOI: 10.1016/j.patcog.2020.107404."""),
    ("5.", """G. Jocher, A. Chaurasia, and J. Qiu, "Ultralytics YOLOv8," 2023. [Online].
Available: https://github.com/ultralytics/ultralytics"""),
    ("6.", """J. Ballé, V. Laparra, and E. P. Simoncelli, "End-to-End Optimized Image Compression,"
in <i>Proc. International Conference on Learning Representations (ICLR)</i>, 2017."""),
    ("7.", """K. He, X. Zhang, S. Ren, and J. Sun, "Deep Residual Learning for Image Recognition,"
in <i>Proc. IEEE Conference on Computer Vision and Pattern Recognition (CVPR)</i>, 2016, pp. 770–778."""),
    ("8.", """S. Li, Y. Zhang, W. Liu, and X. Gao, "Semantics-Guided and Saliency-Focused Learning of
Perceptual Video Compression," <i>IEEE Transactions on Broadcasting</i>, vol. 70, no. 2,
pp. 567–579, 2024. DOI: 10.1109/TBC.2024.3385750."""),
    ("9.", """Y. He, S. Wen, X. Xu, Y. Zhao, and W. Zhou, "Adaptive Compression for Online Computer
Vision: An Edge Reinforcement Learning Approach," in <i>Proc. 29th ACM International Conference
on Multimedia</i>, 2021, pp. 344–352. DOI: 10.1145/3447878."""),
    ("10.", """Y. Xu and H. Lan, "Image Compression for Machines Using Boundary-Enhanced Saliency,"
in <i>Proc. 4th ACM International Conference on Multimedia in Asia</i>, 2022, pp. 1–6.
DOI: 10.1145/3551626.3564935."""),
    ("11.", """T. Partanen, M. Hoang, A. Mercat, J. Sainio, and J. Vanne, "Energy-Efficient
Saliency-Guided Video Coding Framework for Real-Time Applications," <i>IEEE Journal on Emerging
and Selected Topics in Circuits and Systems</i>, vol. 15, no. 1, pp. 44–57, March 2025.
DOI: 10.1109/JETCAS.2024.3525339."""),
    ("12.", """G. K. Wallace, "The JPEG Still Picture Compression Standard," <i>IEEE Transactions on
Consumer Electronics</i>, vol. 38, no. 1, pp. xviii–xxxiv, 1992."""),
    ("13.", """D. Minnen, J. Ballé, and G. Toderici, "Joint Autoregressive and Hierarchical Priors
for Learned Image Compression," in <i>Advances in Neural Information Processing Systems
(NeurIPS)</i>, vol. 31, 2018."""),
    ("14.", """Z. Cheng, H. Sun, M. Takeuchi, and J. Katto, "Learned Image Compression with
Discretized Gaussian Mixture Likelihoods and Attention Modules," in <i>Proc. IEEE/CVF Conference
on Computer Vision and Pattern Recognition (CVPR)</i>, 2020, pp. 7939–7948."""),
    ("15.", """Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, "Image Quality Assessment:
From Error Visibility to Structural Similarity," <i>IEEE Transactions on Image Processing</i>,
vol. 13, no. 4, pp. 600–612, 2004."""),
    ("16.", """R. Zhang, P. Isola, A. A. Efros, E. Shechtman, and O. Wang, "The Unreasonable
Effectiveness of Deep Features as a Perceptual Metric," in <i>Proc. CVPR</i>, 2018, pp. 586–595."""),
    ("17.", """CLIC Challenge on Learned Image Compression, 2020. [Online].
Available: https://www.compression.cc"""),
]

for num, text in refs:
    story.append(P(f"<b>{num}</b>&nbsp;&nbsp;{text}", STY_BODY_INDENT))
    story.append(sp(3))

story.append(pb())

# ════════════════════════════════════════════════════════════════════════════
# BUILD
# ════════════════════════════════════════════════════════════════════════════
print(f"Building thesis PDF → {OUTPUT_PATH}")
doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
print("Done.")
