#!/bin/bash
# سكريبت سريع لحفظ التعديلات على GitHub

git add .
echo "✅ تم إضافة الملفات"

read -p "✏️ اكتب رسالة commit: " msg
git commit -m "$msg"
echo "✅ تم عمل commit"

git push origin main
echo "🚀 تم رفع التغييرات على GitHub"
