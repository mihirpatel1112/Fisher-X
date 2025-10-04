
# Preparing CORS for later
#ToDo, fix this up later just adding it to prepare
from dataManagement.TempoDataManagement.TEMPO_Class import MAX_POINTS_PER_FILE
from fastapi import FASTAPI
from dataManagement.TempoDataManagement.TEMPO_Class import TEMPODataManager
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # PLACEHOLDER VALUES FOR DEVELOPMEN]T
    allow_origins = ["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

@app.get("/")
def read():
    return {"message": "TEST"}



core_manager = TEMPODataManager(cache_directory="./TEMPO_snap") # Initialise the manager to manage stuff

@app.get("api/cover")
def getLatest():
    return core_manager.get_latest_snapshot(max_points=10000)

@app.get("api/cover2")
def country():
    return core_manager.get_region_data(
        lat_bounds = (22,34),
        lon_bounds = (-125,-114),
        product_type = NO2_L3, 
    )
