import re
import difflib

KNOWN_SUBJECTS = [
    "Mathematics", "Science", "Social Science", "English", "Hindi",
    "Computer Applications", "Information Technology",
    "Physics", "Chemistry", "Biology",
    "Accountancy", "Business Studies", "Economics",
    "History", "Political Science", "Geography",
]

def match_known_subject(raw: str):
    raw = raw.strip()
    if len(raw) < 3:
        return None
    matches = difflib.get_close_matches(raw, KNOWN_SUBJECTS, n=1, cutoff=0.6)
    return matches[0] if matches else None

MARK_LINE_FUZZY = re.compile(
    r"(?:^\s*(?:\d+[\.\)]?\s*)?)(?P<subject>[A-Za-z][A-Za-z .]{2,35}?)\s*[:\-\|]?\s+"
    r"(?P<obtained>\d{1,3}(?:\.\d+)?)(?:\s+(?:/|out of|\\|\||\s*)\s*(?P<total>\d{1,3}(?:\.\d+)?))?",
    re.IGNORECASE
)

test_cases = [
    "Mathematics 85 100",
    "1. Science       78 / 100",
    "English 90",
    "Social Science : 88 out of 100",
    "02  Hindi        95     100    95 A1",
    "Physics 45 50",
    "   Chemistry  85.5 100",
    "Mathemstics 85 100", # OCR error
]

def test_regex(pattern, name):
    print(f"\n--- Testing {name} ---")
    for tc in test_cases:
        m = pattern.search(tc)
        if m:
            subj = match_known_subject(m.group('subject'))
            if subj:
                print(f"MATCH: {tc} -> subject: {subj}, obtained: {m.group('obtained')}, total: {m.group('total')}")
            else:
                print(f"MATCH but NO SUBJ: {tc} -> {m.group('subject')}")
        else:
            print(f"FAIL : {tc}")

test_regex(MARK_LINE_FUZZY, "FUZZY Regex")
