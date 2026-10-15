import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["PYTHONUNBUFFERED"] = "1"

import sys
import pandas as pd
import numpy as np
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from app.core.config import settings

# Load configuration and ensure Pinecone keys exist
PINECONE_API_KEY = settings.PINECONE_API_KEY or "pcsk_qzvqg_45k7FnGvmyPFV7NkHpXCHCFnuRixV1Vddtt7zFSNszwpMDQK7UB2n61LfYaD5LQ"
PINECONE_INDEX_NAME = settings.PINECONE_INDEX_NAME or "learn-buddy"

if not PINECONE_API_KEY:
    print("Error: PINECONE_API_KEY not found in configuration or .env file.")
    sys.exit(1)

# Ensure stdout handles UTF-8 correctly
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize SentenceTransformer
print("Initializing local embedding model (all-mpnet-base-v2)...")
embed_model = SentenceTransformer('all-mpnet-base-v2')

# Initialize Pinecone
print("Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if it does not exist
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating Pinecone index '{PINECONE_INDEX_NAME}'...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=768,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )
    import time
    while not pc.describe_index(PINECONE_INDEX_NAME).status['ready']:
        print("Waiting for index to become ready...")
        time.sleep(2)

index = pc.Index(PINECONE_INDEX_NAME)

excel_path = "career buddy.xlsx"
if not os.path.exists(excel_path):
    excel_path = os.path.join(os.path.dirname(__file__), "career buddy.xlsx")
    if not os.path.exists(excel_path):
        print(f"Error: excel file not found at {excel_path}")
        sys.exit(1)

print(f"Reading excel sheet from {excel_path}...")

def clean_val(val):
    if pd.isna(val) or val is None:
        return ""
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val).strip()

def clean_dict_metadata(metadata_dict):
    clean = {}
    for k, v in metadata_dict.items():
        val = clean_val(v)
        if val != "":
            clean[k] = val
    return clean

def chunk_and_upsert(vectors, namespace):
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch, namespace=namespace)
        print(f"Upserted {len(batch)} vectors to namespace '{namespace}' (Total: {i + len(batch)}/{len(vectors)})")

# ==========================================
# 1. CAREER NAMESPACE
# ==========================================
def process_careers():
    print("\n--- Processing Careers ---")
    df_master = pd.read_excel(excel_path, sheet_name="Career Master")
    df_roadmap = pd.read_excel(excel_path, sheet_name="Carrer Roadmap")
    df_skills = pd.read_excel(excel_path, sheet_name="skills")
    df_exams = pd.read_excel(excel_path, sheet_name="Entrance-Exam")
    df_descriptions = pd.read_excel(excel_path, sheet_name="Descriptions")

    texts = []
    metadata_list = []
    ids = []
    
    for idx, row in df_master.iterrows():
        career_id = clean_val(row.get("Career ID"))
        if not career_id:
            continue
            
        career_name = clean_val(row.get("Career Name"))
        category = clean_val(row.get("Category"))
        eligible = clean_val(row.get("Eligible After"))
        stream = clean_val(row.get("Stream"))
        min_qual = clean_val(row.get("Min Qualification"))
        short_desc = clean_val(row.get("Short Description"))
        future_demand = clean_val(row.get("Future Demand"))
        ai_impact = clean_val(row.get("AI Impact"))
        
        # Get descriptions
        desc_row = df_descriptions[df_descriptions["Career ID"] == career_id]
        overview = ""
        what_they_do = ""
        responsibilities = ""
        work_env = ""
        work_mode = ""
        growth = ""
        scope = ""
        
        if not desc_row.empty:
            overview = clean_val(desc_row.iloc[0].get("Career Overview"))
            what_they_do = clean_val(desc_row.iloc[0].get("What They Do"))
            responsibilities = clean_val(desc_row.iloc[0].get("Key Responsibilities"))
            work_env = clean_val(desc_row.iloc[0].get("Typical Work Environment"))
            work_mode = clean_val(desc_row.iloc[0].get("Work Mode"))
            growth = clean_val(desc_row.iloc[0].get("Career Growth"))
            scope = clean_val(desc_row.iloc[0].get("Future Scope"))
            
        # Get skills
        skills_row = df_skills[df_skills["Career ID"] == career_id]
        tech_skills = ""
        prog_skills = ""
        tools = ""
        soft_skills = ""
        if not skills_row.empty:
            tech_skills = clean_val(skills_row.iloc[0].get("Technical Skills"))
            prog_skills = clean_val(skills_row.iloc[0].get("Programming Skills"))
            tools = clean_val(skills_row.iloc[0].get("Tools"))
            soft_skills = clean_val(skills_row.iloc[0].get("Soft Skills"))

        # Get roadmap
        roadmap_rows = df_roadmap[df_roadmap["Career ID"] == career_id].sort_values(by="Step No")
        roadmap_txt = []
        for r_idx, r_row in roadmap_rows.iterrows():
            step_no = clean_val(r_row.get("Step No"))
            step_title = clean_val(r_row.get("Title"))
            step_desc = clean_val(r_row.get("Description"))
            roadmap_txt.append(f"Step {step_no}: {step_title} - {step_desc}")
        roadmap_steps_text = "\n".join(roadmap_txt)

        # Get exams
        exam_row = df_exams[df_exams["Career ID"] == career_id]
        exams_list = []
        if not exam_row.empty:
            for col in ["Exam 1", "Exam 2", "Exam 3", "Exam 4", "Exam 5"]:
                exam_name = clean_val(exam_row.iloc[0].get(col))
                if exam_name and exam_name != "-":
                    exams_list.append(exam_name)
        exams_text = ", ".join(exams_list)

        text_content = f"""Career ID: {career_id}
Career Name: {career_name}
Category: {category}
Eligible After: {eligible} | Stream: {stream} | Min Qualification: {min_qual}
Short Description: {short_desc}
Future Demand: {future_demand} | AI Impact: {ai_impact}

Overview:
{overview}

What They Do & Key Responsibilities:
{what_they_do}
{responsibilities}

Work Environment & Mode:
{work_env} | Mode: {work_mode}

Skills Required:
Technical: {tech_skills}
Programming: {prog_skills}
Tools & Soft Skills: {tools} | {soft_skills}

Career Roadmap Steps:
{roadmap_steps_text}

Entrance Exams:
{exams_text}

Career Growth & Future Scope:
{growth}
{scope}"""

        metadata = clean_dict_metadata({
            "career_id": career_id,
            "career_name": career_name,
            "category": category,
            "eligible_after": eligible,
            "stream": stream,
            "min_qualification": min_qual,
            "future_demand": future_demand,
            "ai_impact": ai_impact,
            "text": text_content
        })
        
        texts.append(text_content)
        metadata_list.append(metadata)
        ids.append(career_id)
        
    print(f"Generating {len(texts)} embeddings in batch for careers...")
    embeddings = embed_model.encode(texts, batch_size=32, show_progress_bar=True).tolist()
    
    vectors = [(ids[i], embeddings[i], metadata_list[i]) for i in range(len(ids))]
    chunk_and_upsert(vectors, namespace="careers")

# ==========================================
# 2. COLLEGES NAMESPACE
# ==========================================
def process_colleges():
    print("\n--- Processing Colleges ---")
    df = pd.read_excel(excel_path, sheet_name="College")
    texts = []
    metadata_list = []
    ids = []
    
    for idx, row in df.iterrows():
        college_id = clean_val(row.get("College ID"))
        if not college_id:
            college_id = f"COL_{idx}"
            
        college_name = clean_val(row.get("College Name"))
        location = clean_val(row.get("Location"))
        stream = clean_val(row.get("Stream"))
        college_type = clean_val(row.get("Type"))
        courses = clean_val(row.get("Popular Courses"))
        exams = clean_val(row.get("Entrance Exam"))
        
        text_content = f"""College ID: {college_id}
College Name: {college_name}
Location: {location}
Type: {college_type}
Stream: {stream}
Popular Courses: {courses}
Entrance Exams: {exams}"""

        metadata = clean_dict_metadata({
            "college_id": college_id,
            "college_name": college_name,
            "location": location,
            "type": college_type,
            "stream": stream,
            "courses": courses,
            "exams": exams,
            "text": text_content
        })
        
        texts.append(text_content)
        metadata_list.append(metadata)
        ids.append(college_id)
        
    print(f"Generating {len(texts)} embeddings in batch for colleges...")
    embeddings = embed_model.encode(texts, batch_size=32, show_progress_bar=True).tolist()
    
    vectors = [(ids[i], embeddings[i], metadata_list[i]) for i in range(len(ids))]
    chunk_and_upsert(vectors, namespace="colleges")

# ==========================================
# 3. SYLLABUS NAMESPACE
# ==========================================
def process_syllabus():
    print("\n--- Processing Syllabus ---")
    sheets = {
        "Class 10": "Class 10",
        "Class 12 Science": "Class 12 Science",
        "Class 12 Arts and Commerce": "Class 12 Arts and Commerce"
    }
    texts = []
    metadata_list = []
    ids = []
    
    for sheet_name, class_label in sheets.items():
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        for idx, row in df.iterrows():
            chapter_id = clean_val(row.get("Chapter ID"))
            if not chapter_id:
                continue
                
            subject = clean_val(row.get("Subject"))
            chapter_no = clean_val(row.get("Chapter No"))
            chapter_name = clean_val(row.get("Chapter Name"))
            topics = clean_val(row.get("Topics Covered"))
            
            desc_key = "Description" if "Description" in row else "Descriptions"
            desc = clean_val(row.get(desc_key))
            stream = clean_val(row.get("Stream")) if "Stream" in row else ""
            
            text_content = f"""Class/Level: {class_label}
Stream: {stream}
Subject: {subject}
Chapter {chapter_no}: {chapter_name}
Topics Covered: {topics}
Description: {desc}"""

            metadata = clean_dict_metadata({
                "chapter_id": chapter_id,
                "class_level": class_label,
                "stream": stream,
                "subject": subject,
                "chapter_no": chapter_no,
                "chapter_name": chapter_name,
                "topics_covered": topics,
                "text": text_content
            })
            
            texts.append(text_content)
            metadata_list.append(metadata)
            ids.append(chapter_id)
            
    print(f"Generating {len(texts)} embeddings in batch for syllabus...")
    embeddings = embed_model.encode(texts, batch_size=32, show_progress_bar=True).tolist()
    
    vectors = [(ids[i], embeddings[i], metadata_list[i]) for i in range(len(ids))]
    chunk_and_upsert(vectors, namespace="syllabus")

# ==========================================
# 4. FAQS AND QUERY PATTERNS NAMESPACE
# ==========================================
def process_faqs_and_patterns():
    print("\n--- Processing FAQs & Query Patterns ---")
    df_faqs = pd.read_excel(excel_path, sheet_name="FAQs")
    df_patterns = pd.read_excel(excel_path, sheet_name="FAQ_Qurey_Patterns")
    
    faq_map = {}
    texts = []
    metadata_list = []
    ids = []
    
    # Process FAQs
    for idx, row in df_faqs.iterrows():
        faq_id = clean_val(row.get("FAQ_ID"))
        if not faq_id:
            continue
            
        category = clean_val(row.get("Category"))
        sub_category = clean_val(row.get("Sub_Category"))
        intent = clean_val(row.get("Intent"))
        question = clean_val(row.get("Master_Question"))
        answer = clean_val(row.get("Master_Answer"))
        keywords = clean_val(row.get("Keywords"))
        related_career = clean_val(row.get("Related_Career_ID"))
        related_stream = clean_val(row.get("Related_Stream"))
        
        faq_map[faq_id] = {
            "category": category,
            "sub_category": sub_category,
            "intent": intent,
            "question": question,
            "answer": answer,
            "keywords": keywords,
            "related_career_id": related_career,
            "related_stream": related_stream
        }
        
        text_content = f"""FAQ Category: {category} | Sub-Category: {sub_category}
Intent: {intent}
Question: {question}
Answer: {answer}
Keywords: {keywords}"""

        metadata = clean_dict_metadata({
            "faq_id": faq_id,
            "category": category,
            "sub_category": sub_category,
            "intent": intent,
            "question": question,
            "answer": answer,
            "keywords": keywords,
            "related_career_id": related_career,
            "related_stream": related_stream,
            "text": text_content,
            "is_master": "true"
        })
        
        texts.append(text_content)
        metadata_list.append(metadata)
        ids.append(faq_id)

    # Process FAQ Query Patterns
    for idx, row in df_patterns.iterrows():
        pattern_id = clean_val(row.get("Pattern_ID"))
        faq_id = clean_val(row.get("FAQ_ID"))
        pattern = clean_val(row.get("Pattern"))
        language = clean_val(row.get("Language"))
        
        if not pattern_id or not faq_id or not pattern:
            continue
            
        # Match with master FAQ details
        faq_details = faq_map.get(faq_id)
        if not faq_details:
            continue
            
        category = faq_details["category"]
        sub_category = faq_details["sub_category"]
        intent = faq_details["intent"]
        master_question = faq_details["question"]
        master_answer = faq_details["answer"]
        
        text_content = f"""FAQ Category: {category} | Sub-Category: {sub_category}
Intent: {intent}
User Query Variation ({language}): {pattern}
FAQ Question: {master_question}
FAQ Answer: {master_answer}"""

        metadata = clean_dict_metadata({
            "faq_id": faq_id,
            "pattern_id": pattern_id,
            "category": category,
            "sub_category": sub_category,
            "intent": intent,
            "question": master_question,
            "answer": master_answer,
            "pattern": pattern,
            "language": language,
            "text": text_content,
            "is_master": "false"
        })
        
        texts.append(text_content)
        metadata_list.append(metadata)
        ids.append(pattern_id)
        
    print(f"Generating {len(texts)} embeddings in batch for FAQs & Query Patterns...")
    embeddings = embed_model.encode(texts, batch_size=32, show_progress_bar=True).tolist()
    
    vectors = [(ids[i], embeddings[i], metadata_list[i]) for i in range(len(ids))]
    chunk_and_upsert(vectors, namespace="faqs")

# ==========================================
# 5. STREAMS NAMESPACE
# ==========================================
def process_streams():
    print("\n--- Processing Streams ---")
    # Read excel starting from row 1 to skip header title row
    df = pd.read_excel(excel_path, sheet_name="Stream", skiprows=1)
    texts = []
    metadata_list = []
    ids = []
    
    for idx, row in df.iterrows():
        stream_name = clean_val(row.get("Stream"))
        if not stream_name:
            continue
            
        subjects = clean_val(row.get("Core Subjects"))
        suited_for = clean_val(row.get("Best Suited For"))
        edu_options = clean_val(row.get("Higher Education Options"))
        exams = clean_val(row.get("Popular Entrance Exams"))
        scope = clean_val(row.get("Career / Scope"))
        salary = clean_val(row.get("Typical Starting Salary (India, approx.)"))
        
        text_content = f"""Stream Name: {stream_name}
Core Subjects: {subjects}
Best Suited For: {suited_for}
Higher Education Options: {edu_options}
Popular Entrance Exams: {exams}
Career & Scope: {scope}
Typical Starting Salary: {salary}"""

        stream_id = f"STREAM_{idx}"
        metadata = clean_dict_metadata({
            "stream_id": stream_id,
            "stream_name": stream_name,
            "subjects": subjects,
            "suited_for": suited_for,
            "education_options": edu_options,
            "entrance_exams": exams,
            "scope": scope,
            "salary": salary,
            "text": text_content
        })
        
        texts.append(text_content)
        metadata_list.append(metadata)
        ids.append(stream_id)
        
    print(f"Generating {len(texts)} embeddings in batch for streams...")
    embeddings = embed_model.encode(texts, batch_size=32, show_progress_bar=True).tolist()
    
    vectors = [(ids[i], embeddings[i], metadata_list[i]) for i in range(len(ids))]
    chunk_and_upsert(vectors, namespace="streams")

# ==========================================
# 6. CONVERSATIONS NAMESPACE
# ==========================================
def process_conversations():
    print("\n--- Processing Conversations ---")
    df = pd.read_excel(excel_path, sheet_name="Conversation ")
    texts = []
    metadata_list = []
    ids = []
    
    for idx, row in df.iterrows():
        conv_id = clean_val(row.get("conversation_id"))
        if not conv_id:
            conv_id = f"CONV_{idx}"
            
        category = clean_val(row.get("category"))
        intent = clean_val(row.get("intent"))
        q_hindi = clean_val(row.get("question_hindi"))
        q_english = clean_val(row.get("question_english"))
        q_hinglish = clean_val(row.get("question_hinglish"))
        a_hindi = clean_val(row.get("answer_hindi"))
        a_english = clean_val(row.get("answer_english"))
        a_hinglish = clean_val(row.get("answer_hinglish"))
        tags = clean_val(row.get("tags"))
        
        text_content = f"""Conversation Category: {category} | Intent: {intent}
Question (English): {q_english}
Question (Hindi): {q_hindi}
Question (Hinglish): {q_hinglish}
Answer (English): {a_english}
Answer (Hindi): {a_hindi}
Answer (Hinglish): {a_hinglish}
Tags: {tags}"""

        metadata = clean_dict_metadata({
            "conversation_id": conv_id,
            "category": category,
            "intent": intent,
            "q_english": q_english,
            "q_hindi": q_hindi,
            "q_hinglish": q_hinglish,
            "a_english": a_english,
            "a_hindi": a_hindi,
            "a_hinglish": a_hinglish,
            "tags": tags,
            "text": text_content
        })
        
        texts.append(text_content)
        metadata_list.append(metadata)
        ids.append(conv_id)
        
    print(f"Generating {len(texts)} embeddings in batch for conversations...")
    embeddings = embed_model.encode(texts, batch_size=32, show_progress_bar=True).tolist()
    
    vectors = [(ids[i], embeddings[i], metadata_list[i]) for i in range(len(ids))]
    chunk_and_upsert(vectors, namespace="conversations")

if __name__ == "__main__":
    try:
        process_careers()
        process_colleges()
        process_syllabus()
        process_faqs_and_patterns()
        process_streams()
        process_conversations()
        print("\nPinecone Seeding Completed Successfully!")
    except Exception as e:
        print(f"\nSeeding Failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
