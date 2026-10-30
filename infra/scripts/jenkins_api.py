"""Local Jenkins control and evidence collection without exposing its password."""
import base64
import http.cookiejar
import json
import sys
import time
import urllib.request
from pathlib import Path

INFRA = Path(__file__).resolve().parents[1]
BASE = 'http://localhost:8081/'
JOB = 'job/asdp-assignment-5/'


def client():
    password = (INFRA/'.local/admin-password.txt').read_text().strip()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    opener.addheaders = [('Authorization','Basic '+base64.b64encode(('admin:'+password).encode()).decode())]
    return opener


def get(opener,path):
    with opener.open(BASE+path,timeout=20) as r: return json.load(r)


def post(opener,path):
    crumb = get(opener,'crumbIssuer/api/json')
    req = urllib.request.Request(BASE+path,data=b'',headers={crumb['crumbRequestField']:crumb['crumb']})
    with opener.open(req,timeout=20) as r: return dict(status=r.status,location=r.headers.get('Location'))


if __name__ == '__main__':
    opener = client()
    action = sys.argv[1] if len(sys.argv)>1 else 'status'
    if action == 'build': print(json.dumps(post(opener,JOB+'build')))
    elif action == 'status':
        print(json.dumps(get(opener,JOB+'api/json?tree=name,lastBuild[number,result,building,url],queueItem[id]')))
    elif action == 'evidence':
        result = get(opener,JOB+'lastCompletedBuild/api/json')
        build_path = JOB+str(result['number'])+'/'
        stages = get(opener,build_path+'wfapi/describe')
        tests = get(opener,build_path+'testReport/api/json')
        root = INFRA/'build'; root.mkdir(exist_ok=True)
        for name, data in [('jenkins-build',result),('jenkins-stages',stages),('jenkins-tests',tests)]:
            (root/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
        for name in ('deployment.json','smoke.json','source-commit.txt','junit.xml'):
            with opener.open(BASE+build_path+'artifact/infra/build/'+name,timeout=20) as r:
                (root/name).write_bytes(r.read())
        print(json.dumps(dict(build=result['number'],result=result['result'],
            stages=[dict(name=s['name'],status=s['status']) for s in stages['stages']],
            totalTests=sum(len(s.get('cases',[])) for s in tests.get('suites',[])),failedTests=tests['failCount'])))
    elif action == 'wait':
        for _ in range(45):
            result = get(opener,JOB+'api/json?tree=lastBuild[number,result,building],queueItem[id]')
            build = result.get('lastBuild')
            if build and not build['building'] and not result.get('queueItem'): break
            time.sleep(1)
        print(json.dumps(result))
    else: raise SystemExit('Use build, status, wait or evidence.')
