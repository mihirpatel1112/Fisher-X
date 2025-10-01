
# Preparing CORS for later
#ToDo, fix this up later just adding it to prepare

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # PLACEHOLDER VALUES FOR DEVELOPMENT
    allow_origins = ["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

@app.get("/")
def read():
    return {"message": "TEST"}
