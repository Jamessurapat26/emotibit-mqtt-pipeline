from fastapi import FastAPI
from endpoint.predictEnpoint import router as predictRouter
from config.cors import add_cors_middleware

app = FastAPI()
app.include_router(predictRouter, prefix="/predict", tags=["predict"])  # Add prefix here
add_cors_middleware(app) 

@app.get("/")
def read_root():
    return {"Hello": "World"}
