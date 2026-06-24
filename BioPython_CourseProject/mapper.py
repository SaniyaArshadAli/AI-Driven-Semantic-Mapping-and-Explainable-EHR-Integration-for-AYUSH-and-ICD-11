import pandas as pd
import json
import time
import re
from tqdm import tqdm
from google import genai

# ==============================
# CONFIG — CHANGE ONLY PATHS + KEY
# ==============================
API_KEY = "AIzaSyC9CVXB90kaerFwPMHAoY-Kmp03i8rsCFM"

AYUSH_CSV = r"C:\Users\saniy\OneDrive\Desktop\BioPython_CourseProject\ayush_terms.csv"
ICD_CSV   = r"C:\Users\saniy\OneDrive\Desktop\BioPython_CourseProject\icd11_terms.csv"
OUTPUT_CSV = r"C:\Users\saniy\OneDrive\Desktop\BioPython_CourseProject\semantic_mapping.csv"

MODEL_NAME = "gemini-2.5-flash"
SLEEP_SECONDS = 1
ICD_SAMPLE_SIZE = 25

# ==============================
# INIT GEMINI (NEW SDK)
# ==============================
client = genai.Client(api_key=API_KEY)

# ==============================
# LOAD CSVs SAFELY
# ==============================
ayush_df = pd.read_csv(
    AYUSH_CSV,
    engine="python",
    on_bad_lines="skip"
)

icd_df = pd.read_csv(
    ICD_CSV,
    engine="python",
    on_bad_lines="skip"
)

print(f"AYUSH rows loaded: {len(ayush_df)}")
print(f"ICD rows loaded: {len(icd_df)}")

# ==============================
# MAIN LOOP
# ==============================
results = []

for _, row in tqdm(ayush_df.iterrows(), total=len(ayush_df)):

    ayush_term = str(row["ayush_term"])
    ayush_desc = str(row["description"])

    icd_context = icd_df.sample(ICD_SAMPLE_SIZE)[
        ["icd11_term", "description"]
    ].to_string(index=False)

    prompt = f"""
You are a medical terminology expert.

Map the AYUSH disease to the MOST SEMANTICALLY SIMILAR ICD-11 disease.

AYUSH:
Name: {ayush_term}
Description: {ayush_desc}

ICD OPTIONS:
{icd_context}

Return ONLY JSON:
{{
  "icd11_term": "",
  "confidence": 0.0,
  "reason": ""
}}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        # 🔥 THIS IS THE FIX — DO NOT CHANGE
        raw_text = response.text

        # Clean markdown if present
        raw_text = re.sub(r"```json|```", "", raw_text).strip()

        # Extract JSON safely
        json_start = raw_text.find("{")
        json_end = raw_text.rfind("}") + 1
        mapping = json.loads(raw_text[json_start:json_end])

        results.append({
            "ayush_term": ayush_term,
            "ayush_description": ayush_desc,
            "icd11_term": mapping.get("icd11_term", ""),
            "confidence": float(mapping.get("confidence", 0)),
            "reason": mapping.get("reason", "")
        })

        print(f"✔ {ayush_term} → {mapping.get('icd11_term','')}")

    except Exception as e:
        print(f"❌ FAILED {ayush_term}: {e}")

    time.sleep(SLEEP_SECONDS)

# ==============================
# SAVE OUTPUT
# ==============================
if not results:
    raise RuntimeError("NO MAPPINGS GENERATED — CHECK GEMINI OUTPUT")

pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)

print("\n✅ semantic_mapping.csv CREATED")
print(f"📁 Location: {OUTPUT_CSV}")
print(f"📊 Rows written: {len(results)}")
