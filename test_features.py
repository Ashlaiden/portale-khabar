"""Test detail page + like + comment features end-to-end (real session)."""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.config.settings")
import django
django.setup()
from apps.news.models import Article

BASE = "http://127.0.0.1:8765"

# 1. Get a real slug from the DB
art = Article.objects.first()
if not art:
    print("No article in DB"); raise SystemExit
slug = art.slug
print(f"Real slug: {slug!r}")
detail_url = art.get_absolute_url()
print(f"get_absolute_url: {detail_url!r}")


# Build an opener with a cookie jar so session + csrf cookies persist
import http.cookiejar
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def get(url):
    try:
        r = opener.open(BASE + url, timeout=10)
        return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("Referer", BASE + "/")
    # CSRF from cookie
    csrf = ""
    for c in jar:
        if c.name == "csrftoken":
            csrf = c.value
    if csrf:
        req.add_header("X-CSRFToken", csrf)
    try:
        r = opener.open(req, timeout=10)
        return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


# 2. Visit home first to get cookies (csrftoken + sessionid)
status, html = get("/")
print(f"HOME       -> {status}")
print(f"Cookies: {[c.name for c in jar]}")

# 3. Detail page using URL-encoded slug
encoded_slug = urllib.parse.quote(slug)
status, body = get(f"/news/{encoded_slug}/")
print(f"DETAIL     -> {status}")
if status >= 400:
    # show a snippet
    m = re.search(r"<pre class=\"exception_value\">(.+?)</pre>", body)
    if m:
        print(f"  err: {m.group(1)[:300]}")

art_id = art.id

# 4. Like
status, body = post(f"/like/{art_id}/", {"value": "like"})
print(f"LIKE       -> {status}")
try:
    print(f"  {json.loads(body)}")
except Exception:
    print(f"  {body[:200]}")

# 5. Comment
status, body = post(
    f"/comment/{art_id}/",
    {"name": "کاربر تست", "email": "t@t.com", "body": "نظر آزمایشی"},
)
print(f"COMMENT    -> {status}")
try:
    print(f"  {json.loads(body)}")
except Exception:
    print(f"  {body[:200]}")

print("\nDone.")
