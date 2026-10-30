"""Check a running image with independent HTTP and numerical expectations."""
import hashlib
import json
import math
import sys
import time
import urllib.request
from pathlib import Path


def verify(base, expected_commit, attempts=30):
    last = None
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(base + '/health', timeout=3) as r:
                health = json.load(r)
            assert health['status'] == 'ok'
            assert health['sourceCommit'] == expected_commit, health
            break
        except Exception as exc:
            last = exc
            time.sleep(1)
    else:
        raise RuntimeError(f'Health check failed: {last}')
    raw = b'temperature_C\n20\n22\n24\n26\n28\n'
    boundary = 'asdp5-evidence-boundary'
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="column"\r\n\r\ntemperature_C\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="reference.csv"\r\n'
            'Content-Type: text/csv\r\n\r\n').encode() + raw + f'\r\n--{boundary}--\r\n'.encode()
    req = urllib.request.Request(base+'/api/analysis', data=body,
        headers={'Content-Type': 'multipart/form-data; boundary='+boundary})
    with urllib.request.urlopen(req, timeout=10) as r:
        result = json.load(r)
    assert result['statistics']['mean'] == 24
    assert result['statistics']['median'] == 24
    assert math.isclose(result['statistics']['sampleStandardDeviation'], math.sqrt(10), rel_tol=1e-12)
    assert result['inputSha256'] == hashlib.sha256(raw).hexdigest()
    assert result['sourceCommit'] == expected_commit
    with urllib.request.urlopen(base+'/',timeout=5) as r:
        assert 'Smart City Sensor' in r.read().decode()
    return dict(health=health, referenceMean=24, referenceMedian=24,
                referenceSampleDeviation=result['statistics']['sampleStandardDeviation'],
                inputSha256=result['inputSha256'], httpChecks='passed')


if __name__ == '__main__':
    data = verify(sys.argv[1].rstrip('/'), sys.argv[2])
    output = json.dumps(data, indent=2)
    if len(sys.argv) > 3: Path(sys.argv[3]).write_text(output+'\n',encoding='utf-8')
    print(output)
