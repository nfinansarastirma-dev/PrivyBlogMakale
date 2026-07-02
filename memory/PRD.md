# PrivyAlgo Blog — PRD

## Original Problem Statement
Blog site inspired by NewsCrunch demo layout (https://demo-newscrunch.spicethemes.com/demo-pro-three/) but styled to match https://privyalgo.com aesthetic. The blog will host articles and educational content for PrivyAlgo (BIST + Wall Street quantitative finance platform). Requires admin panel for management and writer panel for authoring articles.

## User Choices (from initial gathering)
- Auth: Emergent Google Auth
- Editor: WYSIWYG rich text editor (Tiptap)
- Images: File upload via Emergent Object Storage
- Roles: Admin + Writer
- Extras: Categories & tags, Search, Featured articles

## Personas
- **Visitor**: reads articles, browses categories, searches for content
- **Writer**: signs in via Google → creates/edits own articles → uploads images → can save draft or publish
- **Admin**: full CMS — manages all articles, categories, users; can feature articles; promotes writers to admin

## Architecture
- **Backend**: FastAPI + Motor(MongoDB). Emergent Google Auth session exchange. Emergent Object Storage for images. All routes under `/api`.
- **Frontend**: React 19 + React Router 7 + TailwindCSS + Shadcn UI + Tiptap 3. Dark theme, terminal aesthetic.
- **Data**: `users`, `user_sessions`, `articles`, `categories`, `files` collections. Custom `user_id`, all reads use `{"_id": 0}` projection.

## Design
- Dark PrivyAlgo aesthetic (#050505 bg, #10B981 primary/AL, #EF4444 SAT, #F59E0B accent)
- Fonts: Outfit (headings), IBM Plex Sans (body), JetBrains Mono (tickers/tags)
- Ticker marquee at top with BIST/US mock signals
- Magazine layout: Hero + Trending sidebar + Category sections
- Zero border radius, high-contrast, terminal corners on cards

## What's Implemented (2026-02)
- [x] Emergent Google Auth (session exchange, cookie + Bearer support)
- [x] First-user-becomes-admin logic (or via `ADMIN_EMAILS` env)
- [x] Categories CRUD (6 defaults seeded: BIST, Wall Street, Opsiyonlar, Kripto, Sentiment, Eğitim)
- [x] Articles CRUD with draft/published status, slug generation, view counter
- [x] Featured articles (admin-only toggle)
- [x] Tags array on articles
- [x] Full-text search across title/excerpt/content/tags
- [x] Public blog: Home (hero + trending sidebar + category sections), Article detail, Category page, Search page
- [x] Tiptap WYSIWYG editor with image upload, links, headings, lists, quotes, code
- [x] Cover image upload
- [x] Ticker marquee (mock financial data endpoint)
- [x] Admin dashboard: articles, users (role mgmt), categories
- [x] Writer dashboard: own articles only
- [x] 5 demo articles seeded across categories
- [x] Backend 23/23 tests passing

## Backlog / P1
- [ ] Real BIST/US ticker data feed (currently mock)
- [ ] Writer approval workflow (currently open publish policy)
- [ ] Rich editor: tables, YouTube embed, code syntax highlighting
- [ ] Newsletter subscription form → send digest via SendGrid/Resend
- [ ] SEO: meta tags per article, sitemap.xml, RSS feed
- [ ] Comments (Disqus or native)
- [ ] Reading progress bar on article
- [ ] Related-by-tag improvements
- [ ] Article scheduling (published_at future)
- [ ] i18n (currently Turkish only)

## P2
- [ ] Analytics dashboard (views per article, top authors)
- [ ] Author profile pages
- [ ] Draft auto-save
- [ ] Bulk operations in admin (multi-select delete/publish)
