import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8765"
PATHS = [
    ("HOME", "/"),
    ("NEWS", "/news/"),
    ("RSS_NEWS", "/rss-news/"),
    ("ABOUT", "/about/"),
    ("CONTACT", "/contact/"),
    ("SEARCH", "/search/?q=test"),
    ("ADMIN", "/admin/"),
    ("CATEGORY", "/news/category/political/"),
]

for name, path in PATHS:
    try:
        r = urllib.request.urlopen(BASE + path, timeout=10)
        print(f"{name:12} -> {r.status}")
    except urllib.error.HTTPError as e:
        print(f"{name:12} -> {e.code} ERROR")
    except Exception as e:
        print(f"{name:12} -> ERR {e}")
