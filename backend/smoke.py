# -*- coding: utf-8 -*-
"""去土改造回归测试：后端健康 + 页面 + 关键接口"""
import json, urllib.request

B = 'http://127.0.0.1:8000'
ok = fail = 0


def req(m, p, d=None, t=None, ct='application/json'):
    headers = {}
    if t:
        headers['Authorization'] = 'Bearer ' + t
    body = None
    if d is not None:
        body = json.dumps(d).encode()
    r = urllib.request.Request(B + p, method=m, headers=headers, data=body)
    try:
        x = urllib.request.urlopen(r, timeout=8)
        return x.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 'ERR'


def chk(n, cond):
    global ok, fail
    print(('PASS ' if cond else 'FAIL ') + n)
    ok += 1 if cond else 0
    fail += 0 if cond else 1


chk('health', req('GET', '/api/health') == 200)
for p in ['/', '/posts', '/gallery', '/messages', '/about', '/login',
          '/stats', '/diary', '/friends', '/archive']:
    chk('page ' + p, req('GET', p) == 200)

chk('summary', req('GET', '/api/stats/summary') == 200)


import urllib.request as u
r = u.Request(B + '/api/auth/login', method='POST',
              data=json.dumps({'username': 'admin', 'password': '123456'}).encode(),
              headers={'Content-Type': 'application/json'})
tok = json.loads(u.urlopen(r, timeout=8).read())['token']

r = u.Request(B + '/api/posts', method='POST',
              data=json.dumps({'title': '去土回归测试文', 'content': 'check', 'category_id': None,
                               'tag_names': []}).encode(),
              headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tok})
pid = json.loads(u.urlopen(r, timeout=8).read())['id']
chk('create post', bool(pid))
chk('delete post', req('DELETE', '/api/posts/' + str(pid), t=tok) in (200, 204))

chk('messages list', req('GET', '/api/messages') == 200)

print('== %d/%d ==' % (ok, ok + fail))
raise SystemExit(0 if fail == 0 else 1)
