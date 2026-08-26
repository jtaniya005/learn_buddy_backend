import sys
import os

# Add the app directory to sys.path so we can import services
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.ocr_service import parse_ocr_text

test_text_1 = """
Student Name: John Doe
Class: XII
Physics 82 100
Chemistry 75 100
Mathematics 88 100
English (Core)
78 100
"""

test_text_2 = """
Student Name: Jane Doe
Class: 12
English Core 78 100
"""

print("=== TEST 1 (Line Splitting) ===")
res1 = parse_ocr_text(test_text_1)
print("\nResult 1:", res1)

print("\n=== TEST 2 (Multi-word English) ===")
res2 = parse_ocr_text(test_text_2)
print("\nResult 2:", res2)
