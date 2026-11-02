# اقرأ

قالون عن نافع أصلًا، مع مقابلة القراءات والروايات بالألوان، ومصحفٌ لكل رواية. نصوص المجمع وخطوطه.

المكدّس: **PostgreSQL** + **Django** (API) + **React** (Vite/TypeScript).

```
pipeline Python (build_*.py) → data/** و fonts/*
        ↓ python manage.py import_data
   PostgreSQL ← Django (/api/…) ← React (frontend/)
```

## البيانات (المجرى القديم، دون تغيير سوى المسارات)

```
pip install -r requirements.txt
python parse_khilaf.py && python link_khilaf.py && python build_app_data.py
```

يكتب `data/**` و`fonts/`.

## التشغيل المحلي

```
docker compose up -d db                       # PostgreSQL على المنفذ 5440
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
# (facultatif) DATABASE_URL — par défaut : postgres://qiraat:qiraat@localhost:5440/qiraat
python manage.py migrate
python manage.py import_data                  # ~١ دقيقة؛ يستبدل المحتوى كلَّه (idempotent)
python manage.py verify_import                # يقارن ردود الـ API بملفات JSON الأصلية حرفياً
python manage.py runserver 8000               # API + admin + /fonts

cd ../frontend && npm install && npm run dev  # http://localhost:5173 (proxy نحو Django)
```

الإنتاج: `docker compose up --build` (يبني React داخل الصورة ويخدمه Django عبر WhiteNoise)، ثم
`docker compose exec web python manage.py import_data`.

## الـ API (قراءة فقط)

| المسار | المحتوى |
|---|---|
| `/api/meta/` | السور والرواة والروايات والخطوط |
| `/api/suras/<n>/qalun/` | كلمات قالون |
| `/api/suras/<n>/reads/` | طبقة الخلاف الموحَّدة (دون الحقل `bk`) |
| `/api/mushafs/<mushaf>/<n>/` | مصحف رواية مقابَلاً بقالون |
| `/fonts/<file>` | خطوط المجمع |

التفاصيل وقوانين الأمانة العلمية في [CLAUDE.md](CLAUDE.md).
