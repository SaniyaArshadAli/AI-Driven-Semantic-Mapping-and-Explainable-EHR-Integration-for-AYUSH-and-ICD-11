import sqlite3
conn = sqlite3.connect("C:\\Users\\saniy\\OneDrive\\Desktop\\BioPython_CourseProject\\ehr.db")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM semantic_mapping")
print(cur.fetchone())
conn.close()
