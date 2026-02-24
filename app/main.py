from fastapi import FastAPI

from app.api.routes import router
from app.config import settings
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix='/api')
