"""PrivyAlgo Blog backend API tests."""
import os
import io
import subprocess
import uuid
import time
import pytest
import requests
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # Read from frontend env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"


def mongo_eval(script: str) -> str:
    r = subprocess.run(
        ["mongosh", "mongodb://localhost:27017/test_database", "--quiet", "--eval", script],
        capture_output=True, text=True, timeout=30,
    )
    return r.stdout + r.stderr


@pytest.fixture(scope="session")
def admin_session():
    uid = f"TEST_admin_{uuid.uuid4().hex[:8]}"
    tok = f"TEST_tok_admin_{uuid.uuid4().hex}"
    email = f"TEST_admin_{uuid.uuid4().hex[:6]}@example.com"
    expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    script = f"""
    db.users.insertOne({{user_id:"{uid}",email:"{email}",name:"Admin Test",picture:"",role:"admin",bio:"",created_at:"{now}"}});
    db.user_sessions.insertOne({{user_id:"{uid}",session_token:"{tok}",expires_at:"{expires}",created_at:"{now}"}});
    """
    mongo_eval(script)
    yield {"user_id": uid, "token": tok, "email": email}
    mongo_eval(f'db.user_sessions.deleteOne({{session_token:"{tok}"}}); db.users.deleteOne({{user_id:"{uid}"}}); db.articles.deleteMany({{author_id:"{uid}"}});')


@pytest.fixture(scope="session")
def writer_session():
    uid = f"TEST_writer_{uuid.uuid4().hex[:8]}"
    tok = f"TEST_tok_writer_{uuid.uuid4().hex}"
    email = f"TEST_writer_{uuid.uuid4().hex[:6]}@example.com"
    expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    script = f"""
    db.users.insertOne({{user_id:"{uid}",email:"{email}",name:"Writer Test",picture:"",role:"writer",bio:"",created_at:"{now}"}});
    db.user_sessions.insertOne({{user_id:"{uid}",session_token:"{tok}",expires_at:"{expires}",created_at:"{now}"}});
    """
    mongo_eval(script)
    yield {"user_id": uid, "token": tok, "email": email}
    mongo_eval(f'db.user_sessions.deleteOne({{session_token:"{tok}"}}); db.users.deleteOne({{user_id:"{uid}"}}); db.articles.deleteMany({{author_id:"{uid}"}});')


def hdr(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------- Public ----------
class TestPublic:
    def test_categories_seeded(self):
        r = requests.get(f"{API}/categories")
        assert r.status_code == 200
        cats = r.json()
        names = {c["name"] for c in cats}
        for expected in ["BIST", "Wall Street", "Opsiyonlar", "Kripto", "Sentiment", "Eğitim"]:
            assert expected in names, f"Missing category {expected}, got {names}"
        assert len(cats) >= 6

    def test_ticker_12(self):
        r = requests.get(f"{API}/ticker")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert len(data["items"]) == 12

    def test_articles_list_no_content_html(self):
        r = requests.get(f"{API}/articles")
        assert r.status_code == 200
        arts = r.json()
        assert isinstance(arts, list)
        assert len(arts) >= 1
        for a in arts:
            assert "content_html" not in a
            assert a.get("status") == "published"

    def test_articles_featured_filter(self):
        r = requests.get(f"{API}/articles", params={"featured": "true"})
        assert r.status_code == 200
        arts = r.json()
        assert len(arts) >= 1
        for a in arts:
            assert a["featured"] is True

    def test_articles_category_filter(self):
        r = requests.get(f"{API}/articles", params={"category": "bist"})
        assert r.status_code == 200
        arts = r.json()
        assert len(arts) >= 1
        for a in arts:
            assert a["category_slug"] == "bist"

    def test_articles_search_gex(self):
        r = requests.get(f"{API}/articles", params={"q": "GEX"})
        assert r.status_code == 200
        arts = r.json()
        assert len(arts) >= 1

    def test_get_single_article_and_views_increment(self):
        # Find an existing slug from list
        r = requests.get(f"{API}/articles")
        slug = r.json()[0]["slug"]
        r1 = requests.get(f"{API}/articles/{slug}")
        assert r1.status_code == 200
        v1 = r1.json()["views"]
        r2 = requests.get(f"{API}/articles/{slug}")
        v2 = r2.json()["views"]
        assert v2 == v1 + 1
        assert "content_html" in r2.json()

    def test_related_articles(self):
        r = requests.get(f"{API}/articles")
        slug = r.json()[0]["slug"]
        r2 = requests.get(f"{API}/articles/{slug}/related")
        assert r2.status_code == 200
        rel = r2.json()
        for a in rel:
            assert a["slug"] != slug


# ---------- Auth ----------
class TestAuth:
    def test_session_missing_header(self):
        r = requests.post(f"{API}/auth/session")
        assert r.status_code == 400

    def test_me_no_auth(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_me_bearer(self, admin_session):
        r = requests.get(f"{API}/auth/me", headers=hdr(admin_session["token"]))
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == admin_session["user_id"]
        assert data["role"] == "admin"

    def test_logout_deletes_session(self):
        # Create ephemeral session
        uid = f"TEST_logout_{uuid.uuid4().hex[:8]}"
        tok = f"TEST_tok_logout_{uuid.uuid4().hex}"
        expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        now = datetime.now(timezone.utc).isoformat()
        mongo_eval(f"""
        db.users.insertOne({{user_id:"{uid}",email:"TEST_l@e.com",name:"L",picture:"",role:"writer",bio:"",created_at:"{now}"}});
        db.user_sessions.insertOne({{user_id:"{uid}",session_token:"{tok}",expires_at:"{expires}",created_at:"{now}"}});
        """)
        # Use cookie for logout since endpoint reads cookie
        r = requests.post(f"{API}/auth/logout", cookies={"session_token": tok})
        assert r.status_code == 200
        # Verify session deleted
        out = mongo_eval(f'db.user_sessions.countDocuments({{session_token:"{tok}"}});')
        assert "0" in out.strip().split()[-1] if out.strip() else True
        # Cleanup
        mongo_eval(f'db.users.deleteOne({{user_id:"{uid}"}});')


# ---------- Writer flow ----------
class TestWriterFlow:
    def test_writer_create_list_update_delete(self, writer_session):
        tok = writer_session["token"]
        # Create
        payload = {
            "title": f"TEST_Writer_Article_{uuid.uuid4().hex[:6]}",
            "excerpt": "özet",
            "content_html": "<p>içerik</p>",
            "category_slug": "bist",
            "tags": ["test"],
            "status": "published",
        }
        r = requests.post(f"{API}/articles", json=payload, headers=hdr(tok))
        assert r.status_code == 200, r.text
        art = r.json()
        assert art["author_id"] == writer_session["user_id"]
        assert art["featured"] is False
        aid = art["id"]

        # /my/articles returns own only
        r = requests.get(f"{API}/my/articles", headers=hdr(tok))
        assert r.status_code == 200
        mine = r.json()
        assert all(a["author_id"] == writer_session["user_id"] for a in mine)
        assert any(a["id"] == aid for a in mine)

        # Update
        r = requests.patch(f"{API}/articles/{aid}", json={"title": "TEST_Updated_Title"}, headers=hdr(tok))
        assert r.status_code == 200
        assert r.json()["title"] == "TEST_Updated_Title"

        # Delete
        r = requests.delete(f"{API}/articles/{aid}", headers=hdr(tok))
        assert r.status_code == 200

    def test_writer_cannot_feature(self, writer_session):
        tok = writer_session["token"]
        payload = {
            "title": f"TEST_NoFeature_{uuid.uuid4().hex[:6]}",
            "excerpt": "e", "content_html": "<p>c</p>",
            "category_slug": "bist", "tags": [], "status": "published",
        }
        r = requests.post(f"{API}/articles", json=payload, headers=hdr(tok))
        aid = r.json()["id"]
        r = requests.patch(f"{API}/articles/{aid}", json={"featured": True}, headers=hdr(tok))
        assert r.status_code == 403
        requests.delete(f"{API}/articles/{aid}", headers=hdr(tok))

    def test_create_article_invalid_category(self, writer_session):
        r = requests.post(f"{API}/articles", json={
            "title": "TEST_BadCat", "content_html": "<p>x</p>",
            "category_slug": "nonexistent-cat-xyz", "status": "draft",
        }, headers=hdr(writer_session["token"]))
        assert r.status_code == 400

    def test_slug_uniqueness(self, writer_session):
        tok = writer_session["token"]
        title = f"TEST_SlugDup_{uuid.uuid4().hex[:6]}"
        p = {"title": title, "content_html": "<p>a</p>", "category_slug": "bist", "status": "draft"}
        r1 = requests.post(f"{API}/articles", json=p, headers=hdr(tok))
        r2 = requests.post(f"{API}/articles", json=p, headers=hdr(tok))
        assert r1.status_code == 200 and r2.status_code == 200
        s1, s2 = r1.json()["slug"], r2.json()["slug"]
        assert s1 != s2
        assert s2.endswith("-2")
        requests.delete(f"{API}/articles/{r1.json()['id']}", headers=hdr(tok))
        requests.delete(f"{API}/articles/{r2.json()['id']}", headers=hdr(tok))


# ---------- Admin flow ----------
class TestAdminFlow:
    def test_admin_create_and_delete_category(self, admin_session):
        tok = admin_session["token"]
        name = f"TEST_Cat_{uuid.uuid4().hex[:6]}"
        r = requests.post(f"{API}/admin/categories", json={"name": name, "description": "d", "color": "#123456"}, headers=hdr(tok))
        assert r.status_code == 200, r.text
        cat = r.json()
        assert cat["slug"] and cat["slug"] == cat["slug"].lower()
        assert cat["name"] == name
        cid = cat["id"]
        # Duplicate
        r2 = requests.post(f"{API}/admin/categories", json={"name": name}, headers=hdr(tok))
        assert r2.status_code == 400
        # Delete
        r3 = requests.delete(f"{API}/admin/categories/{cid}", headers=hdr(tok))
        assert r3.status_code == 200

    def test_admin_list_users_and_change_role(self, admin_session, writer_session):
        tok = admin_session["token"]
        r = requests.get(f"{API}/admin/users", headers=hdr(tok))
        assert r.status_code == 200
        users = r.json()
        assert any(u["user_id"] == writer_session["user_id"] for u in users)

        # Change role to writer (idempotent)
        r = requests.patch(f"{API}/admin/users/{writer_session['user_id']}/role", params={"role": "writer"}, headers=hdr(tok))
        assert r.status_code == 200

        # Invalid role
        r = requests.patch(f"{API}/admin/users/{writer_session['user_id']}/role", params={"role": "root"}, headers=hdr(tok))
        assert r.status_code == 400

    def test_admin_can_feature(self, admin_session, writer_session):
        # Writer creates article
        wtok = writer_session["token"]
        p = {"title": f"TEST_Feat_{uuid.uuid4().hex[:6]}", "content_html": "<p>x</p>", "category_slug": "bist", "status": "published"}
        r = requests.post(f"{API}/articles", json=p, headers=hdr(wtok))
        aid = r.json()["id"]
        # Admin features
        r = requests.patch(f"{API}/articles/{aid}", json={"featured": True}, headers=hdr(admin_session["token"]))
        assert r.status_code == 200
        assert r.json()["featured"] is True
        requests.delete(f"{API}/articles/{aid}", headers=hdr(admin_session["token"]))

    def test_writer_my_articles_isolated(self, writer_session):
        """Writer must not see system-seeded articles in /my/articles."""
        r = requests.get(f"{API}/my/articles", headers=hdr(writer_session["token"]))
        assert r.status_code == 200
        arts = r.json()
        for a in arts:
            assert a["author_id"] == writer_session["user_id"], f"Writer saw foreign article: {a.get('author_id')}"


# ---------- Uploads ----------
# Minimal 1x1 PNG
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6300010000000500010d0a2db40000000049454e44ae426082"
)


class TestUpload:
    def test_upload_no_auth(self):
        files = {"file": ("t.png", io.BytesIO(PNG_BYTES), "image/png")}
        r = requests.post(f"{API}/upload", files=files)
        assert r.status_code == 401

    def test_upload_png_and_download(self, writer_session):
        files = {"file": ("t.png", io.BytesIO(PNG_BYTES), "image/png")}
        r = requests.post(f"{API}/upload", files=files, headers=hdr(writer_session["token"]))
        assert r.status_code == 200, r.text
        data = r.json()
        assert "id" in data and "url" in data and "size" in data
        # Try download
        # url is /api/files/{path}
        full = f"{BASE_URL}{data['url']}"
        r2 = requests.get(full)
        assert r2.status_code == 200
        assert r2.headers.get("content-type", "").startswith("image/")

    def test_upload_wrong_type(self, writer_session):
        files = {"file": ("t.txt", io.BytesIO(b"hello"), "text/plain")}
        r = requests.post(f"{API}/upload", files=files, headers=hdr(writer_session["token"]))
        assert r.status_code == 400
