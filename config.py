import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

# ============================================================================
# PRODUCTION CONFIGURATION
# ============================================================================
PRODUCTION_MODE = True  # Set to True for full 92-day generation

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

# ============================================================================
# KARGIL WAR SCENARIO - COMPLETE 92 DAYS
# ============================================================================
KARGIL_SCENARIO = {
    "name": "kargil_war_1999",
    "description": "Kargil War 1999 - Complete intelligence reconstruction from pre-infiltration through post-war consolidation",
    "start_date": "1999-05-08",  # May 8 - Infiltration begins
    "end_date": "1999-08-07",    # August 7 - Post-war consolidation complete (92 days)
    "border": "india_pakistan",
    "area": "kargil_sector",
    "phases": {
        "infiltration": {
            "start": "1999-05-08",
            "end": "1999-05-20",
            "days": 13,
            "description": "Pakistani infiltration phase - covert movement and position occupation",
            "activity_level": "low_to_medium",
            "key_events": [
                {"date": "1999-05-08", "event": "Initial infiltration begins in multiple sectors"},
                {"date": "1999-05-10", "event": "Tiger Hill area occupied"},
                {"date": "1999-05-15", "event": "Tololing complex infiltrated"},
                {"date": "1999-05-18", "event": "Heavy weapons positioning"}
            ]
        },
        "discovery": {
            "start": "1999-05-21",
            "end": "1999-05-31",
            "days": 11,
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
            "days": 50,
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
            "days": 6,
            "description": "Final operations and Pakistani withdrawal",
            "activity_level": "medium",
            "key_events": [
                {"date": "1999-07-21", "event": "Pakistani forces begin withdrawal"},
                {"date": "1999-07-26", "event": "Victory declared - Operation Vijay concludes"}
            ]
        },
        "post_war": {
            "start": "1999-07-27",
            "end": "1999-08-07",
            "days": 12,
            "description": "Post-war consolidation and position strengthening",
            "activity_level": "low",
            "key_events": [
                {"date": "1999-07-27", "event": "Defensive position consolidation"},
                {"date": "1999-07-30", "event": "Area sanitization operations"},
                {"date": "1999-08-05", "event": "Final position fortification"}
            ]
        }
    }
}

# Geographic areas - Kargil sector
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
            "point_4700": {"lat": 34.5321, "long": 76.1445, "height": 4700},
            "batalik": {"lat": 34.7867, "long": 76.4321, "height": 4200},
            "drass": {"lat": 34.4230, "long": 75.7500, "height": 3350},
            "mushkoh_valley": {"lat": 34.5890, "long": 76.0890, "height": 4100},
            "kaksar": {"lat": 34.6123, "long": 76.2234, "height": 4400}
        }
    }
}

# Formation Code Mapping - Indian Army Units
FORMATION_MAPPING = {
    # ELINT Units
    "NC14087001": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "8 Mountain Division",
        "bde_name": "70 Infantry Brigade",
        "unit_name": "Electronic Warfare Unit 112",
        "level": "Brigade"
    },
    "NC14087901": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "8 Mountain Division",
        "bde_name": "79 Mountain Brigade",
        "unit_name": "SIGINT Company 14 Corps",
        "level": "Brigade"
    },
    "NC14035601": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "3 Infantry Division",
        "bde_name": "56 Mountain Brigade",
        "unit_name": "Electronic Intelligence Detachment",
        "level": "Brigade"
    },
    # IMINT Units
    "NC14085601": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "8 Mountain Division",
        "bde_name": "56 Mountain Brigade",
        "unit_name": "Imagery Analysis Cell 06",
        "level": "Division"
    },
    "NC14036801": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "3 Infantry Division",
        "bde_name": "68 Mountain Brigade",
        "unit_name": "Imagery Analysis Cell 03",
        "level": "Division"
    },
    # TACINT Units
    "NC14087002": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "8 Mountain Division",
        "bde_name": "70 Infantry Brigade",
        "unit_name": "BSF Observation Post Delta-7",
        "level": "Battalion"
    },
    "NC14087902": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "8 Mountain Division",
        "bde_name": "79 Mountain Brigade",
        "unit_name": "BSF Observation Post Alpha-3",
        "level": "Battalion"
    },
    "NC14080201": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "8 Mountain Division",
        "bde_name": "102 Infantry Brigade",
        "unit_name": "BSF Battalion 125",
        "level": "Battalion"
    },
    "NC14036802": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "3 Infantry Division",
        "bde_name": "68 Mountain Brigade",
        "unit_name": "18 Grenadiers Forward Post",
        "level": "Battalion"
    },
    "NC14035602": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "3 Infantry Division",
        "bde_name": "56 Mountain Brigade",
        "unit_name": "BSF Observation Post Charlie-9",
        "level": "Battalion"
    },
    "NC15281801": {
        "cmd_name": "Northern Command",
        "corps_name": "XV Corps",
        "div_name": "28 Infantry Division",
        "bde_name": "18 Grenadiers Brigade",
        "unit_name": "Forward Observation Team Bravo",
        "level": "Battalion"
    },
    # FUSION Unit
    "NC14080000": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "8 Mountain Division",
        "bde_name": "Division HQ",
        "unit_name": "Intelligence Fusion Cell - 8 Mtn Div",
        "level": "Division"
    },
    # SITREP Units
    "NC14087000": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "8 Mountain Division",
        "bde_name": "70 Infantry Brigade",
        "unit_name": "70 Infantry Brigade Headquarters",
        "level": "Brigade"
    },
    "NC14087900": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "8 Mountain Division",
        "bde_name": "79 Mountain Brigade",
        "unit_name": "79 Mountain Brigade Headquarters",
        "level": "Brigade"
    },
    "NC14035600": {
        "cmd_name": "Northern Command",
        "corps_name": "XIV Corps",
        "div_name": "3 Infantry Division",
        "bde_name": "56 Mountain Brigade",
        "unit_name": "56 Mountain Brigade Headquarters",
        "level": "Brigade"
    }
}

# Unit rotation by source type
OBSERVING_UNITS = {
    "ELINT": ["NC14087001", "NC14087901", "NC14035601"],
    "IMINT": ["NC14085601", "NC14036801"],
    "TACINT": ["NC14087002", "NC14087902", "NC14080201", "NC14036802", "NC14035602", "NC15281801"],
    "FUSION": ["NC14080000"],
    "SITREP": ["NC14087000", "NC14087900", "NC14035600"]
}

# Model configuration
MODEL_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 16384,
    "temperature": 0.1,
}

# Time slots for 6 observations per day
DAILY_TIME_SLOTS = [
    "00:00",  # Night operations
    "04:00",  # Pre-dawn
    "08:00",  # Morning
    "12:00",  # Midday
    "16:00",  # Afternoon
    "20:00"   # Evening
]

# Pakistani military equipment database
PAKISTANI_EQUIPMENT = {
    "armor": ["Al-Khalid MBT", "T-59 Tank", "T-69 Tank", "M113 APC", "Talha APC"],
    "artillery": ["130mm M-46 Gun", "122mm D-30 Howitzer", "155mm M-114 Howitzer", "107mm Rocket Launcher"],
    "aircraft": ["F-16 Fighting Falcon", "Mirage III", "Mirage V", "A-5 Fantan"],
    "communications": ["TRC-20H Tactical Radio", "HF Command Net", "VHF Tactical Net"],
    "radar": ["AN/TPS-43 Surveillance Radar", "Crotale Fire Control Radar", "Type 305 Radar"]
}

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)