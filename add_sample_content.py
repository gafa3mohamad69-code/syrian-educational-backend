import sqlite3

conn = sqlite3.connect('syria_edu.db')
cursor = conn.cursor()

# محتوى تجريبي
sample_content = [
    ('كتاب الرياضيات - الصف التاسع', 'شرح شامل لمنهج الرياضيات للصف التاسع مع أمثلة وتمارين', 'book', 'إعدادي', 'رياضيات', 1),
    ('محاضرة الفيزياء - الحركة', 'محاضرة مفصلة عن قوانين الحركة ونيوتن', 'lecture', 'ثانوي', 'فيزياء', 1),
    ('ملخص الكيمياء العضوية', 'ملخص شامل للكيمياء العضوية للثانوية العامة', 'note', 'ثانوي', 'كيمياء', 1),
    ('كتاب اللغة العربية', 'كتاب شامل لقواعد اللغة العربية', 'book', 'إعدادي', 'عربي', 1),
    ('محاضرة التاريخ الإسلامي', 'تاريخ الدولة الأموية', 'lecture', 'ثانوي', 'تاريخ', 1),
]

for title, desc, ctype, stage, subject, uploader in sample_content:
    try:
        cursor.execute('''
            INSERT INTO content (title, description, content_type, stage, subject, uploader_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, desc, ctype, stage, subject, uploader))
    except:
        pass  # تجاهل إذا كان موجود مسبقاً

conn.commit()
conn.close()
print("✅ تم إضافة المحتوى التجريبي!")
