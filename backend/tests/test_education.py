"""Tests for Education gating and Education Members CRUD."""
import os
import uuid
import subprocess
import pytest
import requests
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
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


def hdr(tok):
    return {"Authorization": f"Bearer {tok}"}


def _seed_user(role: str, education_access: bool = False):
    uid = f"TEST_{role}_{uuid.uuid4().hex[:8]}"
    tok = f"TEST_tok_{role}_{uuid.uuid4().hex}"
    email = f"test_{role}_{uuid.uuid4().hex[:6]}@example.com"
    expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    script = f"""
    db.users.insertOne({{user_id:"{uid}",email:"{email}",name:"{role}",picture:"",role:"{role}",bio:"",education_access:{'true' if education_access else 'false'},created_at:"{now}"}});
    db.user_sessions.insertOne({{user_id:"{uid}",session_token:"{tok}",expires_at:"{expires}",created_at:"{now}"}});
    """
    mongo_eval(script)
    return {"user_id": uid, "token": tok, "email": email}


def _cleanup_user(u):
    mongo_eval(
        f'db.user_sessions.deleteMany({{user_id:"{u["user_id"]}"}});'
        f'db.users.deleteMany({{user_id:"{u["user_id"]}"}});'
        f'db.education_members.deleteMany({{email:"{u["email"]}"}});'
    )


@pytest.fixture(scope="module")
def admin_u():
    u = _seed_user("admin", education_access=True)
    yield u
    _cleanup_user(u)


@pytest.fixture(scope="module")
def writer_blocked():
    u = _seed_user("writer", education_access=False)
    yield u
    _cleanup_user(u)


@pytest.fixture(scope="module")
def writer_approved():
    u = _seed_user("writer", education_access=True)
    yield u
    _cleanup_user(u)


@pytest.fixture(scope="module")
def egitim_slug():
    """Return slug of an existing article in category 'egitim'."""
    r = requests.get(f"{API}/articles", params={"category": "egitim"})
    assert r.status_code == 200, r.text
    arts = r.json()
    assert len(arts) >= 1, "No education articles seeded"
    return arts[0]["slug"]


# ---------- Education Members CRUD ----------
class TestEducationMembers:
    def test_list_requires_admin(self, writer_blocked):
        r = requests.get(f"{API}/admin/education-members", headers=hdr(writer_blocked["token"]))
        assert r.status_code == 403

    def test_list_no_auth(self):
        r = requests.get(f"{API}/admin/education-members")
        assert r.status_code == 401

    def test_add_member_clean_json(self, admin_u):
        email = f"TEST_edu_{uuid.uuid4().hex[:6]}@example.com".lower()
        r = requests.post(f"{API}/admin/education-members",
                          json={"email": email, "note": "unit test"},
                          headers=hdr(admin_u["token"]))
        assert r.status_code == 200, r.text
        data = r.json()
        # Clean JSON, no ObjectId leak
        assert "_id" not in data
        assert data["email"] == email
        assert data["note"] == "unit test"
        assert isinstance(data["id"], str) and len(data["id"]) > 0
        assert "added_at" in data
        member_id = data["id"]

        # Appears in list
        r2 = requests.get(f"{API}/admin/education-members", headers=hdr(admin_u["token"]))
        assert r2.status_code == 200
        emails = [m["email"] for m in r2.json()]
        assert email in emails
        for m in r2.json():
            assert "_id" not in m

        # Duplicate email rejected
        r3 = requests.post(f"{API}/admin/education-members", json={"email": email},
                           headers=hdr(admin_u["token"]))
        assert r3.status_code == 400

        # Invalid email
        r4 = requests.post(f"{API}/admin/education-members", json={"email": "not-an-email"},
                           headers=hdr(admin_u["token"]))
        assert r4.status_code == 400

        # Delete
        r5 = requests.delete(f"{API}/admin/education-members/{member_id}", headers=hdr(admin_u["token"]))
        assert r5.status_code == 200

        # Verify removed
        r6 = requests.get(f"{API}/admin/education-members", headers=hdr(admin_u["token"]))
        emails2 = [m["email"] for m in r6.json()]
        assert email not in emails2

    def test_add_member_grants_existing_user_access(self, admin_u):
        # Create a fresh writer with education_access=false
        u = _seed_user("writer", education_access=False)
        try:
            # Verify /auth/me currently false
            r0 = requests.get(f"{API}/auth/me", headers=hdr(u["token"]))
            assert r0.status_code == 200
            assert r0.json().get("education_access") is False

            # Admin adds their email to education_members
            r = requests.post(f"{API}/admin/education-members",
                              json={"email": u["email"], "note": ""},
                              headers=hdr(admin_u["token"]))
            assert r.status_code == 200, r.text
            member_id = r.json()["id"]

            # Now /auth/me should reflect access=True immediately
            r2 = requests.get(f"{API}/auth/me", headers=hdr(u["token"]))
            assert r2.status_code == 200
            assert r2.json().get("education_access") is True

            # Delete member -> revokes access
            rd = requests.delete(f"{API}/admin/education-members/{member_id}", headers=hdr(admin_u["token"]))
            assert rd.status_code == 200

            r3 = requests.get(f"{API}/auth/me", headers=hdr(u["token"]))
            assert r3.json().get("education_access") is False
        finally:
            _cleanup_user(u)

    def test_patch_user_education_mirrors_members(self, admin_u):
        u = _seed_user("writer", education_access=False)
        try:
            # Enable via PATCH /admin/users/{id}/education
            r = requests.patch(f"{API}/admin/users/{u['user_id']}/education",
                               params={"enabled": "true"},
                               headers=hdr(admin_u["token"]))
            assert r.status_code == 200, r.text

            # Should now appear in education_members
            rl = requests.get(f"{API}/admin/education-members", headers=hdr(admin_u["token"]))
            emails = [m["email"] for m in rl.json()]
            assert u["email"] in emails

            # /auth/me true
            rm = requests.get(f"{API}/auth/me", headers=hdr(u["token"]))
            assert rm.json()["education_access"] is True

            # Disable
            r2 = requests.patch(f"{API}/admin/users/{u['user_id']}/education",
                                params={"enabled": "false"},
                                headers=hdr(admin_u["token"]))
            assert r2.status_code == 200

            rl2 = requests.get(f"{API}/admin/education-members", headers=hdr(admin_u["token"]))
            emails2 = [m["email"] for m in rl2.json()]
            assert u["email"] not in emails2

            rm2 = requests.get(f"{API}/auth/me", headers=hdr(u["token"]))
            assert rm2.json()["education_access"] is False
        finally:
            _cleanup_user(u)


# ---------- Article gating ----------
class TestEducationArticleGating:
    def test_no_auth_restricted(self, egitim_slug):
        r = requests.get(f"{API}/articles/{egitim_slug}")
        assert r.status_code == 200
        data = r.json()
        assert data.get("restricted") is True
        assert data.get("content_html") == ""

    def test_writer_no_access_restricted(self, egitim_slug, writer_blocked):
        r = requests.get(f"{API}/articles/{egitim_slug}", headers=hdr(writer_blocked["token"]))
        assert r.status_code == 200
        data = r.json()
        assert data.get("restricted") is True
        assert data.get("content_html") == ""

    def test_admin_full_content(self, egitim_slug, admin_u):
        r = requests.get(f"{API}/articles/{egitim_slug}", headers=hdr(admin_u["token"]))
        assert r.status_code == 200
        data = r.json()
        assert data.get("restricted") is False
        assert data.get("content_html") and len(data["content_html"]) > 0

    def test_writer_with_access_full_content(self, egitim_slug, writer_approved):
        r = requests.get(f"{API}/articles/{egitim_slug}", headers=hdr(writer_approved["token"]))
        assert r.status_code == 200
        data = r.json()
        assert data.get("restricted") is False
        assert data.get("content_html") and len(data["content_html"]) > 0

    def test_related_endpoint_still_works(self, egitim_slug):
        r = requests.get(f"{API}/articles/{egitim_slug}/related")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_articles_list_public_shows_egitim(self, egitim_slug):
        r = requests.get(f"{API}/articles", params={"category": "egitim"})
        assert r.status_code == 200
        arts = r.json()
        assert any(a["slug"] == egitim_slug for a in arts)
        # List never contains content_html
        for a in arts:
            assert "content_html" not in a

    def test_non_egitim_article_not_restricted(self):
        # Ensure gating doesn't affect other categories
        r = requests.get(f"{API}/articles", params={"category": "bist"})
        arts = r.json()
        if arts:
            slug = arts[0]["slug"]
            r2 = requests.get(f"{API}/articles/{slug}")
            assert r2.status_code == 200
            data = r2.json()
            assert data.get("restricted") is False
            assert data.get("content_html")


# ---------- Model regression: auth/me still exposes education_access ----------
class TestAuthMeEducationField:
    def test_me_has_education_access_field(self, writer_blocked):
        r = requests.get(f"{API}/auth/me", headers=hdr(writer_blocked["token"]))
        assert r.status_code == 200
        data = r.json()
        assert "education_access" in data
        assert data["education_access"] is False

    def test_me_admin_has_field(self, admin_u):
        r = requests.get(f"{API}/auth/me", headers=hdr(admin_u["token"]))
        assert r.status_code == 200
        assert r.json().get("education_access") is True
