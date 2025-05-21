from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def add_cors_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # เปลี่ยนเป็น ["https://your-frontend.com"] ใน production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )