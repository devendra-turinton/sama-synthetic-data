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

# Kargil War Historical Timeline
KARGIL_SCENARIO = {
    "name": "kargil_war_1999",
    "description": "Kargil War 1999 - Complete intelligence reconstruction from pre-infiltration through post-war consolidation",
    "start_date": "1999-05-01",  # 20 days before discovery
    "discovery_date": "1999-05-21",  # When infiltration was discovered
    "operation_vijay_start": "1999-05-26",
    "end_date": "1999-07-26",  # Victory Day
    "post_war_end": "1999-07-31",  # 5 days post-war
    "border": "india_pakistan",
    "area": "kargil_sector",
    "phases": {
        "pre_infiltration": {
            "start": "1999-05-01",
            "end": "1999-05-20",
            "description": "Pakistani infiltration phase - covert movement of troops and equipment",
            "activity_level": "low_to_medium",
            "key_events": [
                {"date": "1999-05-03", "event": "Initial infiltration begins in Batalik sector"},
                {"date": "1999-05-08", "event": "Pakistani forces occupy Tiger Hill"},
                {"date": "1999-05-10", "event": "Point 5140 infiltrated"},
                {"date": "1999-05-15", "event": "Tololing complex occupied"},
                {"date": "1999-05-18", "event": "Heavy weapons positioning begins"}
            ]
        },
        "discovery": {
            "start": "1999-05-21",
            "end": "1999-05-31",
            "description": "Discovery and initial response phase",
            "activity_level": "medium_to_high",
            "key_events": [
                {"date": "1999-05-21", "event": "Indian patrol discovers Pakistani positions"},
                {"date": "1999-05-26", "event": "Operation Vijay officially launched"},
                {"date": "1999-05-28", "event": "First artillery strikes"},
                {"date": "1999-05-30", "event": "Air strikes commence"}
            ]
        },
        "major_operations": {
            "start": "1999-06-01",
            "end": "1999-07-20",
            "description": "Main battle phase with intensive combat operations",
            "activity_level": "very_high",
            "key_events": [
                {"date": "1999-06-13", "event": "Battle for Tololing begins"},
                {"date": "1999-06-20", "event": "Tololing recaptured"},
                {"date": "1999-06-29", "event": "Point 5140 assault"},
                {"date": "1999-07-04", "event": "Tiger Hill recaptured"},
                {"date": "1999-07-08", "event": "Point 4875 recaptured"},
                {"date": "1999-07-14", "event": "Battle for Batalik sector"}
            ]
        },
        "conclusion": {
            "start": "1999-07-21",
            "end": "1999-07-26",
            "description": "Final operations and Pakistani withdrawal",
            "activity_level": "medium",
            "key_events": [
                {"date": "1999-07-21", "event": "Pakistani forces begin withdrawal"},
                {"date": "1999-07-26", "event": "Victory declared - Operation Vijay concludes"}
            ]
        },
        "post_war": {
            "start": "1999-07-27",
            "end": "1999-07-31",
            "description": "Post-war consolidation and position strengthening",
            "activity_level": "low",
            "key_events": [
                {"date": "1999-07-27", "event": "Defensive position consolidation"},
                {"date": "1999-07-29", "event": "Area sanitization operations"}
            ]
        }
    }
}

# Geographic areas - Kargil sector specific locations
GEOGRAPHIC_AREAS = {
    "kargil_sector": {
        "center_lat": 34.5535,
        "center_long": 76.1315,
        "radius_km": 30,
        "key_positions": {
            "tiger_hill": {"lat": 34.5123, "long": 76.1234, "height": 5062},
            "tololing": {"lat": 34.5445, "long": 76.1156, "height": 4590},
            "point_5140": {"lat": 34.5234, "long": 76.1523, "height": 5140},
            "point_4875": {"lat": 34.5678, "long": 76.1012, "height": 4875},
            "batalik": {"lat": 34.7867, "long": 76.4321, "height": 4200},
            "drass": {"lat": 34.4230, "long": 75.7500, "height": 3350}
        }
    }
}

# Indian Army Formation Structure for Northern Command (Kargil War)
INDIAN_FORMATIONS = {
    "commands": {
        "NC": {
            "name": "Northern Command",
            "code": "NC",
            "corps": {
                "14": {
                    "name": "XIV Corps",
                    "code": "14",
                    "divisions": {
                        "08": {
                            "name": "8 Mountain Division",
                            "code": "08",
                            "brigades": {
                                "70": {"name": "70 Infantry Brigade", "code": "70"},
                                "79": {"name": "79 Mountain Brigade", "code": "79"},
                                "102": {"name": "102 Infantry Brigade", "code": "02"}
                            }
                        },
                        "03": {
                            "name": "3 Infantry Division",
                            "code": "03",
                            "brigades": {
                                "56": {"name": "56 Mountain Brigade", "code": "56"},
                                "68": {"name": "68 Mountain Brigade", "code": "68"},
                                "121": {"name": "121 Infantry Brigade", "code": "21"}
                            }
                        }
                    }
                },
                "15": {
                    "name": "XV Corps",
                    "code": "15",
                    "divisions": {
                        "28": {
                            "name": "28 Infantry Division",
                            "code": "28",
                            "brigades": {
                                "192": {"name": "192 Mountain Brigade", "code": "92"},
                                "18": {"name": "18 Grenadiers Brigade", "code": "18"}
                            }
                        }
                    }
                }
            }
        }
    },
    "bsf_units": [
        "BSF Observation Post Delta-7",
        "BSF Observation Post Alpha-3",
        "BSF Observation Post Charlie-9",
        "BSF Battalion 125",
        "BSF Battalion 136"
    ],
    "intelligence_units": [
        "Electronic Warfare Unit 112",
        "Imagery Analysis Cell 06",
        "Intelligence Fusion Cell",
        "SIGINT Company 14 Corps"
    ]
}

# Model configuration - using Claude Sonnet for better quality
MODEL_CONFIG = {
    "model": "claude-sonnet-4-20250514",  # Upgraded from Haiku for quality
    "max_tokens": 8000,  # Increased for detailed descriptions
    "temperature": 0.3,  # Slightly higher for varied realistic descriptions
}

# Time slots for 6 observations per day (every 4 hours)
DAILY_TIME_SLOTS = [
    "00:00",  # Night operations
    "04:00",  # Pre-dawn
    "08:00",  # Morning
    "12:00",  # Midday
    "16:00",  # Afternoon
    "20:00"   # Evening
]

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
