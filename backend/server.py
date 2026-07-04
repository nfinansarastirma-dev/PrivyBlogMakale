"""
PrivyAlgo Blog — Portable Backend API
FastAPI + MongoDB + JWT + bcrypt + Authlib (Google OAuth) + Local file storage
No proprietary/closed-source dependencies.
"""
import os
import re
import uuid
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import jwt
from bson import ObjectId
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi import (
    FastAPI, APIRouter, HTTPException, Header, Response,
    UploadFile, File, Form, Query, Request, Depends
)
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from authlib.integrations.starlette_client import OAuth


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

APP_NAME = "privyalgo-blog"
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production-please")
JWT_ALGO = "HS256"
JWT_EXPIRE_DAYS = 7
RESET_TOKEN_EXPIRE_MINUTES = 60

# Super admin bootstrap
SUPER_ADMIN_EMAIL = "nfinansarastirma@gmail.com"
SUPER_ADMIN_INITIAL_PASSWORD = "Admin123!"

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", str(ROOT_DIR / "uploads")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# SMTP for password reset (falls back to log if not configured)
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER or "no-reply@privyalgo.blog")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="PrivyAlgo Blog API")
api_router = APIRouter(prefix="/api")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Auth utilities
# ---------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(pw, hashed)
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def create_reset_token(email: str) -> str:
    payload = {
        "sub": email,
        "type": "reset",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def slugify(s: str) -> str:
    s = s.lower().strip()
    tr = str.maketrans("çğıöşüâîû", "cgiosuaiu")
    s = s.translate(tr)
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s or uuid.uuid4().hex[:8]


def compute_reading_minutes(html: str) -> int:
    text = re.sub(r"<[^>]+>", " ", html or "")
    words = len(text.split())
    return max(1, round(words / 200))


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = ""
    role: str = "user"  # "admin" | "user"
    bio: Optional[str] = ""
    education_access: bool = False
    must_change_password: bool = False
    provider: str = "local"  # "local" | "google"
    created_at: str


class UserPublic(BaseModel):
    """User payload for responses (no password_hash)."""
    user_id: str
    email: str
    name: str
    picture: Optional[str] = ""
    role: str = "user"
    bio: Optional[str] = ""
    education_access: bool = False
    must_change_password: bool = False
    provider: str = "local"
    created_at: str


class RegisterPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordPayload(BaseModel):
    email: EmailStr


class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordPayload(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UpdateProfilePayload(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None


class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    description: Optional[str] = ""
    color: Optional[str] = "#F59E0B"


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "#F59E0B"


class Article(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    excerpt: str = ""
    content_html: str = ""
    cover_image: Optional[str] = ""
    category_slug: str
    category_name: str
    category_slugs: List[str] = []
    category_names: List[str] = []
    tags: List[str] = []
    author_id: str
    author_name: str
    author_picture: Optional[str] = ""
    status: str = "draft"
    featured: bool = False
    views: int = 0
    reading_minutes: int = 3
    created_at: str
    updated_at: str
    published_at: Optional[str] = None


class ArticleCreate(BaseModel):
    title: str
    excerpt: Optional[str] = ""
    content_html: str = ""
    cover_image: Optional[str] = ""
    category_slug: Optional[str] = None
    category_slugs: Optional[List[str]] = None
    tags: List[str] = []
    status: str = "draft"
    featured: Optional[bool] = False


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    excerpt: Optional[str] = None
    content_html: Optional[str] = None
    cover_image: Optional[str] = None
    category_slug: Optional[str] = None
    category_slugs: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    featured: Optional[bool] = None


class EducationMemberCreate(BaseModel):
    email: EmailStr
    note: Optional[str] = ""


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------
async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[User]:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    user_doc = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user_doc:
        return None
    return User(**user_doc)


async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    user = await get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ---------------------------------------------------------------------------
# Email helper
# ---------------------------------------------------------------------------
def send_email(to: str, subject: str, body_html: str) -> bool:
    if not SMTP_HOST or not SMTP_USER:
        logger.warning(f"[SMTP not configured] Would send to {to}: {subject}\n{body_html}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD or "")
            server.sendmail(SMTP_FROM, [to], msg.as_string())
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"SMTP error sending to {to}: {e}")
        return False


# ---------------------------------------------------------------------------
# Google OAuth (Authlib)
# ---------------------------------------------------------------------------
oauth = OAuth()
if os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"):
    oauth.register(
        name="google",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    GOOGLE_ENABLED = True
    logger.info("Google OAuth configured")
else:
    GOOGLE_ENABLED = False
    logger.warning("Google OAuth not configured (missing GOOGLE_CLIENT_ID/SECRET) — button will be disabled")


# ---------------------------------------------------------------------------
# Auth Routes — Email/Password
# ---------------------------------------------------------------------------
def _sanitize_user(doc: dict) -> dict:
    doc.pop("_id", None)
    doc.pop("password_hash", None)
    return doc


async def _create_user(email: str, name: str, password: Optional[str], provider: str = "local", picture: str = "") -> dict:
    email = email.lower().strip()
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    is_edu_member = await db.education_members.find_one({"email": email}, {"_id": 0}) is not None
    doc = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "picture": picture,
        "role": "admin" if email == SUPER_ADMIN_EMAIL else "user",
        "bio": "",
        "education_access": is_edu_member,
        "must_change_password": False,
        "provider": provider,
        "password_hash": hash_password(password) if password else "",
        "created_at": now_iso(),
    }
    await db.users.insert_one(doc)
    return _sanitize_user(dict(doc))


@api_router.post("/auth/register")
async def register(payload: RegisterPayload):
    email = payload.email.lower().strip()
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı")
    user_doc = await _create_user(email, payload.name, payload.password, provider="local")
    token = create_access_token(user_doc["user_id"], email)
    return {"access_token": token, "token_type": "bearer", "user": user_doc}


@api_router.post("/auth/login")
async def login(payload: LoginPayload):
    email = payload.email.lower().strip()
    user_doc = await db.users.find_one({"email": email})
    if not user_doc or not user_doc.get("password_hash"):
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")
    if not verify_password(payload.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")
    # Sync education access
    is_edu_member = await db.education_members.find_one({"email": email}, {"_id": 0}) is not None
    if bool(user_doc.get("education_access")) != is_edu_member:
        await db.users.update_one({"user_id": user_doc["user_id"]}, {"$set": {"education_access": is_edu_member}})
        user_doc["education_access"] = is_edu_member
    token = create_access_token(user_doc["user_id"], email)
    return {"access_token": token, "token_type": "bearer", "user": _sanitize_user(user_doc)}


@api_router.get("/auth/me")
async def me(user: User = Depends(get_current_user)):
    return user.model_dump()


@api_router.post("/auth/logout")
async def logout():
    # JWT is stateless — client just discards the token.
    return {"ok": True}


@api_router.post("/auth/forgot-password")
async def forgot_password(payload: ForgotPasswordPayload):
    email = payload.email.lower().strip()
    user_doc = await db.users.find_one({"email": email}, {"_id": 0})
    if not user_doc:
        # Don't reveal whether email exists
        return {"ok": True}
    token = create_reset_token(email)
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    body = f"""
    <h2>PrivyAlgo Blog — Şifre Sıfırlama</h2>
    <p>Merhaba {user_doc.get('name', '')},</p>
    <p>Şifrenizi sıfırlamak için aşağıdaki linke tıklayın (60 dakika geçerli):</p>
    <p><a href="{reset_url}" style="background:#F59E0B;color:#000;padding:10px 20px;text-decoration:none;font-weight:bold">Şifreyi Sıfırla</a></p>
    <p>Ya da tarayıcınıza yapıştırın:<br><code>{reset_url}</code></p>
    <p>Bu isteği siz yapmadıysanız bu mesajı görmezden gelin.</p>
    <p>— PrivyAlgo · nFinans</p>
    """
    sent = send_email(email, "PrivyAlgo — Şifre Sıfırlama", body)
    result = {"ok": True}
    if not sent:
        # Dev mode: return reset URL for local testing
        result["dev_reset_url"] = reset_url
    return result


@api_router.post("/auth/reset-password")
async def reset_password(payload: ResetPasswordPayload):
    decoded = decode_token(payload.token)
    if not decoded or decoded.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş token")
    email = decoded["sub"]
    user_doc = await db.users.find_one({"email": email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=400, detail="Kullanıcı bulunamadı")
    await db.users.update_one(
        {"email": email},
        {"$set": {"password_hash": hash_password(payload.new_password), "must_change_password": False}},
    )
    return {"ok": True}


@api_router.post("/auth/change-password")
async def change_password(payload: ChangePasswordPayload, user: User = Depends(get_current_user)):
    user_doc = await db.users.find_one({"user_id": user.user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    if not user_doc.get("password_hash") or not verify_password(payload.current_password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Mevcut şifre hatalı")
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"password_hash": hash_password(payload.new_password), "must_change_password": False}},
    )
    return {"ok": True}


@api_router.patch("/auth/profile")
async def update_profile(payload: UpdateProfilePayload, user: User = Depends(get_current_user)):
    updates = {}
    if payload.name is not None:
        updates["name"] = payload.name.strip()[:100]
    if payload.bio is not None:
        updates["bio"] = payload.bio.strip()[:500]
    if updates:
        await db.users.update_one({"user_id": user.user_id}, {"$set": updates})
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    return user_doc


# ---------------------------------------------------------------------------
# Auth Routes — Google OAuth (Authlib)
# ---------------------------------------------------------------------------
@api_router.get("/auth/google/status")
async def google_status():
    return {"enabled": GOOGLE_ENABLED}


@api_router.get("/auth/google/login")
async def google_login(request: Request):
    if not GOOGLE_ENABLED:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured on this server")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI") or str(request.url_for("google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@api_router.get("/auth/google/callback", name="google_callback")
async def google_callback(request: Request):
    if not GOOGLE_ENABLED:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        return RedirectResponse(f"{FRONTEND_URL}/login?error=google_auth_failed")

    userinfo = token.get("userinfo") or {}
    if not userinfo:
        try:
            resp = await oauth.google.get("userinfo", token=token)
            userinfo = resp.json()
        except Exception:
            userinfo = {}

    email = (userinfo.get("email") or "").lower().strip()
    if not email:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=google_no_email")

    name = userinfo.get("name") or email.split("@")[0]
    picture = userinfo.get("picture") or ""

    user_doc = await db.users.find_one({"email": email})
    if user_doc:
        await db.users.update_one(
            {"user_id": user_doc["user_id"]},
            {"$set": {"name": name, "picture": picture, "provider": "google"}},
        )
        user_id = user_doc["user_id"]
    else:
        new_user = await _create_user(email, name, password=None, provider="google", picture=picture)
        user_id = new_user["user_id"]

    access_token = create_access_token(user_id, email)
    return RedirectResponse(f"{FRONTEND_URL}/auth/callback?token={access_token}")


# ---------------------------------------------------------------------------
# Public: Categories & Articles
# ---------------------------------------------------------------------------
@api_router.get("/categories")
async def list_categories():
    return await db.categories.find({}, {"_id": 0}).to_list(200)


@api_router.get("/articles")
async def list_articles(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    limit: int = Query(20, le=100),
    skip: int = Query(0),
):
    query: dict = {"status": "published"}
    if category:
        query["$or"] = [{"category_slugs": category}, {"category_slug": category}]
    if tag:
        query["tags"] = tag
    if featured is not None:
        query["featured"] = featured
    if q:
        rx = {"$regex": re.escape(q), "$options": "i"}
        q_or = [{"title": rx}, {"excerpt": rx}, {"content_html": rx}, {"tags": rx}]
        if "$or" in query:
            query = {"$and": [{"$or": query.pop("$or")}, {"$or": q_or}], **query}
        else:
            query["$or"] = q_or
    cursor = db.articles.find(query, {"_id": 0, "content_html": 0}).sort("published_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(limit)


EDUCATION_SLUG = "egitim"


def _is_education_article(art: dict) -> bool:
    slugs = art.get("category_slugs") or ([art.get("category_slug")] if art.get("category_slug") else [])
    return EDUCATION_SLUG in slugs


@api_router.get("/articles/{slug}")
async def get_article(slug: str, user: Optional[User] = Depends(get_current_user_optional)):
    art = await db.articles.find_one({"slug": slug, "status": "published"}, {"_id": 0})
    if not art:
        raise HTTPException(status_code=404, detail="Not found")

    if _is_education_article(art):
        if not user or (user.role != "admin" and not user.education_access):
            art["content_html"] = ""
            art["restricted"] = True
            return art

    await db.articles.update_one({"id": art["id"]}, {"$inc": {"views": 1}})
    art["views"] += 1
    art["restricted"] = False
    return art


@api_router.get("/articles/{slug}/related")
async def related_articles(slug: str):
    art = await db.articles.find_one({"slug": slug}, {"_id": 0})
    if not art:
        return []
    cat_slugs = art.get("category_slugs") or [art.get("category_slug")]
    cursor = db.articles.find(
        {
            "$or": [
                {"category_slugs": {"$in": cat_slugs}},
                {"category_slug": {"$in": cat_slugs}},
            ],
            "slug": {"$ne": slug},
            "status": "published",
        },
        {"_id": 0, "content_html": 0},
    ).sort("published_at", -1).limit(4)
    return await cursor.to_list(4)


# ---------------------------------------------------------------------------
# Author / Admin: Article management
# ---------------------------------------------------------------------------
@api_router.get("/my/articles")
async def my_articles(user: User = Depends(get_current_user)):
    q = {} if user.role == "admin" else {"author_id": user.user_id}
    cursor = db.articles.find(q, {"_id": 0, "content_html": 0}).sort("created_at", -1).limit(200)
    return await cursor.to_list(200)


@api_router.get("/my/articles/{article_id}")
async def get_my_article(article_id: str, user: User = Depends(get_current_user)):
    art = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not art:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role != "admin" and art["author_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return art


@api_router.post("/articles")
async def create_article(payload: ArticleCreate, user: User = Depends(get_current_user)):
    req_slugs = payload.category_slugs or ([payload.category_slug] if payload.category_slug else [])
    req_slugs = [s for s in req_slugs if s]
    if not req_slugs:
        raise HTTPException(status_code=400, detail="En az bir kategori seçmelisiniz")

    resolved = []
    for s in req_slugs:
        c = await db.categories.find_one({"slug": s}, {"_id": 0})
        if not c:
            raise HTTPException(status_code=400, detail=f"Geçersiz kategori: {s}")
        resolved.append(c)

    primary = resolved[0]

    base_slug = slugify(payload.title)
    slug = base_slug
    i = 2
    while await db.articles.find_one({"slug": slug}):
        slug = f"{base_slug}-{i}"
        i += 1

    now = now_iso()
    requested_status = payload.status if payload.status in ("draft", "published") else "draft"
    if user.role != "admin" and requested_status == "published":
        requested_status = "draft"

    art = Article(
        title=payload.title,
        slug=slug,
        excerpt=payload.excerpt or "",
        content_html=payload.content_html or "",
        cover_image=payload.cover_image or "",
        category_slug=primary["slug"],
        category_name=primary["name"],
        category_slugs=[c["slug"] for c in resolved],
        category_names=[c["name"] for c in resolved],
        tags=payload.tags or [],
        author_id=user.user_id,
        author_name=user.name,
        author_picture=user.picture or "",
        status=requested_status,
        featured=bool(payload.featured) if user.role == "admin" else False,
        views=0,
        reading_minutes=compute_reading_minutes(payload.content_html or ""),
        created_at=now,
        updated_at=now,
        published_at=now if requested_status == "published" else None,
    )
    doc = art.model_dump()
    await db.articles.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.patch("/articles/{article_id}")
async def update_article(article_id: str, payload: ArticleUpdate, user: User = Depends(get_current_user)):
    art = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not art:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role != "admin" and art["author_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    updates: dict = {"updated_at": now_iso()}
    data = payload.model_dump(exclude_unset=True)

    if "title" in data:
        updates["title"] = data["title"]
    if "excerpt" in data:
        updates["excerpt"] = data["excerpt"]
    if "content_html" in data:
        updates["content_html"] = data["content_html"]
        updates["reading_minutes"] = compute_reading_minutes(data["content_html"])
    if "cover_image" in data:
        updates["cover_image"] = data["cover_image"]
    if "tags" in data:
        updates["tags"] = data["tags"]
    if "category_slug" in data or "category_slugs" in data:
        req_slugs = data.get("category_slugs") or ([data.get("category_slug")] if data.get("category_slug") else [])
        req_slugs = [s for s in req_slugs if s]
        if not req_slugs:
            raise HTTPException(status_code=400, detail="En az bir kategori seçmelisiniz")
        resolved = []
        for s in req_slugs:
            c = await db.categories.find_one({"slug": s}, {"_id": 0})
            if not c:
                raise HTTPException(status_code=400, detail=f"Geçersiz kategori: {s}")
            resolved.append(c)
        updates["category_slug"] = resolved[0]["slug"]
        updates["category_name"] = resolved[0]["name"]
        updates["category_slugs"] = [c["slug"] for c in resolved]
        updates["category_names"] = [c["name"] for c in resolved]
    if "status" in data and data["status"] in ("draft", "published"):
        if data["status"] == "published" and user.role != "admin":
            raise HTTPException(status_code=403, detail="Sadece admin makale yayınlayabilir")
        updates["status"] = data["status"]
        if data["status"] == "published" and not art.get("published_at"):
            updates["published_at"] = now_iso()
    if "featured" in data:
        if user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admin can feature")
        updates["featured"] = bool(data["featured"])

    await db.articles.update_one({"id": article_id}, {"$set": updates})
    return await db.articles.find_one({"id": article_id}, {"_id": 0})


@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str, user: User = Depends(get_current_user)):
    art = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not art:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role != "admin" and art["author_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await db.articles.delete_one({"id": article_id})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Admin: Categories & Users & Education
# ---------------------------------------------------------------------------
@api_router.post("/admin/categories")
async def create_category(payload: CategoryCreate, admin: User = Depends(require_admin)):
    slug = slugify(payload.name)
    if await db.categories.find_one({"slug": slug}):
        raise HTTPException(status_code=400, detail="Category exists")
    cat = Category(name=payload.name, slug=slug, description=payload.description or "", color=payload.color or "#F59E0B")
    doc = cat.model_dump()
    await db.categories.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.delete("/admin/categories/{cat_id}")
async def delete_category(cat_id: str, admin: User = Depends(require_admin)):
    await db.categories.delete_one({"id": cat_id})
    return {"ok": True}


@api_router.get("/admin/users")
async def list_users(admin: User = Depends(require_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    return users


@api_router.patch("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role: str = Query(...), admin: User = Depends(require_admin)):
    if role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'user'")
    # Prevent demoting super admin
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if target and target["email"] == SUPER_ADMIN_EMAIL and role != "admin":
        raise HTTPException(status_code=400, detail="Super admin rolü değiştirilemez")
    await db.users.update_one({"user_id": user_id}, {"$set": {"role": role}})
    return {"ok": True}


@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: User = Depends(require_admin)):
    target = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Not found")
    if target["email"] == SUPER_ADMIN_EMAIL:
        raise HTTPException(status_code=400, detail="Super admin silinemez")
    await db.users.delete_one({"user_id": user_id})
    return {"ok": True}


@api_router.patch("/admin/users/{user_id}/education")
async def toggle_user_education(user_id: str, enabled: bool = Query(...), admin: User = Depends(require_admin)):
    u = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    await db.users.update_one({"user_id": user_id}, {"$set": {"education_access": bool(enabled)}})
    if enabled:
        if not await db.education_members.find_one({"email": u["email"]}):
            await db.education_members.insert_one({
                "id": str(uuid.uuid4()),
                "email": u["email"],
                "note": f"{u.get('name', '')} (via user toggle)",
                "added_at": now_iso(),
            })
    else:
        await db.education_members.delete_many({"email": u["email"]})
    return {"ok": True}


@api_router.get("/admin/education-members")
async def list_education_members(admin: User = Depends(require_admin)):
    members = await db.education_members.find({}, {"_id": 0}).sort("added_at", -1).to_list(500)
    return members


@api_router.post("/admin/education-members")
async def add_education_member(payload: EducationMemberCreate, admin: User = Depends(require_admin)):
    email = payload.email.lower().strip()
    if await db.education_members.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Bu email zaten eklenmiş")
    doc = {
        "id": str(uuid.uuid4()),
        "email": email,
        "note": payload.note or "",
        "added_at": now_iso(),
    }
    await db.education_members.insert_one(doc)
    doc.pop("_id", None)
    await db.users.update_one({"email": email}, {"$set": {"education_access": True}})
    return doc


@api_router.delete("/admin/education-members/{member_id}")
async def remove_education_member(member_id: str, admin: User = Depends(require_admin)):
    m = await db.education_members.find_one({"id": member_id}, {"_id": 0})
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    await db.education_members.delete_one({"id": member_id})
    await db.users.update_one({"email": m["email"]}, {"$set": {"education_access": False}})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Uploads (Local file storage)
# ---------------------------------------------------------------------------
ALLOWED_IMG_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@api_router.post("/upload")
async def upload_image(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    ctype = file.content_type or "application/octet-stream"
    if ctype not in ALLOWED_IMG_TYPES:
        raise HTTPException(status_code=400, detail="Only image files allowed (jpg, png, webp, gif)")
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Max 8MB")

    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "bin"
    ext = re.sub(r"[^a-z0-9]", "", ext)[:5] or "bin"
    filename = f"{uuid.uuid4().hex}.{ext}"
    user_dir = UPLOAD_DIR / user.user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_dir / filename
    file_path.write_bytes(data)

    storage_path = f"{user.user_id}/{filename}"
    file_id = str(uuid.uuid4())
    await db.files.insert_one({
        "id": file_id,
        "storage_path": storage_path,
        "original_filename": file.filename,
        "content_type": ctype,
        "size": len(data),
        "uploaded_by": user.user_id,
        "created_at": now_iso(),
    })
    return {"id": file_id, "url": f"/api/files/{storage_path}", "size": len(data)}


@api_router.get("/files/{path:path}")
async def download_file(path: str):
    # Prevent path traversal
    safe_path = (UPLOAD_DIR / path).resolve()
    try:
        safe_path.relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    record = await db.files.find_one({"storage_path": path}, {"_id": 0})
    media_type = record.get("content_type") if record else "application/octet-stream"
    return FileResponse(safe_path, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})


# ---------------------------------------------------------------------------
# Ticker
# ---------------------------------------------------------------------------
@api_router.get("/ticker")
async def ticker():
    return {"items": [
        {"symbol": "BIST THYAO", "price": "327.83", "change": "+2.45%", "signal": "TF AL"},
        {"symbol": "BIST EUPWR", "price": "92.71", "change": "+4.58%", "signal": "TF AL"},
        {"symbol": "BIST GESAN", "price": "95.76", "change": "+8.47%", "signal": "TF AL"},
        {"symbol": "BIST ASTOR", "price": "72.33", "change": "+1.12%", "signal": "TF AL"},
        {"symbol": "BIST TOASO", "price": "215.40", "change": "-1.30%", "signal": "TF SAT"},
        {"symbol": "BIST SISE", "price": "97.58", "change": "-2.42%", "signal": "TF SAT"},
        {"symbol": "US SPX", "price": "4,508.32", "change": "+0.42%", "signal": "POZ GAMMA"},
        {"symbol": "US QQQ", "price": "382.11", "change": "+1.08%", "signal": "BULL"},
        {"symbol": "US VIX", "price": "13.84", "change": "-3.21%", "signal": "DÜŞÜK"},
        {"symbol": "GEX NET", "price": "+1.42B", "change": "POZ", "signal": "HEDGE"},
        {"symbol": "0DTE", "price": "62%", "change": "↑", "signal": "ELEVATED"},
        {"symbol": "BTC", "price": "104,250", "change": "+2.14%", "signal": "BULL"},
    ]}


# ---------------------------------------------------------------------------
# Seed defaults
# ---------------------------------------------------------------------------
DEFAULT_CATEGORIES = [
    {"name": "BIST", "description": "Borsa İstanbul analizleri ve algoritmik sinyaller", "color": "#F59E0B"},
    {"name": "Wall Street", "description": "ABD piyasaları, GEX, Vanna, 0DTE haritaları", "color": "#10B981"},
    {"name": "Opsiyonlar", "description": "Opsiyon piyasaları, Greeks, hedging stratejileri", "color": "#EF4444"},
    {"name": "Kripto", "description": "Kripto piyasaları ve türev analizleri", "color": "#10B981"},
    {"name": "Sentiment", "description": "Alıcı-satıcı gücü ve piyasa duygusu", "color": "#F59E0B"},
    {"name": "Eğitim", "description": "Kantitatif finans ve algo trading eğitimleri", "color": "#A1A1AA"},
]


async def seed_super_admin():
    """Ensure the hardcoded super admin exists on startup with initial password."""
    existing = await db.users.find_one({"email": SUPER_ADMIN_EMAIL}, {"_id": 0})
    if existing:
        updates = {}
        if existing.get("role") != "admin":
            updates["role"] = "admin"
        if not existing.get("password_hash"):
            # User previously created without a password (e.g. via OAuth) — bootstrap one so they can log in.
            updates["password_hash"] = hash_password(SUPER_ADMIN_INITIAL_PASSWORD)
            updates["must_change_password"] = True
            updates["provider"] = existing.get("provider") or "local"
            logger.info(f"Super admin missing password — bootstrapped with initial password: {SUPER_ADMIN_INITIAL_PASSWORD}")
        if updates:
            await db.users.update_one({"email": SUPER_ADMIN_EMAIL}, {"$set": updates})
        return
    doc = {
        "user_id": f"user_{uuid.uuid4().hex[:12]}",
        "email": SUPER_ADMIN_EMAIL,
        "name": "PrivyAlgo Super Admin",
        "picture": "",
        "role": "admin",
        "bio": "nFinans Araştırma Super Admin",
        "education_access": True,
        "must_change_password": True,
        "provider": "local",
        "password_hash": hash_password(SUPER_ADMIN_INITIAL_PASSWORD),
        "created_at": now_iso(),
    }
    await db.users.insert_one(doc)
    logger.info(f"Super admin seeded: {SUPER_ADMIN_EMAIL} / initial password: {SUPER_ADMIN_INITIAL_PASSWORD}")


async def seed_categories():
    if await db.categories.count_documents({}) == 0:
        for c in DEFAULT_CATEGORIES:
            slug = slugify(c["name"])
            await db.categories.insert_one({
                "id": str(uuid.uuid4()),
                "name": c["name"],
                "slug": slug,
                "description": c["description"],
                "color": c["color"],
            })
        logger.info("Seeded default categories")


# ---------------------------------------------------------------------------
# App wiring
# ---------------------------------------------------------------------------
app.include_router(api_router)

# SessionMiddleware is required by Authlib for OAuth state
app.add_middleware(SessionMiddleware, secret_key=JWT_SECRET, same_site="lax", https_only=False)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_start():
    await seed_super_admin()
    await seed_categories()


@app.on_event("shutdown")
async def on_stop():
    client.close()
