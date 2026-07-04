"""
PrivyAlgo Blog — Backend API
FastAPI + MongoDB + Emergent Google Auth + Emergent Object Storage
"""
import os
import re
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any

import requests
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Header, Cookie, Response, UploadFile, File, Form, Query, Request
from fastapi.responses import Response as FastAPIResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

APP_NAME = "privyalgo-blog"
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
ADMIN_EMAILS = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="PrivyAlgo Blog API")
api_router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Storage (Emergent Object Storage)
# ---------------------------------------------------------------------------
_storage_key: Optional[str] = None


def init_storage() -> Optional[str]:
    global _storage_key
    if _storage_key:
        return _storage_key
    if not EMERGENT_KEY:
        logger.warning("EMERGENT_LLM_KEY not set — storage disabled")
        return None
    try:
        r = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
        r.raise_for_status()
        _storage_key = r.json()["storage_key"]
        logger.info("Storage initialized")
        return _storage_key
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
        return None


def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage unavailable")
    r = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


def get_object(path: str):
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage unavailable")
    r = requests.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key}, timeout=60)
    r.raise_for_status()
    return r.content, r.headers.get("Content-Type", "application/octet-stream")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = ""
    role: str = "writer"  # "admin" | "writer"
    bio: Optional[str] = ""
    education_access: bool = False  # can view /kategori/egitim content
    created_at: str


class EducationMemberCreate(BaseModel):
    email: str
    note: Optional[str] = ""


class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    description: Optional[str] = ""
    color: Optional[str] = "#10B981"


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "#10B981"


class Article(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    excerpt: str = ""
    content_html: str = ""
    cover_image: Optional[str] = ""
    category_slug: str  # primary category (backward compat + primary display)
    category_name: str
    category_slugs: List[str] = []  # all categories (multi-select)
    category_names: List[str] = []
    tags: List[str] = []
    author_id: str
    author_name: str
    author_picture: Optional[str] = ""
    status: str = "draft"  # "draft" | "published"
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
    category_slug: Optional[str] = None  # deprecated single category
    category_slugs: Optional[List[str]] = None  # preferred: list of categories
    tags: List[str] = []
    status: str = "draft"


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


# ---------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(s: str) -> str:
    s = s.lower().strip()
    # Turkish char map
    tr = str.maketrans("çğıöşüâîû", "cgiosuaiu")
    s = s.translate(tr)
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s or uuid.uuid4().hex[:8]


def compute_reading_minutes(html: str) -> int:
    text = re.sub(r"<[^>]+>", " ", html or "")
    words = len(text.split())
    return max(1, round(words / 200))


async def get_current_user(session_token: Optional[str], authorization: Optional[str]) -> Optional[User]:
    """Get user via cookie or Bearer token."""
    token = session_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if not token:
        return None
    session_doc = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session_doc:
        return None
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        return None
    return User(**user_doc)


async def require_user(session_token: Optional[str], authorization: Optional[str]) -> User:
    user = await get_current_user(session_token, authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_admin(session_token: Optional[str], authorization: Optional[str]) -> User:
    user = await require_user(session_token, authorization)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ---------------------------------------------------------------------------
# Auth Routes
# ---------------------------------------------------------------------------
@api_router.post("/auth/session")
async def create_session(response: Response, x_session_id: Optional[str] = Header(None)):
    """Exchange session_id from Emergent Auth for our own session token."""
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Missing session id")

    try:
        r = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": x_session_id},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error(f"Emergent auth failed: {e}")
        raise HTTPException(status_code=401, detail="Auth failed") from e

    email = data["email"].lower()
    name = data.get("name", email.split("@")[0])
    picture = data.get("picture", "")
    session_token = data["session_token"]

    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        # Update picture/name in case they changed
        await db.users.update_one({"user_id": user_id}, {"$set": {"name": name, "picture": picture}})
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        # Determine role: if configured admin email OR first user in system
        role = "writer"
        if email in ADMIN_EMAILS:
            role = "admin"
        else:
            total_users = await db.users.count_documents({})
            if total_users == 0:
                role = "admin"
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "role": role,
            "bio": "",
            "education_access": False,
            "created_at": now_iso(),
        })

    # Sync education_access based on pre-approved email list
    is_edu_member = await db.education_members.find_one({"email": email}, {"_id": 0}) is not None
    await db.users.update_one({"user_id": user_id}, {"$set": {"education_access": is_edu_member}})

    # Store session
    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": now_iso(),
    })

    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=7 * 24 * 60 * 60,
        path="/",
        httponly=True,
        secure=True,
        samesite="none",
    )

    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return {"user": user_doc, "session_token": session_token}


@api_router.get("/auth/me")
async def me(session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    user = await require_user(session_token, authorization)
    return user.model_dump()


@api_router.post("/auth/logout")
async def logout(response: Response, session_token: Optional[str] = Cookie(None)):
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie("session_token", path="/", samesite="none", secure=True)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Public: Categories & Articles
# ---------------------------------------------------------------------------
@api_router.get("/categories")
async def list_categories():
    cats = await db.categories.find({}, {"_id": 0}).to_list(200)
    return cats


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
        # Support both new list field and legacy single field
        query["$or"] = [{"category_slugs": category}, {"category_slug": category}]
    if tag:
        query["tags"] = tag
    if featured is not None:
        query["featured"] = featured
    if q:
        rx = {"$regex": re.escape(q), "$options": "i"}
        q_or = [{"title": rx}, {"excerpt": rx}, {"content_html": rx}, {"tags": rx}]
        if "$or" in query:
            # combine: (category match) AND (search match)
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
async def get_article(slug: str, session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    art = await db.articles.find_one({"slug": slug, "status": "published"}, {"_id": 0})
    if not art:
        raise HTTPException(status_code=404, detail="Not found")

    # Restrict content_html for education articles if user is not approved
    if _is_education_article(art):
        user = await get_current_user(session_token, authorization)
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
async def my_articles(session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    user = await require_user(session_token, authorization)
    q = {} if user.role == "admin" else {"author_id": user.user_id}
    cursor = db.articles.find(q, {"_id": 0, "content_html": 0}).sort("created_at", -1).limit(200)
    return await cursor.to_list(200)


@api_router.get("/my/articles/{article_id}")
async def get_my_article(article_id: str, session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    user = await require_user(session_token, authorization)
    art = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not art:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role != "admin" and art["author_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return art


@api_router.post("/articles")
async def create_article(payload: ArticleCreate, session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    user = await require_user(session_token, authorization)

    # Normalize: accept either category_slugs (list) or category_slug (single)
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
    category_slugs = [c["slug"] for c in resolved]
    category_names = [c["name"] for c in resolved]

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
        category_slugs=category_slugs,
        category_names=category_names,
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
async def update_article(article_id: str, payload: ArticleUpdate, session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    user = await require_user(session_token, authorization)
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
        # Only admins can publish; writers can only save as draft
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
    new_doc = await db.articles.find_one({"id": article_id}, {"_id": 0})
    return new_doc


@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str, session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    user = await require_user(session_token, authorization)
    art = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not art:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role != "admin" and art["author_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await db.articles.delete_one({"id": article_id})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Admin: Categories & Users
# ---------------------------------------------------------------------------
@api_router.post("/admin/categories")
async def create_category(payload: CategoryCreate, session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    await require_admin(session_token, authorization)
    slug = slugify(payload.name)
    if await db.categories.find_one({"slug": slug}):
        raise HTTPException(status_code=400, detail="Category exists")
    cat = Category(name=payload.name, slug=slug, description=payload.description or "", color=payload.color or "#10B981")
    await db.categories.insert_one(cat.model_dump())
    return cat.model_dump()


@api_router.delete("/admin/categories/{cat_id}")
async def delete_category(cat_id: str, session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    await require_admin(session_token, authorization)
    await db.categories.delete_one({"id": cat_id})
    return {"ok": True}


@api_router.get("/admin/users")
async def list_users(session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    await require_admin(session_token, authorization)
    users = await db.users.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return users


@api_router.patch("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role: str = Query(...), session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    await require_admin(session_token, authorization)
    if role not in ("admin", "writer"):
        raise HTTPException(status_code=400, detail="Invalid role")
    await db.users.update_one({"user_id": user_id}, {"$set": {"role": role}})
    return {"ok": True}


@api_router.patch("/admin/users/{user_id}/education")
async def toggle_user_education(user_id: str, enabled: bool = Query(...), session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    await require_admin(session_token, authorization)
    u = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    await db.users.update_one({"user_id": user_id}, {"$set": {"education_access": bool(enabled)}})
    # Also mirror into education_members list so the flag persists across re-logins
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


# -------- Education Members (pre-approved emails) --------
@api_router.get("/admin/education-members")
async def list_education_members(session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    await require_admin(session_token, authorization)
    members = await db.education_members.find({}, {"_id": 0}).sort("added_at", -1).to_list(500)
    return members


@api_router.post("/admin/education-members")
async def add_education_member(payload: EducationMemberCreate, session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    await require_admin(session_token, authorization)
    email = (payload.email or "").strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Geçerli bir email adresi girin")
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
    # If user already exists with this email, immediately grant access
    await db.users.update_one({"email": email}, {"$set": {"education_access": True}})
    return doc


@api_router.delete("/admin/education-members/{member_id}")
async def remove_education_member(member_id: str, session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    await require_admin(session_token, authorization)
    m = await db.education_members.find_one({"id": member_id}, {"_id": 0})
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    await db.education_members.delete_one({"id": member_id})
    # Revoke access on the user if they exist
    await db.users.update_one({"email": m["email"]}, {"$set": {"education_access": False}})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Uploads
# ---------------------------------------------------------------------------
ALLOWED_IMG_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@api_router.post("/upload")
async def upload_image(file: UploadFile = File(...), session_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):
    user = await require_user(session_token, authorization)
    ctype = file.content_type or "application/octet-stream"
    if ctype not in ALLOWED_IMG_TYPES:
        raise HTTPException(status_code=400, detail="Only image files allowed (jpg, png, webp, gif)")
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Max 8MB")

    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else "bin"
    path = f"{APP_NAME}/uploads/{user.user_id}/{uuid.uuid4().hex}.{ext}"
    result = put_object(path, data, ctype)

    file_id = str(uuid.uuid4())
    await db.files.insert_one({
        "id": file_id,
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": ctype,
        "size": result.get("size", len(data)),
        "uploaded_by": user.user_id,
        "is_deleted": False,
        "created_at": now_iso(),
    })

    return {"id": file_id, "url": f"/api/files/{result['path']}", "size": result.get("size", len(data))}


@api_router.get("/files/{path:path}")
async def download_file(path: str):
    record = await db.files.find_one({"storage_path": path, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    data, ctype = get_object(path)
    return FastAPIResponse(content=data, media_type=record.get("content_type", ctype), headers={"Cache-Control": "public, max-age=86400"})


# ---------------------------------------------------------------------------
# Ticker (mock financial data for the marquee)
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
    {"name": "BIST", "description": "Borsa İstanbul analizleri ve algoritmik sinyaller", "color": "#10B981"},
    {"name": "Wall Street", "description": "ABD piyasaları, GEX, Vanna, 0DTE haritaları", "color": "#F59E0B"},
    {"name": "Opsiyonlar", "description": "Opsiyon piyasaları, Greeks, hedging stratejileri", "color": "#EF4444"},
    {"name": "Kripto", "description": "Kripto piyasaları ve türev analizleri", "color": "#F59E0B"},
    {"name": "Sentiment", "description": "Alıcı-satıcı gücü ve piyasa duygusu", "color": "#10B981"},
    {"name": "Eğitim", "description": "Kantitatif finans ve algo trading eğitimleri", "color": "#A1A1AA"},
]


DEMO_ARTICLES = [
    {
        "title": "BIST'te TF AL Sinyalleri Nasıl Okunur?",
        "excerpt": "Momentum, Market Score ve AOF kombinasyonundan üretilen TF AL/SAT sinyallerinin arkasındaki matematik ve pratik kullanım rehberi.",
        "category_slug": "bist",
        "tags": ["TF AL", "sinyal", "momentum"],
        "cover_image": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1600&q=80",
        "featured": True,
        "content_html": """
<p>PrivyAlgo TF AL / TF SAT sinyalleri, üç ana bileşenin ağırlıklı kombinasyonundan üretilir: <strong>Momentum</strong>, <strong>Market Score</strong> ve <strong>AOF (Ağırlıklı Ortalama Fiyat)</strong>. Bu üç bileşen 5, 15, 60 ve 120 dakikalık zaman dilimlerinde ayrı ayrı hesaplanır.</p>
<h2>Momentum Skoru</h2>
<p>Momentum, son N barın kapanış farklarının hacim ağırlıklı toplamıdır. Pozitif momentum alıcıların baskın olduğunu, negatif momentum ise satıcıların baskın olduğunu gösterir. Ancak momentum tek başına sinyal üretmez; her zaman <em>Market Score</em> ile birlikte değerlendirilir.</p>
<h2>Market Score</h2>
<p>Market Score, alıcı ve satıcı emir defterlerindeki likidite dengesizliğini +1.0 ile -1.0 arasında normalize ederek okur. 1.0'a yakın değerler güçlü alıcı baskısını, -1.0'a yakın değerler güçlü satıcı baskısını gösterir.</p>
<blockquote>Bir TF AL sinyali, üç bileşen de pozitif tarafta hizalandığında üretilir. Yanlış sinyal oranı %8'in altındadır.</blockquote>
<h2>Pratik Kullanım</h2>
<ul>
<li>15dk grafikte TF AL geldiğinde, 60dk grafiğinde momentum pozitif olmalı.</li>
<li>Hedge Wall seviyesinin üzerinde TF AL, güçlü uzun pozisyon için doğrulamadır.</li>
<li>TF SAT sinyalinde stop, son 5 barın en yüksek noktası olarak konur.</li>
</ul>
<p>Sinyallerin canlı takibi için <a href="https://bist.privyalgo.com">BIST Terminal</a>'i kullanabilirsiniz.</p>
""",
    },
    {
        "title": "Wall Street: Net GEX ve Vanna Akışları Piyasayı Nasıl Yönlendirir?",
        "excerpt": "Opsiyon piyasa yapıcılarının hedge davranışlarını okumak için Net GEX ve Vanna (VEX) haritaları neden kritiktir?",
        "category_slug": "wall-street",
        "tags": ["GEX", "Vanna", "SPX"],
        "cover_image": "https://images.unsplash.com/photo-1639305239797-41f29e441d78?w=1600&q=80",
        "featured": True,
        "content_html": """
<p>Piyasa yapıcılar (Market Makers) hedge etmek zorunda oldukları için, opsiyon açık pozisyonları (Open Interest) sadece bir istatistik değil, aynı zamanda spot piyasada <strong>fiili likidite hareketleridir</strong>.</p>
<h2>Net GEX Nedir?</h2>
<p>Net Gamma Exposure (GEX), tüm strike'lardaki dealer pozisyonlarının gamma'sının net toplamıdır. Pozitif GEX rejiminde piyasa yapıcılar <em>volatiliteyi bastırır</em>: fiyat yükseldikçe satar, düştükçe alır — bu da fiyat aralığını daraltır.</p>
<h2>Vanna: İkinci Türev Silahı</h2>
<p>Vanna, delta'nın volatiliteye duyarlılığıdır. VIX düştüğünde vanna pozitif olan dealerlar spot piyasadan alım yapar. Bu, "VIX crush → SPX up" korelasyonunun temel mekanizmasıdır.</p>
<pre><code>Rejim Tespiti:
  NET GEX > +1B  &rarr; Pin risk, dar range
  NET GEX < -500M &rarr; Volatilite patlaması</code></pre>
<h2>0DTE Etkisi</h2>
<p>Günün son 2 saatinde 0DTE opsiyonların gamma'sı katlanarak büyür. Bu, sabahları sakin görünen piyasanın öğleden sonra ani hareketler yaşamasının temel sebebidir.</p>
""",
    },
    {
        "title": "Sentiment Skoru: Alıcı ve Satıcı Gücünü Ölçmenin Matematiği",
        "excerpt": "BuyerScore, SellerScore ve toplam SentimentScore nasıl hesaplanır? Neden hisse haberleri değil bu skorlar öncüdür?",
        "category_slug": "sentiment",
        "tags": ["sentiment", "buyer score", "seller score"],
        "cover_image": "https://images.pexels.com/photos/6770610/pexels-photo-6770610.jpeg?w=1600&q=80",
        "featured": False,
        "content_html": """
<p>Sentiment Score, geleneksel haberlerden çok önce fiyat hareketini haber verir çünkü <strong>haberler yavaşlar, likidite hızlı akar</strong>. PrivyAlgo Sentiment formülü üç ana veri katmanı kullanır.</p>
<h2>Veri Katmanları</h2>
<ol>
<li><strong>Alış/Satış Hacim Oranı</strong> — Emir defterindeki agresif alıcı ve satıcı hacimlerinin oranı.</li>
<li><strong>Fiyat/Ortalama Sapma</strong> — Fiyatın hacim ağırlıklı ortalamadan sapması.</li>
<li><strong>Likidite Emici Emirler</strong> — Bid ve ask üzerindeki büyük emirlerin oranı.</li>
</ol>
<h3>Formül</h3>
<p><code>Score = 0.5 * (BuyVol - SellVol)/TotalVol + 0.3 * (Price - VWAP)/ATR + 0.2 * LiquidityRatio</code></p>
<blockquote>+80 üzerindeki skorlar güçlü alıcı bölgesini, -80 altındaki skorlar güçlü satıcı bölgesini işaret eder.</blockquote>
""",
    },
    {
        "title": "Opsiyon 101: Greeks Delta, Gamma, Theta, Vega Nedir?",
        "excerpt": "Opsiyon fiyatını yönlendiren dört ana Yunan harfi — sıfırdan pratik örneklerle.",
        "category_slug": "egitim",
        "tags": ["eğitim", "opsiyon", "greeks"],
        "cover_image": "https://images.unsplash.com/photo-1644088379091-d574269d422f?w=1600&q=80",
        "featured": False,
        "content_html": """
<p>Opsiyon fiyatlaması çok değişkenli bir denklemdir. Greeks, bu değişkenlerin her birinin fiyata etkisini ölçen türevlerdir.</p>
<h2>Delta (&Delta;)</h2>
<p>Opsiyon fiyatının, spot fiyatındaki 1 birim değişime tepkisi. ATM bir call'un delta'sı ~0.5'tir. Delta aynı zamanda opsiyonun ITM sonlanma olasılığının kaba tahminidir.</p>
<h2>Gamma (&Gamma;)</h2>
<p>Delta'nın delta'sı. Spot hareket ettikçe delta'nın ne kadar hızlı değişeceğini söyler. En yüksek gamma ATM'dedir ve vade yaklaştıkça artar.</p>
<h2>Theta (&Theta;)</h2>
<p>Zaman değeri erozyonu. Uzun opsiyon pozisyonları theta ödediği için "kiracıdır"; kısa pozisyonlar "kiracıdan kira alır".</p>
<h2>Vega (V)</h2>
<p>Implied volatilite değişimine duyarlılık. IV yükseldiğinde uzun opsiyon değer kazanır.</p>
""",
    },
    {
        "title": "Kripto Piyasasında Türev Akış Analizi: Deribit Verisi Ne Söyler?",
        "excerpt": "BTC ve ETH opsiyon piyasalarında Open Interest, Put/Call oranı ve funding rate'lerin fiyatla ilişkisi.",
        "category_slug": "kripto",
        "tags": ["BTC", "Deribit", "OI"],
        "cover_image": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=1600&q=80",
        "featured": False,
        "content_html": """
<p>Kripto piyasaları 7/24 açıktır ve türevler burada spot piyasayı sıklıkla domine eder. Deribit'in BTC ve ETH opsiyon zincirinden çıkarılan üç metrik, kısa vadeli yön için altın değerinde ipucu verir.</p>
<h2>1. Open Interest Konsantrasyonu</h2>
<p>Belirli strike'larda biriken OI, dealer hedge davranışı nedeniyle "mıknatıs" gibi çalışır. BTC 100k üzerindeki büyük call OI, spot fiyatını çekim etkisiyle o seviyeye yaklaştırabilir.</p>
<h2>2. Put/Call Oranı</h2>
<p>PCR &gt; 1: Aşırı korumacı ortam &rarr; contrarian long. PCR &lt; 0.5: Aşırı iyimserlik &rarr; dikkat.</p>
<h2>3. Perpetual Funding</h2>
<p>Pozitif funding: long'lar prim ödüyor (aşırı ısınma). Negatif funding: short'lar prim ödüyor (bottom sinyali).</p>
""",
    },
]


async def seed_data():
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

    if await db.articles.count_documents({}) == 0:
        # Seed a system author
        system_user_id = "system_privyalgo"
        if not await db.users.find_one({"user_id": system_user_id}):
            await db.users.insert_one({
                "user_id": system_user_id,
                "email": "editor@privyalgo.blog",
                "name": "PrivyAlgo Editör",
                "picture": "",
                "role": "admin",
                "bio": "nFinans Araştırma editörü",
                "created_at": now_iso(),
            })
        now = now_iso()
        for i, a in enumerate(DEMO_ARTICLES):
            slug = slugify(a["title"])
            cat = await db.categories.find_one({"slug": a["category_slug"]}, {"_id": 0})
            if not cat:
                continue
            doc = {
                "id": str(uuid.uuid4()),
                "title": a["title"],
                "slug": slug,
                "excerpt": a["excerpt"],
                "content_html": a["content_html"],
                "cover_image": a["cover_image"],
                "category_slug": a["category_slug"],
                "category_name": cat["name"],
                "category_slugs": [a["category_slug"]],
                "category_names": [cat["name"]],
                "tags": a["tags"],
                "author_id": system_user_id,
                "author_name": "PrivyAlgo Editör",
                "author_picture": "",
                "status": "published",
                "featured": a.get("featured", False),
                "views": 0,
                "reading_minutes": compute_reading_minutes(a["content_html"]),
                "created_at": now,
                "updated_at": now,
                "published_at": now,
            }
            await db.articles.insert_one(doc)
        logger.info(f"Seeded {len(DEMO_ARTICLES)} demo articles")

    # Migrate existing docs missing category_slugs array (idempotent)
    async for old in db.articles.find({"category_slugs": {"$exists": False}}, {"_id": 0, "id": 1, "category_slug": 1, "category_name": 1}):
        await db.articles.update_one(
            {"id": old["id"]},
            {"$set": {"category_slugs": [old.get("category_slug")], "category_names": [old.get("category_name")]}},
        )


# ---------------------------------------------------------------------------
# App wiring
# ---------------------------------------------------------------------------
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_start():
    try:
        init_storage()
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
    await seed_data()


@app.on_event("shutdown")
async def on_stop():
    client.close()
