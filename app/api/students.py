from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import Dict, Any
import difflib

from app.services.ocr_service import extract_marksheet_data, KNOWN_SUBJECTS
from app.dependencies.auth_deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/students", tags=["Students"])

def get_expected_subjects(student_class: int) -> list[str]:
    # Reuse KNOWN_SUBJECTS for simplicity until stream mapping is implemented
    return KNOWN_SUBJECTS

@router.post("/me/marksheet/extract")
async def extract_marksheet(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    print("FILE:", file.filename)
    print("CONTENT TYPE:", file.content_type)
    contents = await file.read()
    print("FILE SIZE:", len(contents))
    print("Calling extract_marksheet_data...")
    result = extract_marksheet_data(contents, file.filename, file.content_type)
    
    warnings = []
    
    detected_name = result.get("detected_name")
    if detected_name and current_user.name:
        similarity = difflib.SequenceMatcher(
            None, detected_name.lower(), current_user.name.lower()
        ).ratio()
        if similarity < 0.6:
            warnings.append(
                f"This marksheet says the name is '{detected_name}', but your "
                f"profile says '{current_user.name}'. Please make sure this is your own marksheet."
            )
            
    detected_class = result.get("detected_class")
    if detected_class:
        expected_previous_class = 9 if current_user.student_class == 10 else 11
        if detected_class != expected_previous_class:
            warnings.append(
                f"This marksheet appears to be for Class {detected_class}, but we "
                f"expected Class {expected_previous_class} (your previous class). Please check "
                f"you uploaded the right document."
            )
            
    expected_subjects = get_expected_subjects(current_user.student_class)
    unexpected = [m["subject"] for m in result.get("marks", []) if m["subject"] not in expected_subjects]
    if unexpected:
        warnings.append(
            f"These subjects don't match your class/stream: {', '.join(unexpected)}. Double-check they're correct."
        )
        
    result["warnings"] = warnings
    return result

@router.post("/me/marksheet/save")
def save_marksheet(data: dict):
    return {"status": "success"}
