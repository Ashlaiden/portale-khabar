import urllib.request, http.cookiejar, re, sys

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login first to get session
r = opener.open('http://127.0.0.1:8765/admin/login/')
html = r.read().decode()
m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
csrf = m.group(1)
data = ('csrfmiddlewaretoken=' + csrf + '&username=admin&password=admin12345&next=/admin/').encode()
req = urllib.request.Request('http://127.0.0.1:8765/admin/login/', data=data)
opener.open(req)

# Test article detail
url = 'http://127.0.0.1:8765/news/%D9%86%D8%B4%D8%B3%D8%AA-%D9%85%D8%B4%D8%AA%D8%B1%DA%A9-%D8%AF%D9%88%D9%84%D8%AA-%D9%88-%D8%A8%D8%AE%D8%B4-%D8%AE%D8%B5%D9%88%D8%B5%DB%8C-%D8%A8%D8%B1%D8%A7%DB%8C-%DA%A9%D9%86%D8%AA%D8%B1%D9%84-%D8%AA%D9%88%D8%B1%D9%85/'
r = opener.open(url)
body = r.read().decode()
print(f'Status: {r.status}')
print(f'Has like widget: {"data-article-id" in body}')
print(f'Has comment form: {"comment-form" in body}')
print(f'Has content: {"content" in body}')
print(f'Has sidebar: {"sidebar_news" in body or "آخرین اخبار" in body}')
print(f'Has glass: {"glass" in body}')
print(f'Has related section: {"اخبار مرتبط" in body or "related_news" in body}')
print(f'Has error: {"Server Error" in body or "Traceback" in body}')

# Check article count on page
view_count = body.count('بازدید')
print(f'View badge count: {view_count}')
