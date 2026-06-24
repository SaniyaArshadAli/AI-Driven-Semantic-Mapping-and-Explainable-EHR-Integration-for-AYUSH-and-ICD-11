import sqlite3
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "C:\\Users\\saniy\\OneDrive\\Desktop\\BioPython_CourseProject\\ehr.db")
CSV_PATH = os.path.join(BASE_DIR, "C:\\Users\\saniy\\OneDrive\\Desktop\\BioPython_CourseProject\\semantic_mapping.csv")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

with open(CSV_PATH, newline='', encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute("""
            INSERT INTO semantic_mapping (
                ayush_term,
                ayush_description,
                icd11_term,
                confidence,
                reason,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row["ayush_term"],
            row["ayush_description"],
            row["icd11_term"],
            float(row["confidence"]),
            row["reason"],
            "PENDING"
        ))

conn.commit()
conn.close()

print("✅ Data loaded successfully")
