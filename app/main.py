from fastapi import FastAPI

from routes import router
from config import settings
from database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix='/api')
