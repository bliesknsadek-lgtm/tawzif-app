# -*- coding: utf-8 -*-
import os
import uuid
import sqlite3
from typing import Optional
from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jinja2 import Template

APP_NAME = "منصة التوظيف"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "tawzif.db")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title=APP_NAME)
security = HTTPBasic()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            job_title TEXT NOT NULL,
            work_location TEXT NOT NULL,
            experience TEXT,
            cv_filename TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = "admin"
    correct_password = "admin123"
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="بيانات الدخول غير صحيحة",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

HTML_FORM = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقديم طلب توظيف</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; font-family: system-ui, -apple-system, sans-serif; }
        .card { border-radius: 15px; border: none; }
        .btn-primary { background-color: #0d6efd; border: none; padding: 12px; font-weight: bold; }
    </style>
</head>
<body class="py-4 py-md-5">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-12 col-md-8 col-lg-6">
                <div class="card shadow-sm p-4">
                    <h3 class="text-center mb-4 text-primary">استمارة تقديم طلب توظيف</h3>
                    {% if success %}
                    <div class="alert alert-success text-center mb-4">
                        تم تقديم طلبك بنجاح! سنقوم براجعته والتواصل معك قريباً.
                    </div>
                    {% endif %}
                    <form action="/apply" method="post" enctype="multipart/form-data">
                        <div class="mb-3">
                            <label class="form-label font-weight-bold">الاسم الكامل *</label>
                            <input type="text" name="full_name" class="form-control" placeholder="أدخل اسمك الثلاثي" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">رقم الهاتف *</label>
                            <input type="tel" name="phone" class="form-control" placeholder="03123456" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">البريد الإلكتروني</label>
                            <input type="email" name="email" class="form-control" placeholder="example@domain.com">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">الوظيفة المطلوبة *</label>
                            <input type="text" name="job_title" class="form-control" placeholder="مثال: فني تبريد، محاسب، مبيعات..." required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">تفصيل تفضيل مكان العمل *</label>
                            <select name="work_location" class="form-select" required>
                                <option value="" disabled selected>اختر مكان العمل المفضّل</option>
                                <option value="داخل لبنان">داخل لبنان</option>
                                <option value="خارج لبنان (سفر)">خارج لبنان (سفر)</option>
                                <option value="كلاهما (لا مانع من السفر)">كلاهما (لا مانع من السفر)</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">نبذة مختصرة عن الخبرات والمهارات</label>
                            <textarea name="experience" class="form-control" rows="3" placeholder="اشرح بسطرين عن خبرتك السابقة..."></textarea>
                        </div>
                        <div class="mb-4">
                            <label class="form-label">رفع السيرة الذاتية (CV) *</label>
                            <input type="file" name="cv_file" class="form-control" accept=".pdf,.doc,.docx" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">إرسال الطلب</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

HTML_ADMIN = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم - طلبات التوظيف</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; font-family: system-ui, -apple-system, sans-serif; }
        .job-header { background-color: #0d6efd; color: white; border-radius: 8px; padding: 10px 15px; }
        .table { background: white; border-radius: 8px; overflow: hidden; }
    </style>
</head>
<body class="py-4">
    <div class="container-fluid px-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>لوحة إدارة المتقدمين للوظائف</h2>
            <span class="badge bg-secondary p-2">المسؤول: {{ username }}</span>
        </div>

        {% if not grouped_applicants %}
        <div class="alert alert-info text-center">لا يوجد أي طلبات توظيف مقدمة حتى الآن.</div>
        {% endif %}

        {% for job_title, candidates in grouped_applicants.items() %}
        <div class="mb-5">
            <div class="job-header d-flex justify-content-between align-items-center mb-3">
                <h4 class="m-0">الوظيفة: {{ job_title }}</h4>
                <span class="badge bg-light text-dark">{{ candidates|length }} متقدمين</span>
            </div>
            <div class="table-responsive shadow-sm">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-dark">
                        <tr>
                            <th>الاسم الكامل</th>
                            <th>رقم الهاتف</th>
                            <th>البريد الإلكتروني</th>
                            <th>مكان العمل المفصل</th>
                            <th>نبذة الخبرة</th>
                            <th>السيرة الذاتية</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for c in candidates %}
                        <tr>
                            <td class="fw-bold">{{ c.full_name }}</td>
                            <td><a href="tel:{{ c.phone }}" class="text-decoration-none">{{ c.phone }}</a></td>
                            <td>{{ c.email if c.email else '-' }}</td>
                            <td><span class="badge bg-info text-dark">{{ c.work_location }}</span></td>
                            <td><small>{{ c.experience if c.experience else '-' }}</small></td>
                            <td>
                                <a href="/uploads/{{ c.cv_filename }}" target="_blank" class="btn btn-sm btn-outline-primary">عرض / تحميل CV</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def form_page(success: bool = False):
    template = Template(HTML_FORM)
    return template.render(success=success)

@app.post("/apply", response_class=HTMLResponse)
async def apply_job(
    full_name: str = Form(...),
    phone: str = Form(...),
    email: Optional[str] = Form(""),
    job_title: str = Form(...),
    work_location: str = Form(...),
    experience: Optional[str] = Form(""),
    cv_file: UploadFile = File(...)
):
    ext = cv_file.filename.split(".")[-1] if "." in cv_file.filename else "pdf"
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(await cv_file.read())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO candidates (full_name, phone, email, job_title, work_location, experience, cv_filename)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (full_name, phone, email, job_title, work_location, experience, unique_filename))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/?success=True", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(username: str = Depends(verify_admin)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, phone, email, job_title, work_location, experience, cv_filename FROM candidates ORDER BY job_title ASC, id DESC")
    rows = cursor.fetchall()
    conn.close()

    grouped_applicants = {}
    for r in rows:
        job = r[4]
        applicant = {
            "id": r[0],
            "full_name": r[1],
            "phone": r[2],
            "email": r[3],
            "work_location": r[5],
            "experience": r[6],
            "cv_filename": r[7]
        }
        if job not in grouped_applicants:
            grouped_applicants[job] = []
        grouped_applicants[job].append(applicant)

    template = Template(HTML_ADMIN)
    return template.render(grouped_applicants=grouped_applicants, username=username)

@app.get("/uploads/{filename}")
async def get_cv_file(filename: str, username: str = Depends(verify_admin)):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="الملف غير موجود")
