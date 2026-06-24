import sqlite3

DB = "ehr.db"

def get_db():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    db = get_db()
    with open("C:\\Users\\saniy\\OneDrive\\Desktop\\BioPython_CourseProject\\models.sql") as f:
        db.executescript(f.read())
    db.commit()
    db.close()
if __name__ == "__main__":
    init_db()
    print("✅ Database initialized")
    print(f"📁 Location: {DB}")