import urllib.request, http.cookiejar, re, sys

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

pages = [
    ('Home', 'http://127.0.0.1:8765/'),
    ('News List', 'http://127.0.0.1:8765/news/'),
    ('RSS News', 'http://127.0.0.1:8765/rss-news/'),
    ('About', 'http://127.0.0.1:8765/about/'),
    ('Contact', 'http://127.0.0.1:8765/contact/'),
    ('Search', 'http://127.0.0.1:8765/search/?q=test'),
]

# Login first to get session for like tokens
r = opener.open('http://127.0.0.1:8765/admin/login/')
html = r.read().decode()
m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
csrf = m.group(1)
data = ('csrfmiddlewaretoken=' + csrf + '&username=admin&password=admin12345&next=/admin/').encode()
req = urllib.request.Request('http://127.0.0.1:8765/admin/login/', data=data)
opener.open(req)

all_ok = True
for name, url in pages:
    try:
        r = opener.open(url)
        body = r.read().decode()
        status = r.status
        has_glass = 'glass' in body
        has_rtl = 'rtl' in body
        has_vazir = 'Vazirmatn' in body
        # Check for common errors
        has_error = 'Server Error' in body or 'Traceback' in body
        flag = 'OK' if not has_error else 'ERROR'
        if has_error:
            all_ok = False
        print(f'  [{flag}] {name:15s} -> {status} | glass={has_glass} rtl={has_rtl} vazir={has_vazir}')
    except Exception as e:
        all_ok = False
        print(f'  [FAIL] {name:15s} -> {e}')

# Also test article detail (need to find an article slug)
try:
    r = opener.open('http://127.0.0.1:8765/')
    html = r.read().decode()
    m = re.search(r'href="(/news/\d+/[^"]+)"', html)
    if m:
        detail_url = 'http://127.0.0.1:8765' + m.group(1)
        r = opener.open(detail_url)
        body = r.read().decode()
        has_like = 'data-article-id' in body
        has_comment = 'comment-form' in body
        has_error = 'Server Error' in body or 'Traceback' in body
        flag = 'OK' if not has_error else 'ERROR'
        if has_error:
            all_ok = False
        print(f'  [{flag}] Article Detail  -> {r.status} | like={has_like} comment={has_comment}')
    else:
        print('  [SKIP] No article links found on home page')
except Exception as e:
    all_ok = False
    print(f'  [FAIL] Article Detail  -> {e}')

print()
print('ALL PAGES OK' if all_ok else 'SOME PAGES FAILED')
