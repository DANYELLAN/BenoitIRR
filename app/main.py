from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix='/api')
app.mount('/static', StaticFiles(directory='app/static'), name='static')


@app.get('/', include_in_schema=False)
def ui() -> FileResponse:
    return FileResponse('app/static/index.html')
