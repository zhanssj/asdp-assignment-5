"""Replace only this assignment's test service; restore the previous service on failure."""
import json
import subprocess
import sys
from pathlib import Path
from verify_http import verify

NAME = 'asdp5-analyzer'
BACKUP = NAME+'-previous'
LABEL = 'com.asdp.assignment'


def docker(*args, check=True):
    return subprocess.run(['docker',*args],check=check,text=True,capture_output=True)


def inspect(name):
    p = docker('inspect',name,check=False)
    return json.loads(p.stdout)[0] if p.returncode == 0 else None


def owned(info):
    if (info['Config'].get('Labels') or {}).get(LABEL) != '5':
        raise RuntimeError('Refusing to replace a container outside Assignment 5.')


def deploy(image, commit):
    if inspect(BACKUP): raise RuntimeError('Resolve the existing backup container before deploying.')
    old = inspect(NAME)
    if old:
        owned(old)
        docker('stop',NAME)
        docker('rename',NAME,BACKUP)
    try:
        docker('run','-d','--name',NAME,'--label',LABEL+'=5','--restart','unless-stopped',
               '--network','asdp5-ci','-p','127.0.0.1:8000:8000',image)
        evidence = verify('http://'+NAME+':8000',commit)
        info = inspect(NAME)
        evidence.update(image=image,imageId=info['Image'],deployment='passed')
    except Exception:
        failed = inspect(NAME)
        if failed:
            owned(failed); docker('rm','-f',NAME)
        if old:
            docker('rename',BACKUP,NAME); docker('start',NAME)
        raise
    if old: docker('rm',BACKUP)
    return evidence


if __name__ == '__main__':
    evidence = deploy(sys.argv[1],sys.argv[2])
    Path('infra/build/deployment.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))
