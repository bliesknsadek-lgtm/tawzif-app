-- coding: utf-8 --
import os
import sqlite3
from typing import Optional
from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI(title="منصة التوظيف")

BASE_DIR = os.path.dirname(os.path.abspath(file))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "tawzif.db")

os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS admin_config (
id INTEGER PRIMARY KEY,
username TEXT NOT NULL,
password TEXT NOT NULL
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS applications (
id INTEGER PRIMARY KEY AUTOINCREMENT,
full_name TEXT NOT NULL,
phone TEXT NOT NULL,
email TEXT,
job_title TEXT NOT NULL,
location_preference TEXT NOT NULL,
experience TEXT,
cv_filename TEXT NOT NULL
)
''')
cursor.execute('SELECT COUNT(*) FROM admin_config')
if cursor.fetchone()[0] == 0:
cursor.execute('INSERT INTO admin_config (id, username, password) VALUES (1, ?, ?)', ('admin', 'password123'))
conn.commit()
conn.close()

init_db()

def get_admin_credentials():
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('SELECT username, password FROM admin_config WHERE id = 1')
row = cursor.fetchone()
conn.close()
if row:
return row[0], row[1]
return "admin", "password123"

security = HTTPBasic()

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
current_user, current_pass = get_admin_credentials()
if credentials.username != current_user or credentials.password != current_pass:
raise HTTPException(
status_code=status.HTTP_401_UNAUTHORIZED,
detail="بيانات الدخول غير صحيحة",
headers={"WWW-Authenticate": "Basic"},
)
return credentials.username

@app.get("/", response_class=HTMLResponse)
async def read_form():
return """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>تقديم طلب توظيف</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
<style>
body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); font-family: sans-serif; min-height: 100vh; padding: 20px 0; }
.card { border: none; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); background: #ffffff; }
.card-header { background: linear-gradient(to right, #2a5298, #1e3c72); color: white; border-top-left-radius: 20px !important; border-top-right-radius: 20px !important; text-align: center; padding: 25px; }
.btn-primary { background: #1e3c72; border: none; border-radius: 12px; padding: 12px; font-weight: bold; }
.btn-primary:hover { background: #2a5298; }
.form-control, .form-select { border-radius: 10px; padding: 12px; }
</style>
</head>
<body>
<div class="container">
<div class="row justify-content-center">
<div class="col-md-8 col-lg-6">
<div class="card my-3">
<div class="card-header">
<h3 class="mb-0">استمارة تقديم طلب توظيف</h3>
<p class="text-light mb-0 mt-2 small">يرجى تعبئة كافة البيانات بدقة</p>
</div>
<div class="card-body p-4">
<form action="/submit" method="post" enctype="multipart/form-data">
<div class="mb-3">
<label class="form-label fw-bold">الاسم الكامل *</label>
<input type="text" name="full_name" class="form-control" placeholder="أدخل اسمك الثلاثي" required>
</div>
<div class="mb-3">
<label class="form-label fw-bold">رقم الهاتف *</label>
<input type="tel" name="phone" class="form-control" placeholder="03123456" required>
</div>
<div class="mb-3">
<label class="form-label fw-bold">البريد الإلكتروني</label>
<input type="email" name="email" class="form-control" placeholder="example@domain.com">
</div>
<div class="mb-3">
<label class="form-label fw-bold">الوظيفة المطلوبة *</label>
<input type="text" name="job_title" class="form-control" placeholder="مثال: فني تبريد، محاسب..." required>
</div>
<div class="mb-3">
<label class="form-label fw-bold">مكان العمل المفضل *</label>
<select name="location_preference" class="form-select" required>
<option value="" disabled selected>اختر مكان العمل المفضل</option>
<option value="بيروت">بيروت</option>
<option value="الشوف">الشوف</option>
<option value="البقاع">البقاع</option>
<option value="طرابلس">طرابلس</option>
<option value="صيدا">صيدا</option>
<option value="عن بُعد">عن بُعد (Online)</option>
</select>
</div>
<div class="mb-3">
<label class="form-label fw-bold">نبذة مختصرة عن الخبرات والمهارات</label>
<textarea name="experience" class="form-control" rows="3" placeholder="اشرح بسطرين عن خبرتك السابقة..."></textarea>
</div>
<div class="mb-4">
<label class="form-label fw-bold">رفع السيرة الذاتية (CV) *</label>
<input type="file" name="cv_file" class="form-control" accept=".pdf,.doc,.docx,.png,.jpg" required>
</div>
<button type="submit" class="btn btn-primary w-100 fs-5">إرسال الطلب</button>
</form>
</div>
</div>
</div>
</div>
</div>
</body>
</html>
"""

@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
full_name: str = Form(...),
phone: str = Form(...),
email: Optional[str] = Form(None),
job_title: str = Form(...),
location_preference: str = Form(...),
experience: Optional[str] = Form(""),
cv_file: UploadFile = File(...)
):
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

filename = f"{cv_file.filename}"
file_path = os.path.join(UPLOAD_DIR, filename)
with open(file_path, "wb") as buffer:
buffer.write(await cv_file.read())

cursor.execute('''
INSERT INTO applications (full_name, phone, email, job_title, location_preference, experience, cv_filename)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', (full_name, phone, email, job_title, location_preference, experience, filename))

conn.commit()
conn.close()

return """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
<style>body { background: #f5f7fa; text-align: center; padding-top: 100px; font-family: sans-serif; }</style>
</head>
<body>
<div class="container">
<div class="card p-5 shadow-sm d-inline-block" style="max-width: 500px; border-radius: 20px;">
<h2 class="text-success mb-3">✓ تم إرسال طلبك بنجاح!</h2>
<p class="fs-5 text-muted">شكرًا لتقديمك، سنتواصل معك قريباً.</p>
<a href="/" class="btn btn-primary mt-3 px-4">تقديم طلب آخر</a>
</div>
</div>
</body>
</html>
"""

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(admin: str = Depends(authenticate_admin)):
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('SELECT id, full_name, phone, email, job_title, location_preference, experience, cv_filename FROM applications')
apps = cursor.fetchall()
conn.close()

cards = ""
for app in apps:
cards += f"""
<div class="card mb-3 p-3 bg-dark text-white border-secondary">
<div class="d-flex justify-content-between align-items-center mb-2">
<h5 class="mb-0 text-warning">{app[1]}</h5>
<span class="badge bg-info">{app[4]}</span>
</div>
<p class="mb-1"><strong>الهاتف:</strong> <a href="tel:{app[2]}" class="text-light">{app[2]}</a></p>
<p class="mb-1"><strong>البريد:</strong> {app[3] or 'غير محدد'}</p>
<p class="mb-1"><strong>المكان المفضل:</strong> {app[5]}</p>
<p class="mb-2"><small><strong>الخبرة:</strong> {app[6] or 'لا يوجد'}</small></p>
<div class="d-flex gap-2 mt-2">
<a href="/uploads/{app[7]}" target="_blank" class="btn btn-sm btn-primary flex-fill">📄 عرض السيرة الذاتية</a>
<a href="/admin/delete/{app[0]}" class="btn btn-sm btn-danger flex-fill" onclick="return confirm('هل أنت متأكد من حذف هذا الطلب؟')">🗑️ حذف</a>
</div>
</div>
"""

return f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>لوحة تحكم المدير</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
<style>
body {{ background: #1a1a2e; color: #fff; font-family: sans-serif; padding: 15px; }}
.card {{ background: #16213e; border-radius: 15px; }}
</style>
</head>
<body>
<div class="container-fluid">
<div class="d-flex justify-content-between align-items-center mb-3">
<h3 class="mb-0">📊 لوحة الأدمن</h3>
<span class="badge bg-primary fs-6">الطلبات: {len(apps)}</span>
</div>

<!-- قسم تعديل كلمة السر والمستخدم مخصص للهاتف -->
<div class="card p-3 mb-4 border-warning">
<h5 class="text-warning mb-3">⚙️ تغيير بيانات دخول الأدمن</h5>
<form action="/admin/change-credentials" method="post">
<div class="mb-2">
<input type="text" name="new_username" class="form-control bg-dark text-white border-secondary" required placeholder="اسم المستخدم الجديد">
</div>
<div class="mb-3">
<input type="password" name="new_password" class="form-control bg-dark text-white border-secondary" required placeholder="كلمة السر الجديدة">
</div>
<button type="submit" class="btn btn-warning w-100 fw-bold">حفظ البيانات الجديدة</button>
</form>
</div>

<h4 class="mb-3">📋 المتقدمون للوظائف</h4>
{cards if cards else '<div class="alert alert-secondary text-center">لا توجد طلبات مقدمة حالياً.</div>'}
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@app.get("/uploads/{filename}")
async def get_upload(filename: str, admin: str = Depends(authenticate_admin)):
file_path = os.path.join(UPLOAD_DIR, filename)
if os.path.exists(file_path):
return FileResponse(file_path)
raise HTTPException(status_code=404, detail="الملف غير موجود")

@app.get("/admin/delete/{app_id}")
async def delete_application(app_id: int, admin: str = Depends(authenticate_admin)):
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('DELETE FROM applications WHERE id = ?', (app_id,))
conn.commit()
conn.close()
return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/change-credentials")
async def change_credentials(
new_username: str = Form(...),
new_password: str = Form(...),
admin: str = Depends(authenticate_admin)
):
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('UPDATE admin_config SET username = ?, password = ? WHERE id = 1', (new_username, new_password))
conn.commit()
conn.close()
return HTMLResponse("""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-dark text-white text-center p-5">
<div class="container mt-5">
<h3 class="text-success mb-3">✓ تم تغيير بيانات الدخول بنجاح!</h3>
<p>يرجى تسجيل الدخول بالاسم وكلمة المرور الجديدة.</p>
<a href="/admin" class="btn btn-warning mt-3 px-4">الذهاب لوحة التحكم</a>
</div>
</body>
</html>
""")