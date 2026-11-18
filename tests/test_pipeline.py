import json
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient
import app as app_module

client = TestClient(app_module.app)
CONFIG = json.loads(Path('config.json').read_text())


def test_dataset_valid():
    df = pd.read_csv('dataset/train.csv')
    assert len(df) >= 100
    assert set(CONFIG['features'] + ['label']).issubset(df.columns)


def test_metrics_file():
    m = json.loads(Path('artifacts/metrics.json').read_text())
    for k in ['student_id', 'accuracy', 'training_rows', 'model_version', 'git_sha']:
        assert k in m
    assert m['accuracy'] >= 0.5


def test_metrics_endpoint():
    r = client.get('/metrics')
    assert r.status_code == 200
    assert r.json()['student_id'] == CONFIG['student_id']


def test_predict_endpoint():
    rec = {f: 0 for f in CONFIG['features']}
    r = client.post('/predict', json={'records': [rec]})
    assert r.status_code == 200
    assert len(r.json()['predictions']) == 1