import re
import difflib
import fitz  # pymupdf
import cv2
import numpy as np
import pytesseract
from PIL import Image
from fastapi import HTTPException

from app.core.config import settings

# Configure Tesseract path if set in environment (especially useful on Windows)
if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
else:
    # Fallback to default winget installation path in case backend wasn't restarted
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

import os
from pathlib import Path
# Set TESSDATA_PREFIX so Tesseract finds the downloaded language models
os.environ["TESSDATA_PREFIX"] = str(Path(__file__).parent.parent.parent / "tessdata")

KNOWN_SUBJECTS = [
    "Mathematics", "Science", "Social Science", "English", "Hindi",
    "Computer Applications", "Computer Science", "Information Technology",
    "Physics", "Chemistry", "Biology",
    "Accountancy", "Business Studies", "Economics",
    "History", "Political Science", "Geography",
]

# Pattern to extract subject name followed by 2-3 numbers (marks columns).
# Allows parenthesized text in subject names like "English (Sample)".
# Captures up to three numeric columns so we can figure out which is obtained vs total.
_MARKS_ROW = re.compile(
    r"(?:^\s*(?:\d+[\.)\]]?\s*)?)"                        # optional serial no.
    r"(?P<subject>[A-Za-z][A-Za-z .()\-]{2,45}?)"         # subject name (allows parens)
    r"\s+(?P<n1>\d{1,3}(?:\.\d+)?)"                       # first number
    r"(?:\s+(?P<n2>\d{1,3}(?:\.\d+)?))?"                  # second number (optional)
    r"(?:\s+(?P<n3>[A-Za-z+\-]{1,3}|\d{1,3}(?:\.\d+)?))?" # third col: grade or number
    r"\s*$",
    re.IGNORECASE,
)

# Legacy pattern: "subject : obtained / total" (colon-separated style)
MARK_LINE = re.compile(
    r"(?:^\s*(?:\d+[\.)\]]?\s*)?)(?P<subject>[A-Za-z][A-Za-z .()\-]{2,45}?)\s*[:\-\|]\s+"
    r"(?P<obtained>\d{1,3}(?:\.\d+)?)(?:\s*(?:/|out of|\\|\|)\s*(?P<total>\d{1,3}(?:\.\d+)?))?",
    re.IGNORECASE
)
PERCENT_LINE = re.compile(
    r"(percentage|aggregate|overall)\D{0,15}(?P<value>\d{1,3}(?:\.\d+)?)\s*%?",
    re.IGNORECASE,
)
_NAME_LINE = re.compile(
    r"(?:student'?s?\s*name|name\s*of\s*student|name)\s*[:\-]\s*([A-Za-z .]{3,40})",
    re.IGNORECASE,
)
_CLASS_LINE = re.compile(
    r"class\s*[:\-]?\s*(IX|X[IT]I|X[IT]|XII|XI|X|9|10|11|12)\b",
    re.IGNORECASE,
)

def pdf_to_images(pdf_bytes: bytes) -> list[np.ndarray]:
    """Convert a PDF byte stream into a list of OpenCV-compatible numpy arrays (BGR)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        elif pix.n == 1:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
        images.append(img_array)
    return images

def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """Preprocess an image array for better Tesseract accuracy."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    # Adaptive threshold handles uneven lighting/shadows better than a fixed threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh, h=10)
    return denoised

def ocr_image_array(img_array: np.ndarray) -> str:
    """Run Tesseract OCR on a preprocessed numpy array image."""
    # Ensure it's passed as a PIL image for pytesseract
    pil_image = Image.fromarray(img_array)
    return pytesseract.image_to_string(pil_image, lang="eng")

def match_known_subject(raw: str) -> str | None:
    raw = raw.strip()
    if len(raw) < 3:
        return None
    matches = difflib.get_close_matches(raw, KNOWN_SUBJECTS, n=1, cutoff=0.6)
    return matches[0] if matches else None

def parse_ocr_text(text: str) -> dict:
    """Parse OCR text block into structured marks dictionary."""
    percentage = None
    detected_name = None
    detected_class = None
    marks = []
    seen = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        print(f"LINE: {line!r}")

        # ── English-specific debug: print raw line before any matching ──
        if "english" in line.lower() or "eng" in line.lower():
            print(f"ENGLISH-LIKE LINE: {line!r}")

        # Check name
        if detected_name is None:
            name_m = _NAME_LINE.search(line)
            if name_m:
                detected_name = name_m.group(1).strip()
        
        # Check class
        if detected_class is None:
            class_m = _CLASS_LINE.search(line)
            if class_m:
                c_str = class_m.group(1).upper()
                if c_str in ("IX", "9"): detected_class = 9
                elif c_str in ("X", "10"): detected_class = 10
                elif c_str in ("XI", "11"): detected_class = 11
                elif c_str in ("XII", "12"): detected_class = 12

        if percentage is None:
            pct = PERCENT_LINE.search(line)
            if pct:
                percentage = float(pct.group("value"))
                print(f"  -> matched percentage: {percentage}")
                continue
        # --- Try the tabular row pattern first (e.g. "English (Sample) 100 78 B+") ---
        row = _MARKS_ROW.match(line)
        m = None
        if row:
            subj_raw = row.group("subject")
            n1 = row.group("n1")
            n2 = row.group("n2")
            subject = match_known_subject(subj_raw)
            if subject and subject not in seen and n1:
                if n2:
                    v1, v2 = float(n1), float(n2)
                    # Determine column order: if first number >= second, it's "total obtained"
                    if v1 >= v2:
                        total, obtained = v1, v2
                    else:
                        obtained, total = v1, v2
                else:
                    # Only one number — assume it's obtained out of 100
                    obtained, total = float(n1), 100.0
                marks.append({"subject": subject, "marks_obtained": obtained, "total_marks": total})
                seen.add(subject)
                print(f"  -> ROW matched | subject={subject!r} obtained={obtained} total={total}")
                continue
            elif subject and "english" in subject.lower():
                # Diagnostic: English subject fuzzy-matched but numbers missing
                print(f"  -> ENGLISH DIAG: subject={subject!r} n1={n1!r} n2={n2!r} raw_groups={row.groups()!r}")

        # --- Fallback: colon-separated pattern (e.g. "English: 78/100") ---
        m = MARK_LINE.match(line)
        if m:
            subject = match_known_subject(m.group("subject"))
            if subject and subject not in seen:
                obtained = float(m.group("obtained"))
                total = float(m.group("total")) if m.group("total") else 100.0
                marks.append({"subject": subject, "marks_obtained": obtained, "total_marks": total})
                seen.add(subject)
                print(f"  -> LEGACY matched | subject={subject!r} obtained={obtained} total={total}")
                continue

        print(f"  -> no match")

    # ── Fallback pass: join consecutive short lines and re-match ──
    # Tesseract sometimes splits a single row across two lines, e.g.:
    #   "English"  (line N)
    #   "78 100"   (line N+1)
    # This pass joins consecutive short lines and tries the regex again.
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i in range(len(lines) - 1):
        if len(lines[i]) < 30 and len(lines[i + 1]) < 30:
            joined = lines[i] + " " + lines[i + 1]
            row = _MARKS_ROW.match(joined)
            if row:
                subj_raw = row.group("subject")
                n1 = row.group("n1")
                n2 = row.group("n2")
                subject = match_known_subject(subj_raw)
                if subject and subject not in seen and n1:
                    if n2:
                        v1, v2 = float(n1), float(n2)
                        if v1 >= v2:
                            total, obtained = v1, v2
                        else:
                            obtained, total = v1, v2
                    else:
                        obtained, total = float(n1), 100.0
                    marks.append({"subject": subject, "marks_obtained": obtained, "total_marks": total})
                    seen.add(subject)
                    print(f"  -> JOINED matched | subject={subject!r} obtained={obtained} total={total} from lines {i},{i+1}")
                    continue
            # Also try the colon-separated fallback on the joined line
            m = MARK_LINE.match(joined)
            if m:
                subject = match_known_subject(m.group("subject"))
                if subject and subject not in seen:
                    obtained = float(m.group("obtained"))
                    total = float(m.group("total")) if m.group("total") else 100.0
                    marks.append({"subject": subject, "marks_obtained": obtained, "total_marks": total})
                    seen.add(subject)
                    print(f"  -> JOINED LEGACY matched | subject={subject!r} obtained={obtained} total={total} from lines {i},{i+1}")

    print(f"DETECTED NAME: {detected_name!r}")
    print(f"DETECTED CLASS: {detected_class!r}")
    
    return {
        "previous_class_percentage": percentage,
        "detected_name": detected_name,
        "detected_class": detected_class,
        "marks": marks
    }

def extract_marksheet_data(file_bytes: bytes, filename: str, content_type: str) -> dict:
    """Main pipeline for marksheet extraction from an uploaded file."""
    try:
        if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
            images = pdf_to_images(file_bytes)
            if not images:
                raise HTTPException(status_code=400, detail="PDF is empty")
        else:
            np_arr = np.frombuffer(file_bytes, np.uint8)
            img_array = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img_array is None:
                raise HTTPException(status_code=400, detail="Invalid image file")
            images = [img_array]

        full_text = ""
        for img in images:
            preprocessed = preprocess_for_ocr(img)
            text = ocr_image_array(preprocessed)
            full_text += text + "\n"

        print("=" * 40)
        print("RAW OCR TEXT:")
        print(full_text)
        print("=" * 40)

        result = parse_ocr_text(full_text)
        if not result["marks"] and result["previous_class_percentage"] is None:
            raise HTTPException(status_code=422, detail="Could not extract any marks from this image.")
        
        return result

    except pytesseract.TesseractNotFoundError:
        raise HTTPException(
            status_code=500, 
            detail="Tesseract is not installed or not on PATH. Please configure TESSERACT_CMD or install it."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
