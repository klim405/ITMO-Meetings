import os
from pathlib import Path

from fastapi import APIRouter
from starlette.responses import HTMLResponse, FileResponse

router = APIRouter()


@router.get('/{p:path}',  response_class=FileResponse)
def main_page(p):
    BASE_DIR = Path(os.getcwd()) / 'build'
    target_file = BASE_DIR / p
    if target_file.exists() and target_file.is_file() and False:
        return FileResponse(target_file)
    return FileResponse(BASE_DIR / 'index.html')
