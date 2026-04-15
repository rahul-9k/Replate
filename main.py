# main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

from app.graph.workflow import build_graph

load_dotenv()

app = FastAPI(title="Food Redistribution Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

# Request Schema
class DonationRequest(BaseModel):
    id: str
    source_name: str
    contact_phone: str

    food_type: str
    quantity: int
    is_veg: bool

    prepared_at: str
    expiry_hours: int

    pickup_address: str
    pickup_lat: float
    pickup_lng: float

    special_notes: str

# Routes
@app.get("/")
def home():
    return {"message": "API is running 🚀"}


@app.post("/process-food")
def process_food(request: DonationRequest):
    try:
        result = graph.invoke({
            "donation": request.dict()
        })

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
