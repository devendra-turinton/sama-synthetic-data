import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")





# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "sama_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
REFERENCE_DATA_DIR = os.path.join(DATA_DIR, "reference")

# Scenario configuration
SCENARIOS = [
    {
        "name": "pakistan_infiltration",
        "description": "Pakistani infiltration operation in Kashmir with diversionary ceasefire violations",
        "duration_days": 14,
        "border": "india_pakistan",
        "area": "kashmir_loc",
    },
    {
        "name": "china_infrastructure",
        "description": "Chinese infrastructure development near LAC in Ladakh with military support",
        "duration_days": 14,
        "border": "india_china",
        "area": "ladakh_lac",
    },
    {
        "name": "pakistan_military_buildup",
        "description": "Pakistani military buildup near Punjab border including armor and artillery",
        "duration_days": 10,
        "border": "india_pakistan",
        "area": "punjab_ib",
    },
    {
        "name": "china_patrol_confrontation",
        "description": "Chinese patrol confrontation and face-off in Arunachal Pradesh",
        "duration_days": 7,
        "border": "india_china",
        "area": "arunachal_lac",
    },
    {
        "name": "two_front_pressure",
        "description": "Coordinated pressure along both Pakistan and China borders with simultaneous activities",
        "duration_days": 21,
        "border": "both",
        "area": "multi_sector",
    },
]

# Geographic areas
GEOGRAPHIC_AREAS = {
    "kashmir_loc": {
        "center_lat": 34.0836,
        "center_long": 74.8023,
        "radius_km": 50,
    },
    "punjab_ib": {
        "center_lat": 31.6340,
        "center_long": 74.8723,
        "radius_km": 30,
    },
    "ladakh_lac": {
        "center_lat": 34.2268,
        "center_long": 77.5619,
        "radius_km": 40,
    },
    "arunachal_lac": {
        "center_lat": 27.6891,
        "center_long": 92.2008,
        "radius_km": 35,
    },
    "multi_sector": {
        "sub_areas": ["kashmir_loc", "ladakh_lac"],
    },
}

# Model configuration
MODEL_CONFIG = {
    "model": "claude-3-haiku-20240307",
    "max_tokens": 4000,
    "temperature": 0.2,
}

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)