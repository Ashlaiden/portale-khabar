import urllib.request, urllib.parse, http.cookiejar, re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Step 1: GET login page
r = opener.open('http://127.0.0.1:8765/admin/login/')
html = r.read().decode()
print('Login page:', r.status)

# Extract CSRF
m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
if not m:
    print('ERROR: CSRF token not found')
    exit(1)
csrf = m.group(1)
print('CSRF:', csrf[:30])

# Step 2: POST login
data = urllib.parse.urlencode({
    'csrfmiddlewaretoken': csrf,
    'username': 'admin',
    'password': 'admin12345',
    'next': '/admin/'
}).encode()
req = urllib.request.Request(
    'http://127.0.0.1:8765/admin/login/',
    data=data,
    headers={'Referer': 'http://127.0.0.1:8765/admin/login/'}
)
r = opener.open(req)
body = r.read().decode()
print('Login POST:', r.status)
print('Redirected to:', r.url)
print('Has RTL:', 'rtl' in body.lower())
print('Has Vazirmatn:', 'Vazirmatn' in body)
print('Has custom_admin.css:', 'custom_admin.css' in body)
