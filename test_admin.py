"""Quick admin panel test."""
import os, urllib.parse, urllib.request, urllib.error, http.cookiejar

BASE = "http://127.0.0.1:8765"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

# 1. Get login page + CSRF
r = opener.open(BASE + "/admin/login/", timeout=10)
html = r.read().decode(errors="replace")
csrf = ""
import re
m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
if m:
    csrf = m.group(1)

# 2. POST login
body = urllib.parse.urlencode({
    "csrfmiddlewaretoken": csrf,
    "username": "admin",
    "password": "admin12345",
    "next": "/admin/",
}).encode()
req = urllib.request.Request(BASE + "/admin/login/", data=body, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")
req.add_header("Referer", BASE + "/admin/login/")
r = opener.open(req, timeout=10)
print(f"LOGIN      -> {r.status} -> {r.url}")
print(f"  Final URL: {r.url}")

# 3. Try admin index
r = opener.open(BASE + "/admin/", timeout=10)
print(f"ADMIN INDEX -> {r.status}")
has_rtl = "rtl" in r.read().decode(errors="replace").lower()
print(f"  Has RTL: {has_rtl}")

# 4. Try article list
r = opener.open(BASE + "/admin/news/article/", timeout=10)
body = r.read().decode(errors="replace")
has_jazzmin = "jazzmin" in body.lower() or "brand" in body.lower()
has_dark = "darkly" in body.lower() or "dark" in body.lower()
print(f"ARTICLE LIST -> {r.status}")
print(f"  Has dark theme: {has_dark}")

# 5. Try RSS feed list
r = opener.open(BASE + "/admin/news/rssfeed/", timeout=10)
print(f"RSS FEED LIST -> {r.status}")
