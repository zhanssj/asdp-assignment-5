import os
from pathlib import Path
from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app import __version__
from app.analysis import MAX_BYTES, DataError, parse_csv, preview, analyze

app = FastAPI(title='Smart City Sensor Data Analyzer', version=__version__)
STATIC = Path(__file__).parent / 'static'


@app.exception_handler(DataError)
async def data_error(request: Request, exc: DataError):
    return JSONResponse(status_code=exc.status_code, content={'message': str(exc)})


@app.exception_handler(RequestValidationError)
async def request_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={'message': 'Supply a CSV file and all required form fields.'})


async def dataset(file: UploadFile):
    filename = (file.filename or 'dataset.csv').replace('\\', '/').split('/')[-1]
    filename = ''.join(c for c in filename if ord(c) >= 32 and not 127 <= ord(c) <= 159)[-200:]
    if not filename.lower().endswith('.csv'):
        raise DataError('Choose a file with the .csv extension.')
    try:
        content = await file.read(MAX_BYTES + 1)
    finally:
        await file.close()
    return parse_csv(content), filename


@app.get('/health')
def health():
    return dict(status='ok', applicationVersion=__version__, sourceCommit=os.getenv('SOURCE_COMMIT', 'development'))


@app.post('/api/datasets/preview')
async def dataset_preview(file: UploadFile = File(...)):
    data, filename = await dataset(file)
    return preview(data, filename)


@app.post('/api/analysis')
async def analysis(file: UploadFile = File(...), column: str = Form(...), unit: str = Form('')):
    data, filename = await dataset(file)
    result = analyze(data, filename, column, unit, __version__)
    result['sourceCommit'] = os.getenv('SOURCE_COMMIT', 'development')
    return result


@app.get('/')
def index():
    return FileResponse(STATIC / 'index.html')


app.mount('/', StaticFiles(directory=STATIC), name='static')
