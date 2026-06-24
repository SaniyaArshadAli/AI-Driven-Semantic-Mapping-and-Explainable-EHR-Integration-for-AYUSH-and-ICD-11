from fastapi import FastAPI
import sqlite3

app = FastAPI(title="AYUSH ↔ ICD EHR Engine")

def get_db():
    return sqlite3.connect("ehr.db", check_same_thread=False)

@app.post("/auto-review")
def auto_review():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE semantic_mapping
        SET status =
            CASE
                WHEN confidence >= 0.85 THEN 'APPROVED'
                WHEN confidence < 0.6 THEN 'REJECTED'
                ELSE 'PENDING'
            END
    """)
    db.commit()
    return {"message": "Auto review complete"}

@app.get("/mappings")
def get_mappings(status: str = "PENDING"):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM semantic_mapping WHERE status=?", (status,))
    return cur.fetchall()

@app.post("/review")
def review(id: int, action: str, reviewer: str):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE semantic_mapping
        SET status=?, reviewed_by=?, reviewed_at=datetime('now')
        WHERE id=?
    """, (action, reviewer, id))
    db.commit()
    return {"message": "Review saved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
