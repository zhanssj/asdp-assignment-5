import hashlib
import math
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
RAW = b'temperature_C\n20\n22\n24\n26\n28\n'


def test_health_and_commit(monkeypatch):
    monkeypatch.setenv('SOURCE_COMMIT','abc123')
    assert client.get('/health').json() == dict(status='ok',applicationVersion='1.0.0',sourceCommit='abc123')


def test_actual_application_interface():
    assert 'Smart City Sensor' in client.get('/').text
    assert client.get('/app.js').status_code == 200
    assert client.get('/styles.css').status_code == 200


def test_multipart_preview():
    r = client.post('/api/datasets/preview', files={'file':('s.csv',RAW,'text/csv')})
    assert r.status_code == 200
    assert r.json()['numericColumns'] == ['temperature_C']


def test_multipart_analysis_and_provenance():
    r = client.post('/api/analysis', files={'file':('C:\\data\\s.csv',RAW,'text/csv')},data={'column':'temperature_C','unit':'C'})
    assert r.status_code == 200
    data = r.json()
    assert data['filename'] == 's.csv'
    assert data['inputSha256'] == hashlib.sha256(RAW).hexdigest()
    assert data['statistics']['sampleStandardDeviation'] == pytest.approx(math.sqrt(10))
    assert data['statistics']['mean'] == 24


@pytest.mark.parametrize('filename,raw,data', [('s.txt',RAW,{'column':'temperature_C'}),('s.csv',b'',{'column':'temperature_C'}),('s.csv',RAW,{}),('s.csv',RAW,{'column':'absent'})])
def test_invalid_requests_return_actionable_error(filename,raw,data):
    r = client.post('/api/analysis', files={'file':(filename,raw)},data=data)
    assert r.status_code == 400
    assert r.json()['message']


def test_missing_file():
    assert client.post('/api/datasets/preview').status_code == 400


def test_oversize_upload():
    r = client.post('/api/datasets/preview',files={'file':('s.csv',b'x'*(5*1024*1024+1))})
    assert r.status_code == 413
