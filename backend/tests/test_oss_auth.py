"""
Backend tests for OSS auth refactor (iteration_4).
Covers: JWT auth, register/login/me, forgot/reset password, change password,
profile, google oauth stubs, RBAC, articles, uploads.
"""
import io
import os
import uuid
import struct
import zlib
import pytest
import requests
from pathlib import Path

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://privyalgo-blog.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

SUPER_EMAIL = "nfinansarastirma@gmail.com"
SUPER_PW = "Admin123!"

# unique test user email per session
TEST_USER_EMAIL = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PW = "TestPass123!"


def _png_bytes():
    """Return a 1x1 transparent PNG."""
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    raw = b"\x00\x00\x00\x00\x00"
    idat = zlib.compress(raw)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def admin_token(s):
    r = s.post(f"{API}/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PW})
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def user_token(s):
    r = s.post(f"{API}/auth/register", json={
        "email": TEST_USER_EMAIL, "password": TEST_USER_PW, "name": "Test User"
    })
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


# ----------------------- AUTH: login/me -----------------------
class TestAuthLogin:
    def test_super_admin_login(self, s):
        r = s.post(f"{API}/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PW})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["must_change_password"] is True
        assert data["user"]["email"] == SUPER_EMAIL
        assert "password_hash" not in data["user"]

    def test_login_wrong_password(self, s):
        r = s.post(f"{API}/auth/login", json={"email": SUPER_EMAIL, "password": "wrongpw123"})
        assert r.status_code == 401
        assert "Geçersiz" in r.json().get("detail", "")

    def test_me_with_token(self, s, admin_token):
        r = s.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        d = r.json()
        assert d["email"] == SUPER_EMAIL
        assert "password_hash" not in d

    def test_me_without_token(self, s):
        r = s.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_me_malformed_token(self, s):
        r = s.get(f"{API}/auth/me", headers={"Authorization": "Bearer not-a-jwt-token"})
        assert r.status_code == 401


# ----------------------- AUTH: register -----------------------
class TestAuthRegister:
    def test_register_new_user(self, user_token):
        # relies on fixture success
        assert user_token and len(user_token) > 10

    def test_register_duplicate(self, s):
        r = s.post(f"{API}/auth/register", json={
            "email": TEST_USER_EMAIL, "password": TEST_USER_PW, "name": "Dup"
        })
        assert r.status_code == 400

    def test_register_short_password(self, s):
        r = s.post(f"{API}/auth/register", json={
            "email": f"short_{uuid.uuid4().hex[:6]}@example.com",
            "password": "short",
            "name": "Short",
        })
        assert r.status_code == 422

    def test_new_user_role_is_user(self, s, user_token):
        r = s.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 200
        assert r.json()["role"] == "user"


# ----------------------- AUTH: forgot/reset -----------------------
class TestForgotResetPassword:
    def test_forgot_unknown_email(self, s):
        r = s.post(f"{API}/auth/forgot-password", json={"email": "nonexistent-xyz-999@example.com"})
        assert r.status_code == 200
        assert r.json() == {"ok": True}

    def test_forgot_reset_flow_and_restore(self, s):
        # register a temp user for the reset flow
        temp_email = f"reset_{uuid.uuid4().hex[:8]}@example.com"
        temp_pw = "OrigPass123!"
        new_pw = "NewPass123!"
        r = s.post(f"{API}/auth/register", json={"email": temp_email, "password": temp_pw, "name": "R"})
        assert r.status_code == 200

        r = s.post(f"{API}/auth/forgot-password", json={"email": temp_email})
        assert r.status_code == 200
        data = r.json()
        assert data.get("ok") is True
        assert "dev_reset_url" in data, f"expected dev_reset_url, got {data}"
        # Extract token
        url = data["dev_reset_url"]
        assert "token=" in url
        token = url.split("token=", 1)[1]

        # Reset
        r = s.post(f"{API}/auth/reset-password", json={"token": token, "new_password": new_pw})
        assert r.status_code == 200, r.text

        # Login with new
        r = s.post(f"{API}/auth/login", json={"email": temp_email, "password": new_pw})
        assert r.status_code == 200

        # Old password should fail
        r = s.post(f"{API}/auth/login", json={"email": temp_email, "password": temp_pw})
        assert r.status_code == 401

    def test_reset_with_invalid_token(self, s):
        r = s.post(f"{API}/auth/reset-password", json={"token": "invalid-jwt", "new_password": "SomePass123!"})
        assert r.status_code == 400

    def test_access_token_cannot_be_used_as_reset(self, s, user_token):
        # user_token is 'access' type
        r = s.post(f"{API}/auth/reset-password", json={"token": user_token, "new_password": "AnotherPass123!"})
        assert r.status_code == 400


# ----------------------- AUTH: change-password -----------------------
class TestChangePassword:
    def test_change_password_requires_auth(self, s):
        r = s.post(f"{API}/auth/change-password", json={"current_password": "x", "new_password": "abcdefgh"})
        assert r.status_code == 401

    def test_change_password_wrong_current(self, s, user_token):
        r = s.post(f"{API}/auth/change-password",
                   json={"current_password": "wrong-pw", "new_password": "BrandNewPw123!"},
                   headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 401

    def test_change_password_success(self, s):
        # Use a dedicated temp user to avoid mutating shared user_token
        email = f"cp_{uuid.uuid4().hex[:8]}@example.com"
        pw = "OrigPass123!"
        newpw = "ChangedPw123!"
        r = s.post(f"{API}/auth/register", json={"email": email, "password": pw, "name": "CP"})
        tok = r.json()["access_token"]
        r = s.post(f"{API}/auth/change-password",
                   json={"current_password": pw, "new_password": newpw},
                   headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200
        # login with new
        r = s.post(f"{API}/auth/login", json={"email": email, "password": newpw})
        assert r.status_code == 200


# ----------------------- AUTH: profile -----------------------
class TestProfile:
    def test_update_profile(self, s, user_token):
        r = s.patch(f"{API}/auth/profile",
                    json={"name": "Updated Name", "bio": "hello bio"},
                    headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 200
        d = r.json()
        assert d["name"] == "Updated Name"
        assert d["bio"] == "hello bio"
        assert "password_hash" not in d


# ----------------------- Google OAuth stubs -----------------------
class TestGoogleOAuth:
    def test_google_status_disabled(self, s):
        r = s.get(f"{API}/auth/google/status")
        assert r.status_code == 200
        assert r.json() == {"enabled": False}

    def test_google_login_disabled(self, s):
        r = s.get(f"{API}/auth/google/login", allow_redirects=False)
        assert r.status_code == 503


# ----------------------- RBAC -----------------------
class TestRBAC:
    def test_user_cannot_list_users(self, s, user_token):
        r = s.get(f"{API}/admin/users", headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 403

    def test_admin_can_list_users(self, s, admin_token):
        r = s.get(f"{API}/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200
        users = r.json()
        assert isinstance(users, list)
        assert all("password_hash" not in u for u in users)

    def test_super_admin_role_protected(self, s, admin_token):
        # find super admin id
        r = s.get(f"{API}/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        super_id = next(u["user_id"] for u in r.json() if u["email"] == SUPER_EMAIL)
        r = s.patch(f"{API}/admin/users/{super_id}/role?role=user",
                    headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 400

    def test_super_admin_delete_protected(self, s, admin_token):
        r = s.get(f"{API}/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        super_id = next(u["user_id"] for u in r.json() if u["email"] == SUPER_EMAIL)
        r = s.delete(f"{API}/admin/users/{super_id}",
                     headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 400


# ----------------------- Articles -----------------------
EDU_SLUG = "opsiyon-101-greeks-delta-gamma-theta-vega-nedir"


class TestArticles:
    def test_articles_list(self, s):
        r = s.get(f"{API}/articles")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_education_article_restricted_without_auth(self, s):
        r = s.get(f"{API}/articles/{EDU_SLUG}")
        if r.status_code == 404:
            pytest.skip("education article not present")
        assert r.status_code == 200
        d = r.json()
        assert d.get("restricted") is True
        assert d.get("content_html") == ""

    def test_education_article_admin_full_content(self, s, admin_token):
        r = s.get(f"{API}/articles/{EDU_SLUG}",
                  headers={"Authorization": f"Bearer {admin_token}"})
        if r.status_code == 404:
            pytest.skip("education article not present")
        assert r.status_code == 200
        d = r.json()
        assert d.get("restricted") is False
        assert len(d.get("content_html", "")) > 0

    def test_user_cannot_publish_article(self, s, user_token, admin_token):
        # Create a draft as user
        # First need a category
        cats = s.get(f"{API}/categories").json()
        assert cats
        r = s.post(f"{API}/articles",
                   json={"title": f"TEST Article {uuid.uuid4().hex[:6]}",
                         "content_html": "<p>hi</p>",
                         "category_slug": cats[0]["slug"],
                         "status": "draft"},
                   headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 200, r.text
        article_id = r.json()["id"]
        # Try to publish
        r = s.patch(f"{API}/articles/{article_id}",
                    json={"status": "published"},
                    headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 403
        # cleanup
        s.delete(f"{API}/articles/{article_id}", headers={"Authorization": f"Bearer {admin_token}"})


# ----------------------- Seed -----------------------
class TestSeed:
    def test_categories_seeded(self, s):
        r = s.get(f"{API}/categories")
        assert r.status_code == 200
        cats = r.json()
        assert len(cats) >= 6


# ----------------------- Uploads -----------------------
class TestUploads:
    def test_upload_requires_auth(self, s):
        r = s.post(f"{API}/upload", files={"file": ("t.png", _png_bytes(), "image/png")})
        assert r.status_code == 401

    def test_upload_png_and_download(self, s, user_token):
        png = _png_bytes()
        r = s.post(f"{API}/upload",
                   files={"file": ("test.png", png, "image/png")},
                   headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert "id" in d
        assert "url" in d and d["url"].startswith("/api/files/")
        assert d["size"] == len(png)

        # Extract user_id and filename from url: /api/files/{user_id}/{uuid}.png
        rel = d["url"][len("/api/files/"):]
        parts = rel.split("/")
        assert len(parts) == 2
        user_id, filename = parts
        assert filename.endswith(".png")

        # verify on disk
        disk_path = Path(f"/app/backend/uploads/{user_id}/{filename}")
        assert disk_path.exists(), f"file not saved to disk: {disk_path}"

        # download via public URL
        r2 = s.get(f"{BASE}{d['url']}")
        assert r2.status_code == 200
        assert r2.headers.get("content-type", "").startswith("image/png")
        assert r2.content == png

    def test_upload_wrong_content_type(self, s, user_token):
        r = s.post(f"{API}/upload",
                   files={"file": ("a.txt", b"hello", "text/plain")},
                   headers={"Authorization": f"Bearer {user_token}"})
        assert r.status_code == 400


# ----------------------- Teardown: restore super admin password -----------------------
def test_zz_restore_super_admin_password():
    """Ensure super admin login still works with Admin123! after all tests."""
    r = requests.post(f"{API}/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PW})
    assert r.status_code == 200, "Super admin password was mutated; needs manual restore!"
