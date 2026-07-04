# PrivyAlgo Blog — Portable Deployment

100% open-source stack — no proprietary/closed-source dependencies. Deployable to GitHub Codespaces, VPS (Ubuntu/Debian), Docker, Render, Railway, Fly.io, etc.

## Stack

**Backend**
- FastAPI + Uvicorn
- MongoDB (via `motor` async driver)
- JWT (PyJWT) + bcrypt (passlib) — email/password auth
- Authlib — Google OAuth 2.0 (optional)
- Local filesystem for image storage
- SMTP (stdlib) for password reset emails (optional)

**Frontend**
- React 19 + React Router 7
- Tailwind CSS + shadcn/ui
- Tiptap 3 (WYSIWYG editor + YouTube embed)
- JWT stored in `localStorage`, sent via Axios `Authorization: Bearer` header

## Environment Variables

### `backend/.env`
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="privyalgo_blog"
CORS_ORIGINS="*"

# JWT secret — REPLACE with a strong random string in production
JWT_SECRET="<generate-with-openssl-rand-hex-32>"

# Frontend URL — used for password reset & OAuth redirects
FRONTEND_URL="https://your-domain.com"

# Local upload directory (must be writable)
UPLOAD_DIR="/app/backend/uploads"

# Google OAuth (leave empty to disable "Sign in with Google" button)
GOOGLE_CLIENT_ID=""
GOOGLE_CLIENT_SECRET=""
GOOGLE_REDIRECT_URI="https://your-domain.com/api/auth/google/callback"

# SMTP for password reset (leave empty to log link to console in dev)
SMTP_HOST=""
SMTP_PORT="587"
SMTP_USER=""
SMTP_PASSWORD=""
SMTP_FROM=""
```

### `frontend/.env`
```env
REACT_APP_BACKEND_URL="https://your-domain.com"
```

## Super Admin

On first startup, backend seeds a super admin:

- **Email**: `nfinansarastirma@gmail.com`
- **Initial password**: `Admin123!`
- **must_change_password**: `true` (user will see a warning in Dashboard → Profil/Şifre)

The super admin cannot be deleted or demoted via the admin panel.

## Google OAuth Setup

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (type: Web application)
3. Add authorized redirect URI: `https://your-domain.com/api/auth/google/callback`
4. Copy Client ID and Client Secret into `backend/.env`
5. Restart backend — the Google button appears on `/login` automatically

## Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend (separate terminal)
cd frontend
yarn install
yarn start
```

## Docker (production hint)

```dockerfile
# Backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

## Data Model

- `users` — {user_id, email, password_hash, name, picture, role, bio, education_access, must_change_password, provider, created_at}
- `articles` — {id, title, slug, excerpt, content_html, cover_image, category_slug, category_slugs, category_names, tags, author_id, status, featured, views, ...}
- `categories` — {id, name, slug, description, color}
- `education_members` — {id, email, note, added_at}
- `files` — {id, storage_path, original_filename, content_type, size, uploaded_by, created_at}

## Roles

- `admin` — full CMS access, publish articles, manage users & categories & education members
- `user` — read-only public + can create drafts (needs admin approval to publish)

## Endpoints Summary

**Auth**
- `POST /api/auth/register` `{email, password, name}` → `{access_token, user}`
- `POST /api/auth/login` `{email, password}` → `{access_token, user}`
- `POST /api/auth/forgot-password` `{email}` → sends reset link (or logs in dev)
- `POST /api/auth/reset-password` `{token, new_password}`
- `POST /api/auth/change-password` `{current_password, new_password}` (auth required)
- `PATCH /api/auth/profile` `{name?, bio?}` (auth required)
- `GET /api/auth/me` (auth required)
- `GET /api/auth/google/status` → `{enabled: bool}`
- `GET /api/auth/google/login` → redirect to Google
- `GET /api/auth/google/callback` → redirect to `${FRONTEND_URL}/auth/callback?token=...`

**Content (public)**
- `GET /api/categories`
- `GET /api/articles?category=&tag=&q=&featured=&limit=&skip=`
- `GET /api/articles/{slug}`
- `GET /api/articles/{slug}/related`

**Authoring (auth required)**
- `GET /api/my/articles`
- `POST /api/articles`, `PATCH /api/articles/{id}`, `DELETE /api/articles/{id}`
- `POST /api/upload` (image, max 8MB, jpg/png/webp/gif)
- `GET /api/files/{path}` (public serving of uploaded images)

**Admin (admin role required)**
- `GET /api/admin/users`
- `PATCH /api/admin/users/{user_id}/role?role=admin|user`
- `DELETE /api/admin/users/{user_id}`
- `PATCH /api/admin/users/{user_id}/education?enabled=true|false`
- `POST /api/admin/categories`, `DELETE /api/admin/categories/{id}`
- `GET /api/admin/education-members`
- `POST /api/admin/education-members`, `DELETE /api/admin/education-members/{id}`
