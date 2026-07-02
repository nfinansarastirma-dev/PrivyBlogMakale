Auth-Gated App Testing Playbook (PrivyAlgo Blog)

Step 1: Create Test User & Session (as admin)
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
var email = 'admin.test.' + Date.now() + '@example.com';
db.users.insertOne({
  user_id: userId,
  email: email,
  name: 'Admin Test',
  picture: '',
  role: 'admin',
  bio: '',
  created_at: new Date().toISOString()
});
var expires = new Date(Date.now() + 7*24*60*60*1000);
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: expires.toISOString(),
  created_at: new Date().toISOString()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
print('Email: ' + email);
"

Step 2: Test Backend API
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
curl -s -X GET "$API_URL/api/auth/me" -H "Authorization: Bearer YOUR_SESSION_TOKEN"

# Create an article
curl -s -X POST "$API_URL/api/articles" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN" \
  -d '{"title":"Test Makale","excerpt":"özet","content_html":"<p>içerik</p>","category_slug":"bist","tags":["gex"],"status":"published"}'

# List articles publicly
curl -s "$API_URL/api/articles?limit=5"

Step 3: Browser Testing
await page.context.add_cookies([{
    "name": "session_token",
    "value": "YOUR_SESSION_TOKEN",
    "domain": "privyalgo-blog.preview.emergentagent.com",
    "path": "/",
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
}]);

Checklist
- User has user_id (custom UUID)
- Session user_id matches user.user_id
- Queries use {"_id": 0}
- /api/auth/me returns user
- /api/articles list works publicly
- /api/upload requires auth
- Admin can create categories, promote users, feature articles
- Writers only see their own articles in /api/my/articles
