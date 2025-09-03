from fastapi import FastAPI
from .router_line import router as line_router

app = FastAPI(title="LINE Bot (FastAPI + MySQL)")

# Routers
app.include_router(line_router)
