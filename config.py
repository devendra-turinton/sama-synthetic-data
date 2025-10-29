import os
import random
from datetime import datetime, timedelta
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
# EXPANDED GEOGRAPHIC AREAS - 100+ LOCATIONS
# ============================================================================
GEOGRAPHIC_AREAS_ENHANCED = {
    "tololing_complex": {
        "main_peak": {
            "name": "Tololing Top",
            "lat": 34.5445, 
            "long": 76.1156, 
            "height": 4590,
            "tactical_significance": "Dominates Drass-Kargil road, critical observation position"
        },
        "sub_locations": {
            "tololing_summit": {
                "name": "Tololing Summit",
                "lat": 34.5447, "long": 76.1158, "height": 4590,
                "features": ["Rocky summit", "360-degree observation", "Prepared defensive positions"]
            },
            "tololing_nala": {
                "name": "Tololing Nala",
                "lat": 34.5440, "long": 76.1150, "height": 4450,
                "features": ["Valley approach", "Dead ground from summit", "Natural assembly area"]
            },
            "three_pimples": {
                "name": "Three Pimples Complex",
                "lat": 34.5450, "long": 76.1160, "height": 4520,
                "features": ["Three distinct peaks", "Mutual support positions", "Interlocking fields of fire"]
            },
            "hump_complex": {
                "name": "The Hump",
                "lat": 34.5455, "long": 76.1165, "height": 4480,
                "features": ["Prominent ridgeline", "Observation post site", "Secondary defensive position"]
            },
            "western_spur": {
                "name": "Tololing Western Spur",
                "lat": 34.5438, "long": 76.1145, "height": 4400,
                "features": ["Approach route", "Covered approach", "Flank protection"]
            },
            "eastern_approach": {
                "name": "Tololing Eastern Approach",
                "lat": 34.5452, "long": 76.1170, "height": 4420,
                "features": ["Alternative assault route", "Steep gradient", "Limited cover"]
            },
            "assembly_area_alpha": {
                "name": "Assembly Area Alpha (Tololing)",
                "lat": 34.5435, "long": 76.1140, "height": 4300,
                "features": ["Troop concentration area", "Defilade position", "Protected from observation"]
            },
            "tololing_base": {
                "name": "Tololing Base Camp",
                "lat": 34.5430, "long": 76.1135, "height": 4250,
                "features": ["Logistics node", "Medical facility", "Communications center"]
            }
        }
    },
    
    "tiger_hill_complex": {
        "main_peak": {
            "name": "Tiger Hill",
            "lat": 34.5123, "long": 76.1234, "height": 5062,
            "tactical_significance": "Highest peak in sector, dominates entire Drass valley"
        },
        "sub_locations": {
            "tiger_hill_summit": {
                "name": "Tiger Hill Summit",
                "lat": 34.5125, "long": 76.1236, "height": 5062,
                "features": ["Highest point", "360-degree observation", "Fortified bunkers"]
            },
            "india_saddle": {
                "name": "India Saddle",
                "lat": 34.5120, "long": 76.1230, "height": 4950,
                "features": ["Key terrain feature", "Assault corridor", "Protected from direct fire"]
            },
            "pimple_1": {
                "name": "Tiger Hill Pimple 1",
                "lat": 34.5128, "long": 76.1240, "height": 5020,
                "features": ["Supporting position", "Interlocking fire position", "Observation post"]
            },
            "pimple_2": {
                "name": "Tiger Hill Pimple 2",
                "lat": 34.5130, "long": 76.1245, "height": 5015,
                "features": ["Flanking position", "Fire support base", "Secondary objective"]
            },
            "western_ridge": {
                "name": "Tiger Hill Western Ridge",
                "lat": 34.5118, "long": 76.1225, "height": 4900,
                "features": ["Primary approach route", "Covered movement", "Dead ground sections"]
            },
            "approach_route_alpha": {
                "name": "Tiger Hill Approach Alpha",
                "lat": 34.5115, "long": 76.1220, "height": 4800,
                "features": ["Main assault route", "Steep terrain", "Night approach corridor"]
            },
            "approach_route_bravo": {
                "name": "Tiger Hill Approach Bravo",
                "lat": 34.5110, "long": 76.1215, "height": 4750,
                "features": ["Alternative route", "Less exposed", "Longer distance"]
            },
            "tiger_hill_base": {
                "name": "Tiger Hill Base Area",
                "lat": 34.5105, "long": 76.1210, "height": 4700,
                "features": ["Logistics base", "Artillery positions", "Command post location"]
            }
        }
    },
    
    "point_5140_complex": {
        "main_peak": {
            "name": "Point 5140",
            "lat": 34.5234, "long": 76.1523, "height": 5140,
            "tactical_significance": "Critical discovery point, gateway position"
        },
        "sub_locations": {
            "point_5140_summit": {
                "name": "Point 5140 Summit",
                "lat": 34.5236, "long": 76.1525, "height": 5140,
                "features": ["Peak position", "Observation tower site", "Defensive works"]
            },
            "point_5140_west": {
                "name": "Point 5140 West Face",
                "lat": 34.5232, "long": 76.1518, "height": 5080,
                "features": ["Steep western slope", "Limited access", "Difficult assault route"]
            },
            "point_5140_saddle": {
                "name": "Point 5140 Saddle",
                "lat": 34.5230, "long": 76.1520, "height": 5050,
                "features": ["Connecting terrain", "Movement corridor", "Vulnerable point"]
            },
            "point_5140_north_ridge": {
                "name": "Point 5140 North Ridge",
                "lat": 34.5240, "long": 76.1528, "height": 5100,
                "features": ["Dominating ridge", "Fire position", "Observation line"]
            },
            "point_5140_approach": {
                "name": "Point 5140 Approach Corridor",
                "lat": 34.5228, "long": 76.1515, "height": 5000,
                "features": ["Main approach", "Assembly area", "Staging position"]
            }
        }
    },
    
    "point_5353_complex": {
        "main_peak": {
            "name": "Point 5353",
            "lat": 34.5678, "long": 76.1012, "height": 5353,
            "tactical_significance": "Highest in region, strategic observation"
        },
        "sub_locations": {
            "point_5353_top": {
                "name": "Point 5353 Summit",
                "lat": 34.5680, "long": 76.1014, "height": 5353,
                "features": ["Highest elevation", "Long range observation", "Weather station site"]
            },
            "point_5353_approaches": {
                "name": "Point 5353 Access Routes",
                "lat": 34.5675, "long": 76.1008, "height": 5280,
                "features": ["Multiple approach routes", "Technical climbing", "Supply difficulties"]
            },
            "point_5353_base": {
                "name": "Point 5353 Base Camp",
                "lat": 34.5670, "long": 76.1005, "height": 5200,
                "features": ["Staging area", "Equipment storage", "Personnel rest area"]
            }
        }
    },
    
    "point_4875_complex": {
        "main_peak": {
            "name": "Point 4875",
            "lat": 34.5321, "long": 76.1445, "height": 4875,
            "tactical_significance": "Controls valley approaches"
        },
        "sub_locations": {
            "point_4875_summit": {
                "name": "Point 4875 Top",
                "lat": 34.5323, "long": 76.1447, "height": 4875,
                "features": ["Peak position", "Fire support location", "Observation post"]
            },
            "point_4875_approaches": {
                "name": "Point 4875 Routes",
                "lat": 34.5318, "long": 76.1440, "height": 4800,
                "features": ["Approach corridors", "Assault positions", "Covered routes"]
            },
            "point_4875_east_ridge": {
                "name": "Point 4875 Eastern Ridge",
                "lat": 34.5325, "long": 76.1450, "height": 4850,
                "features": ["Flanking position", "Support by fire", "Alternative objective"]
            }
        }
    },
    
    "batalik_sector": {
        "main_area": {
            "name": "Batalik Sector",
            "lat": 34.7867, "long": 76.4321, "height": 4200,
            "tactical_significance": "Eastern front operations"
        },
        "sub_locations": {
            "batalik_town": {
                "name": "Batalik Town",
                "lat": 34.7870, "long": 76.4325, "height": 4180,
                "features": ["Urban area", "Logistics hub", "Civilian presence"]
            },
            "jubar_ridge": {
                "name": "Jubar Ridge",
                "lat": 34.7865, "long": 76.4315, "height": 4250,
                "features": ["Dominating terrain", "Defensive positions", "Observation line"]
            },
            "khalubar": {
                "name": "Khalubar Complex",
                "lat": 34.7880, "long": 76.4340, "height": 4300,
                "features": ["Peak complex", "Multiple positions", "Interlocking defenses"]
            },
            "batalik_nala": {
                "name": "Batalik Nala",
                "lat": 34.7860, "long": 76.4310, "height": 4150,
                "features": ["Valley floor", "Movement corridor", "Supply route"]
            },
            "batalik_heights": {
                "name": "Batalik Surrounding Heights",
                "lat": 34.7875, "long": 76.4330, "height": 4280,
                "features": ["Multiple peaks", "Commanding positions", "Mutual support"]
            }
        }
    },
    
    "drass_sector": {
        "main_area": {
            "name": "Drass Sector",
            "lat": 34.4230, "long": 75.7500, "height": 3350,
            "tactical_significance": "Second coldest inhabited place, key logistics route"
        },
        "sub_locations": {
            "drass_town": {
                "name": "Drass Town",
                "lat": 34.4232, "long": 75.7502, "height": 3350,
                "features": ["Town center", "Medical facilities", "Supply depot"]
            },
            "drass_valley": {
                "name": "Drass Valley Floor",
                "lat": 34.4220, "long": 75.7490, "height": 3300,
                "features": ["Open valley", "Agricultural area", "Movement corridor"]
            },
            "nh_1d_sector": {
                "name": "NH 1D Drass Stretch",
                "lat": 34.4240, "long": 75.7520, "height": 3380,
                "features": ["Main highway", "Critical supply line", "Target for interdiction"]
            },
            "drass_war_memorial": {
                "name": "Drass War Memorial Area",
                "lat": 34.4235, "long": 75.7505, "height": 3360,
                "features": ["Memorial site", "Historical significance", "Open terrain"]
            },
            "drass_heights": {
                "name": "Drass Surrounding Heights",
                "lat": 34.4250, "long": 75.7530, "height": 3500,
                "features": ["Dominating peaks", "Observation positions", "Fire support bases"]
            }
        }
    },
    
    "mushkoh_valley": {
        "main_area": {
            "name": "Mushkoh Valley",
            "lat": 34.5890, "long": 76.0890, "height": 4100,
            "tactical_significance": "Primary infiltration corridor"
        },
        "sub_locations": {
            "mushkoh_valley_floor": {
                "name": "Mushkoh Valley Floor",
                "lat": 34.5885, "long": 76.0885, "height": 4050,
                "features": ["Valley bottom", "River bed", "Concealed movement"]
            },
            "mushkoh_ridgeline": {
                "name": "Mushkoh Ridge",
                "lat": 34.5895, "long": 76.0900, "height": 4200,
                "features": ["Dominating ridge", "Observation line", "Defensive positions"]
            },
            "mushkoh_approach": {
                "name": "Mushkoh Infiltration Route",
                "lat": 34.5880, "long": 76.0870, "height": 4000,
                "features": ["Covert approach", "Limited visibility", "Natural cover"]
            },
            "mushkoh_pass": {
                "name": "Mushkoh Pass",
                "lat": 34.5900, "long": 76.0910, "height": 4250,
                "features": ["Mountain pass", "Choke point", "Weather affected"]
            }
        }
    },
    
    "kaksar_area": {
        "main_area": {
            "name": "Kaksar",
            "lat": 34.6123, "long": 76.2234, "height": 4400,
            "tactical_significance": "Central sector position"
        },
        "sub_locations": {
            "kaksar_village": {
                "name": "Kaksar Village",
                "lat": 34.6125, "long": 76.2236, "height": 4380,
                "features": ["Small settlement", "Local intelligence source", "Supply point"]
            },
            "kaksar_heights": {
                "name": "Kaksar Heights",
                "lat": 34.6130, "long": 76.2245, "height": 4500,
                "features": ["Elevated positions", "Observation posts", "Defensive works"]
            },
            "kaksar_ridge": {
                "name": "Kaksar Ridge Complex",
                "lat": 34.6135, "long": 76.2250, "height": 4550,
                "features": ["Extended ridgeline", "Multiple positions", "Commanding views"]
            }
        }
    },
    
    "marpo_la": {
        "main_area": {
            "name": "Marpo La Ridge",
            "lat": 34.5556, "long": 76.1667, "height": 4700,
            "tactical_significance": "Connecting terrain between sectors"
        },
        "sub_locations": {
            "marpo_la_ridge": {
                "name": "Marpo La Ridgeline",
                "lat": 34.5558, "long": 76.1669, "height": 4700,
                "features": ["Long ridge", "Movement corridor", "Observation line"]
            },
            "marpo_la_pass": {
                "name": "Marpo La Pass",
                "lat": 34.5552, "long": 76.1662, "height": 4650,
                "features": ["Mountain pass", "Movement route", "Supply corridor"]
            },
            "marpo_la_heights": {
                "name": "Marpo La Heights",
                "lat": 34.5560, "long": 76.1672, "height": 4750,
                "features": ["High ground", "Observation posts", "Fire positions"]
            }
        }
    },
    
    "line_of_control": {
        "main_area": {
            "name": "Line of Control (LoC) Sector",
            "lat": 34.5500, "long": 76.1500, "height": 4500,
            "tactical_significance": "International boundary, patrol line"
        },
        "sub_locations": {
            "loc_checkpoint_alpha": {
                "name": "LoC Checkpoint Alpha",
                "lat": 34.5505, "long": 76.1505, "height": 4520,
                "features": ["Border post", "Observation tower", "Communication relay"]
            },
            "loc_patrol_route_1": {
                "name": "LoC Patrol Route 1",
                "lat": 34.5510, "long": 76.1510, "height": 4540,
                "features": ["Patrol path", "Regular patrols", "Border monitoring"]
            },
            "loc_forward_post": {
                "name": "LoC Forward Observation Post",
                "lat": 34.5515, "long": 76.1515, "height": 4560,
                "features": ["Forward position", "Early warning", "Visual observation"]
            }
        }
    },
    
    "supply_routes": {
        "main_area": {
            "name": "Main Supply Routes",
            "lat": 34.5000, "long": 76.1000, "height": 3800,
            "tactical_significance": "Logistics arteries, critical for operations"
        },
        "sub_locations": {
            "msr_alpha": {
                "name": "Main Supply Route Alpha",
                "lat": 34.5010, "long": 76.1010, "height": 3820,
                "features": ["Primary route", "All-weather road", "Heavy traffic"]
            },
            "msr_bravo": {
                "name": "Main Supply Route Bravo",
                "lat": 34.5020, "long": 76.1020, "height": 3840,
                "features": ["Alternate route", "Mountain road", "Weather dependent"]
            },
            "logistics_node_1": {
                "name": "Forward Logistics Node 1",
                "lat": 34.5030, "long": 76.1030, "height": 3860,
                "features": ["Supply depot", "Fuel storage", "Ammunition dump"]
            }
        }
    }
}

# Keep old GEOGRAPHIC_AREAS for backward compatibility
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

# ============================================================================
# MILITARY INTELLIGENCE LANGUAGE LIBRARY
# ============================================================================
MILITARY_INTELLIGENCE_LANGUAGE = {
    "movement_descriptions": [
        "conducting tactical displacement via covered route",
        "executing deliberate approach march in column formation",
        "performing infiltration movement utilizing dead ground",
        "initiating flanking maneuver along ridgeline axis",
        "conducting withdrawal under contact to alternate positions",
        "executing relief in place with follow-on battalion elements",
        "performing tactical assembly in defilade position",
        "conducting bound-and-overwatch advance toward objective",
        "executing night movement with strict noise discipline maintained",
        "performing tactical road march with convoy security elements",
        "conducting administrative movement to staging area",
        "executing hasty displacement from exposed position",
        "performing deliberate withdrawal to prepared defenses",
        "conducting infiltration using multiple covered approaches",
        "executing relief in contact with covering force",
        "performing tactical repositioning to dominating terrain",
        "conducting movement to contact with reconnaissance forward",
        "executing approach march with advance guard deployed",
        "performing tactical displacement under indirect fire",
        "conducting retrograde operation to phase line"
    ],
    
    "unit_compositions": [
        "reinforced rifle company (est. 120-140 personnel, 3 platoons plus attachments)",
        "platoon-sized element with integral support (35-40 combatants, 3 sections)",
        "company-strength formation with attached weapons platoon (150 personnel, 4 platoons)",
        "battalion-minus configuration (estimated 400-450 troops, 3 rifle companies)",
        "composite force: 2 rifle platoons, 1 mortar section, 1 MG detachment (80-90 personnel)",
        "squadron-sized armored element (12-14 MBTs, support vehicles)",
        "reinforced infantry section (12-14 soldiers, 2 LMG teams)",
        "company team with artillery liaison (140 personnel, organic fire support)",
        "battalion task force with engineer detachment (500+ personnel, multi-role capability)",
        "reinforced platoon with anti-tank section (50 personnel, 4 AT weapons)",
        "company(-) with reduced strength (90-100 personnel, 2 platoons operational)",
        "battalion(+) reinforced with artillery battery (650 personnel, enhanced fires)",
        "rifle section with attached specialist (10 personnel, sniper/signaler integrated)",
        "platoon combat patrol (25-30 personnel, reconnaissance configured)",
        "company assault element (100 personnel, 2 assault platoons, 1 support platoon)"
    ],
    
    "pakistani_units": [
        "12th Northern Light Infantry - Alpha Company",
        "12th Northern Light Infantry - Bravo Company",
        "12th Northern Light Infantry - Charlie Company",
        "12th Northern Light Infantry - Delta Company",
        "5th Northern Light Infantry Battalion",
        "6th Northern Light Infantry Battalion",
        "3rd Battalion Special Services Group (SSG)",
        "Gilgit Scouts reconnaissance element",
        "31st Azad Kashmir Regiment",
        "24th Azad Kashmir Regiment",
        "Artillery support from 80 Field Regiment",
        "22 Punjab Regiment detachment",
        "Frontier Force Regiment elements",
        "Chitral Scouts patrol units",
        "12th NLI - Mortar Platoon",
        "Northern Light Infantry - Machine Gun Section",
        "SSG (N) naval special operations team",
        "Pakistan Army Engineers - 12th NLI attached",
        "Artillery Forward Observer Team - 12th NLI",
        "12th NLI Battalion Headquarters element"
    ],
    
    "indian_units": [
        "2 Rajputana Rifles",
        "18 Grenadiers",
        "8 Sikh Light Infantry",
        "13 JAK Rifles",
        "1/11 Gorkha Rifles",
        "2 Naga Regiment",
        "3 Punjab Regiment",
        "17 Jat Regiment",
        "BSF Battalion 125",
        "BSF Battalion 136",
        "2 Rajputana Rifles - Delta Company",
        "18 Grenadiers - Charlie Company",
        "192 Mountain Regiment (Artillery)",
        "197 Field Regiment",
        "8 Sikh LI - Bravo Company",
        "13 JAK Rifles - reconnaissance platoon",
        "1/11 Gorkha Rifles - assault company",
        "Engineer Task Force - 70 Engineer Regiment",
        "Medical Evacuation Team - 92 Field Hospital",
        "Forward Air Control Team - Indian Air Force"
    ],
    
    "equipment_specifics_pakistan": [
        "3x Al-Khalid MBT, 2x M113 APC, 4x Toyota Hilux technical vehicles",
        "Rifle platoon: 3x sections with G3A3 rifles, 2x RPG-7 teams, 2x PKM GPMG",
        "Artillery support: 2x 130mm M-46 field guns, 3x 122mm D-30 howitzers",
        "Air defense: 2x Anza Mk-II MANPADS teams, 1x 14.5mm ZPU-2 AAA",
        "Mortar section: 2x 60mm commando mortars, 1x 81mm medium mortar",
        "Communications: TRC-20H tactical radio sets, HF command net capability",
        "Infantry weapons: G3A3 7.62mm rifles, Type 56 assault rifles, RPG-7V launchers",
        "Machine gun section: 2x 12.7mm DShK heavy machine guns, 4x PKM 7.62mm GPMG",
        "Anti-tank capability: 2x 106mm M40 recoilless rifles, multiple RPG-7 teams",
        "Indirect fire: 82mm M-43 mortars, 120mm M-43 heavy mortars",
        "Personal equipment: body armor, load-bearing equipment, night vision devices (limited)",
        "Artillery ammunition: HE, illumination, smoke rounds for 130mm and 122mm",
        "Engineer equipment: bangalore torpedoes, mine detectors, demolition charges",
        "Logistics: fuel trucks, ammunition carriers, medical evacuation vehicles"
    ],
    
    "equipment_specifics_india": [
        "Bofors 155mm FH-77B howitzers providing fire support (6-8 guns per battery)",
        "120mm mortar batteries in general support role",
        "Heavy machine guns: 12.7mm M2 Browning, 7.62mm MMG sections",
        "Infantry weapons: INSAS 5.56mm rifles, AK-47/56 rifles, 5.56mm LMG sections",
        "Anti-armor: 84mm Carl Gustav RCL, Milan ATGM systems, RPG-7 launchers",
        "Artillery: 105mm Indian Field Gun, 130mm M-46 counter-battery fire",
        "Mortars: 81mm medium mortars, 120mm heavy mortars with HE and illumination rounds",
        "Air support: Mirage 2000H conducting precision strikes with laser-guided bombs",
        "Close air support: MiG-21, MiG-23, MiG-27 fighter-bombers",
        "Observation equipment: thermal imagers, night vision devices, laser rangefinders",
        "Communications: Motorola tactical radios, secure voice systems, satellite phones",
        "Engineer equipment: mine detectors, demolition charges, obstacle breaching tools",
        "Medical: casualty evacuation helicopters, forward surgical teams, field hospitals",
        "Artillery munitions: HE, DPICM, smoke, illumination rounds"
    ],
    
    "tactical_activities": [
        "establishing blocking position to interdict enemy movement",
        "conducting reconnaissance in force to determine enemy strength",
        "executing deliberate assault with supporting fires",
        "performing feint operation to fix enemy forces",
        "conducting cordon and search of suspected positions",
        "executing raid on enemy logistics node",
        "performing hasty defense establishment with interlocking fires",
        "conducting probing attack to identify weak points",
        "executing infiltration to seize key terrain",
        "performing relief in place with minimal exposure",
        "conducting ambush operations along approach routes",
        "executing break contact drill under fire",
        "performing fire and maneuver to assault objective",
        "conducting retrograde operation with rearguard action",
        "executing breaching operation through obstacle belt",
        "performing consolidation and reorganization after assault",
        "conducting counter-reconnaissance to screen main body",
        "executing demonstration to deceive enemy",
        "performing passage of lines through friendly forces",
        "conducting area reconnaissance with multiple patrols"
    ],
    
    "intelligence_assessments": [
        "Assessed intent: deny Indian control of dominating terrain",
        "Probable mission: interdict NH 1D supply route and isolate forward positions",
        "Estimated objective: establish forward operating base for sustained operations",
        "Inferred purpose: fix Indian forces to enable operations elsewhere in sector",
        "Tactical assessment: preparing defensive positions for prolonged occupation",
        "Strategic evaluation: attempting to cut Ladakh logistics link and threaten LoC",
        "Operational assessment: stage one of multi-phase operation to alter ground situation",
        "Intelligence judgment: unit demonstrates professional military training and doctrine",
        "Capability assessment: equipped for extended mountain warfare operations",
        "Threat analysis: poses significant risk to supply lines and forward deployments",
        "Doctrinal analysis: employing standard infantry defensive tactics with modifications for terrain",
        "Force ratio assessment: enemy holds tactical advantage due to prepared positions",
        "Logistics evaluation: evidence of pre-positioned supplies indicates planning",
        "Morale assessment: defensive discipline suggests motivated and well-led force",
        "Tactical significance: position enables observation and interdiction of key routes"
    ],
    
    "observation_methods": [
        "Visual confirmation at 2.3km range via Simrad LP7 thermal imager",
        "Electronic signature analysis indicates TRC-20H tactical radio net active on VHF frequencies",
        "Overhead imagery from CARTOSAT-3 satellite reveals prepared defensive positions with overhead cover",
        "HUMINT reporting from local sources indicates recent logistics resupply activity in sector",
        "Ground observation post utilizing Carl Zeiss 20-60x spotting scope with reticle ranging",
        "Intercepted communications on Pakistani military frequencies suggest battalion-level coordination",
        "Satellite imagery shows vehicle tracks and defensive works construction in progress",
        "Forward observer reports utilizing laser rangefinder confirmed distance 3.8km to target",
        "Thermal imaging devices detected heat signatures consistent with personnel and vehicles",
        "Direction finding equipment triangulated radio emissions to grid location",
        "Night vision observation confirmed movement at 0230 hours local time",
        "Artillery forward observer adjusted fires based on observed fall of shot",
        "Unmanned aerial reconnaissance provided real-time video feed of enemy positions",
        "Ground surveillance radar detected movement across observation area",
        "Acoustic sensors registered heavy vehicle movement and preparation sounds"
    ],
    
    "tactical_terms": [
        "fire support coordination line (FSCL)",
        "assault position",
        "phase line",
        "objective rally point (ORP)",
        "support by fire position (SBF)",
        "breach point",
        "consolidation area",
        "assembly area (AA)",
        "attack position",
        "forward line of own troops (FLOT)",
        "line of departure (LD)",
        "limit of advance (LOA)",
        "coordinated fire line (CFL)",
        "engagement area (EA)",
        "target reference point (TRP)",
        "battle position (BP)",
        "strongpoint",
        "defended locality",
        "tactical assembly area (TAA)",
        "release point (RP)"
    ],
    
    "weather_tactical_impact": [
        "Clear visibility enabling long-range observation and precision fire support",
        "Low cloud ceiling restricting close air support and helicopter operations",
        "Snowfall reducing visibility to 500 meters and decreasing movement rates significantly",
        "High winds (40+ knots) affecting artillery accuracy and helicopter flight operations",
        "Temperature extremes (-15°C) impacting personnel endurance and equipment reliability",
        "Morning fog providing concealment for tactical movement until 0900 hours local",
        "Bright moonlight (85% illumination) enabling night operations but reducing concealment",
        "Rain and sleet creating slippery conditions on steep approaches to objectives",
        "Afternoon thunderstorms expected to ground aviation assets for 3-4 hours",
        "Dust conditions reducing visibility and affecting optical targeting systems",
        "Snow cover providing natural camouflage for defensive positions",
        "Freezing temperatures causing weapon malfunction risks and cold weather injuries",
        "Clear night skies enhancing effectiveness of thermal imaging and night vision devices",
        "Strong crosswinds affecting accuracy of indirect fire and air-delivered munitions"
    ]
}

# ============================================================================
# KARGIL HISTORICAL TIMELINE - Complete 92 Days
# ============================================================================
def generate_kargil_historical_timeline():
    """Generate complete 92-day historical timeline"""
    timeline = {}
    
    # Define phases with characteristics
    phase_data = {
        "infiltration": {
            "dates": (datetime(1999, 5, 8), datetime(1999, 5, 20)),
            "intensity": "low_to_medium",
            "narrative_theme": "Covert Pakistani infiltration operations under cover of spring thaw",
            "primary_actors_pakistan": [
                "12th Northern Light Infantry - Alpha Company",
                "12th Northern Light Infantry - Bravo Company",
                "5th Northern Light Infantry elements"
            ],
            "primary_actors_india": [
                "3 Punjab Regiment reconnaissance patrols",
                "BSF border posts on routine patrol"
            ],
            "equipment_focus": ["Personal weapons", "climbing equipment", "communications gear", "rations for extended operations"],
            "primary_locations": [
                "Mushkoh Valley infiltration routes",
                "Batalik sector approaches",
                "Drass sector periphery",
                "Tiger Hill approaches",
                "Tololing Complex approaches"
            ]
        },
        "discovery": {
            "dates": (datetime(1999, 5, 21), datetime(1999, 5, 31)),
            "intensity": "medium_to_high",
            "narrative_theme": "Discovery phase - Indian forces realize extent of infiltration",
            "primary_actors_pakistan": [
                "12th Northern Light Infantry in defensive positions",
                "Artillery forward observer teams",
                "Communications detachments"
            ],
            "primary_actors_india": [
                "Multiple reconnaissance units",
                "Artillery preparation units",
                "2 Rajputana Rifles reconnaissance",
                "18 Grenadiers preparation"
            ],
            "equipment_focus": ["Infantry weapons", "observation equipment", "artillery pieces", "communications systems"],
            "primary_locations": [
                "Point 5140 Complex",
                "Tololing approaches",
                "Tiger Hill observation posts",
                "Drass Sector reconnaissance areas",
                "Batalik sector initial contacts"
            ]
        },
        "major_operations": {
            "dates": (datetime(1999, 6, 1), datetime(1999, 7, 20)),
            "intensity": "very_high",
            "narrative_theme": "Intensive combat operations across all sectors",
            "primary_actors_pakistan": [
                "12th Northern Light Infantry defensive operations",
                "5th Northern Light Infantry reinforcements",
                "SSG special operations elements",
                "Artillery support elements"
            ],
            "primary_actors_india": [
                "2 Rajputana Rifles assault operations",
                "18 Grenadiers assault battalions",
                "8 Sikh Light Infantry",
                "13 JAK Rifles",
                "1/11 Gorkha Rifles",
                "192 Mountain Regiment (Artillery)",
                "Indian Air Force close air support"
            ],
            "equipment_focus": [
                "Bofors 155mm artillery",
                "Mirage 2000 aircraft",
                "heavy weapons",
                "bunker-busting munitions",
                "night vision equipment"
            ],
            "primary_locations": [
                "Tololing Complex battle areas",
                "Tiger Hill assault zones",
                "Point 5140 engagement areas",
                "Point 4875 combat zones",
                "Batalik sector operations",
                "Multiple peak assaults across sectors"
            ]
        },
        "conclusion": {
            "dates": (datetime(1999, 7, 21), datetime(1999, 7, 26)),
            "intensity": "medium",
            "narrative_theme": "Pakistani withdrawal and Indian consolidation",
            "primary_actors_pakistan": [
                "Withdrawing Northern Light Infantry elements",
                "Rearguard actions"
            ],
            "primary_actors_india": [
                "Consolidation operations across recaptured positions",
                "Pursuit operations",
                "Position fortification"
            ],
            "equipment_focus": ["Defensive fortifications", "observation equipment", "communications"],
            "primary_locations": [
                "All major peaks - consolidation",
                "LoC restoration operations",
                "Defensive position establishment"
            ]
        },
        "post_war": {
            "dates": (datetime(1999, 7, 27), datetime(1999, 8, 7)),
            "intensity": "low",
            "narrative_theme": "Post-war consolidation and defensive preparation",
            "primary_actors_pakistan": ["Minimal to no presence in Indian territory"],
            "primary_actors_india": [
                "Garrison forces",
                "Engineering units",
                "Logistic support units"
            ],
            "equipment_focus": ["Fortification materials", "winter preparation supplies", "permanent defensive structures"],
            "primary_locations": [
                "All recaptured positions",
                "Forward operating bases",
                "Supply route security points"
            ]
        }
    }
    
    # Major events with specific dates
    major_events_by_date = {
        "1999-05-08": {
            "key_event": "Initial infiltration begins - Batalik and Drass sectors",
            "significance": "major",
            "key_event_type": "infiltration_start",
            "contested_locations": [],
            "controlled_by_pakistan": ["Infiltration routes"],
            "controlled_by_india": ["All forward posts", "Main supply routes"]
        },
        "1999-05-21": {
            "key_event": "Indian patrol discovers Pakistani positions near Point 5140 - War begins",
            "significance": "critical",
            "key_event_type": "major_discovery",
            "contested_locations": ["Point 5140", "Tololing approaches"],
            "controlled_by_pakistan": ["Points 5353, 5240, Tiger Hill, Tololing positions"],
            "controlled_by_india": ["Main supply routes", "base camps", "Drass town"]
        },
        "1999-05-26": {
            "key_event": "Operation Vijay officially launched by Indian Armed Forces",
            "significance": "critical",
            "key_event_type": "operation_launch",
            "contested_locations": ["Multiple peaks across Drass and Batalik sectors"],
            "controlled_by_pakistan": ["Occupied peak positions"],
            "controlled_by_india": ["Base areas", "supply lines"]
        },
        "1999-06-13": {
            "key_event": "Battle for Tololing begins - Intense artillery preparation phase",
            "significance": "critical",
            "key_event_type": "major_battle",
            "contested_locations": ["Tololing Top", "Three Pimples", "Hump Complex", "Tololing Nala"],
            "controlled_by_pakistan": ["Tololing peak complex", "prepared defensive positions"],
            "controlled_by_india": ["Assault positions", "fire support bases", "assembly areas"]
        },
        "1999-06-20": {
            "key_event": "Tololing recaptured by 2 Rajputana Rifles after week of intense combat",
            "significance": "critical",
            "key_event_type": "major_victory",
            "contested_locations": ["Tiger Hill still contested"],
            "controlled_by_pakistan": ["Tiger Hill", "Point 5140 partially", "Point 5353"],
            "controlled_by_india": ["Tololing Complex", "Three Pimples", "Western Spur", "surrounding heights"]
        },
        "1999-06-29": {
            "key_event": "Point 5140 assault operations commence with multi-battalion effort",
            "significance": "critical",
            "key_event_type": "major_battle",
            "contested_locations": ["Point 5140 Complex", "surrounding ridges"],
            "controlled_by_pakistan": ["Point 5140 summit", "defensive positions"],
            "controlled_by_india": ["Approach corridors", "fire support positions"]
        },
        "1999-07-04": {
            "key_event": "Tiger Hill recaptured - Famous 18 Grenadiers night assault",
            "significance": "critical",
            "key_event_type": "major_victory",
            "contested_locations": ["Adjacent peaks being cleared"],
            "controlled_by_pakistan": ["Limited remaining positions", "Point 5353"],
            "controlled_by_india": ["Tiger Hill Complex", "India Saddle", "most major peaks", "observation positions"]
        },
        "1999-07-08": {
            "key_event": "Point 4875 recaptured after determined assault",
            "significance": "major",
            "key_event_type": "major_victory",
            "contested_locations": ["Batalik sector operations"],
            "controlled_by_pakistan": ["Remaining isolated positions"],
            "controlled_by_india": ["Point 4875 Complex", "connecting terrain"]
        },
        "1999-07-14": {
            "key_event": "Batalik sector operations intensify - Multiple peak assaults",
            "significance": "major",
            "key_event_type": "major_battle",
            "contested_locations": ["Jubar Ridge", "Khalubar Complex", "multiple Batalik peaks"],
            "controlled_by_pakistan": ["Remaining Batalik positions under pressure"],
            "controlled_by_india": ["Majority of Drass sector", "increasing Batalik control"]
        },
        "1999-07-21": {
            "key_event": "Pakistani forces begin organized withdrawal from positions",
            "significance": "major",
            "key_event_type": "withdrawal_start",
            "contested_locations": ["Minimal - most peaks recaptured"],
            "controlled_by_pakistan": ["Withdrawal routes only"],
            "controlled_by_india": ["Nearly all recaptured territory", "LoC being restored"]
        },
        "1999-07-26": {
            "key_event": "Victory Day - Official end of Kargil War declared",
            "significance": "critical",
            "key_event_type": "war_end",
            "contested_locations": [],
            "controlled_by_pakistan": ["None in Indian territory"],
            "controlled_by_india": ["All recaptured territory", "LoC fully restored", "defensive consolidation complete"]
        }
    }
    
    # Generate day-by-day timeline
    current_date = datetime(1999, 5, 8)
    end_date = datetime(1999, 8, 7)
    day_number = 1
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Determine phase
        current_phase = None
        phase_info = None
        for phase_name, pdata in phase_data.items():
            if pdata["dates"][0] <= current_date <= pdata["dates"][1]:
                current_phase = phase_name
                phase_info = pdata
                break
        
        # Base timeline entry
        day_data = {
            "day_number": day_number,
            "phase": current_phase,
            "intensity": phase_info["intensity"] if phase_info else "low",
            "narrative_theme": phase_info["narrative_theme"] if phase_info else "Routine operations",
            "primary_actors_pakistan": phase_info["primary_actors_pakistan"] if phase_info else [],
            "primary_actors_india": phase_info["primary_actors_india"] if phase_info else [],
            "equipment_focus": phase_info["equipment_focus"] if phase_info else [],
            "primary_locations": phase_info["primary_locations"] if phase_info else [],
            "weather_conditions": _generate_weather_for_date(current_date),
            "tactical_situation": f"Day {day_number} of operations - {phase_info['narrative_theme'] if phase_info else 'Routine operations'}"
        }
        
        # Check for major events on this date
        if date_str in major_events_by_date:
            major_event = major_events_by_date[date_str]
            day_data.update(major_event)
        else:
            # Regular day - generate based on phase
            day_data["key_event"] = f"{current_phase.replace('_', ' ').title()} operations continue"
            day_data["significance"] = "routine" if phase_info and phase_info["intensity"] in ["low", "low_to_medium"] else "important"
            day_data["contested_locations"] = _get_contested_locations_for_phase(current_phase, day_number)
        
        timeline[date_str] = day_data
        
        current_date += timedelta(days=1)
        day_number += 1
    
    return timeline

def _generate_weather_for_date(date):
    """Generate realistic weather for Kargil region by date"""
    month = date.month
    day = date.day
    
    # May - Spring, snowmelt beginning
    if month == 5:
        if day < 15:
            return "Spring conditions, melting snow, temperatures -5°C to 5°C, intermittent cloud cover"
        else:
            return "Improving weather, temperatures 0°C to 10°C, mostly clear with afternoon clouds"
    
    # June - Early summer, better weather
    elif month == 6:
        if day < 15:
            return "Clear to partly cloudy, temperatures 5°C to 15°C, good visibility for operations"
        else:
            return "Summer conditions, temperatures 10°C to 20°C, excellent visibility, occasional afternoon thunderstorms"
    
    # July - Peak summer
    elif month == 7:
        if day < 15:
            return "Warm summer conditions, temperatures 12°C to 22°C, clear skies, optimal for air operations"
        else:
            return "Continued good weather, temperatures 10°C to 20°C, occasional monsoon clouds from south"
    
    # August - Late summer
    else:
        return "Late summer conditions, temperatures 8°C to 18°C, increasing cloud cover, approaching autumn"

def _get_contested_locations_for_phase(phase, day_number):
    """Get contested locations based on phase and day"""
    if phase == "infiltration":
        return []
    elif phase == "discovery":
        return ["Point 5140", "Tololing approaches", "Tiger Hill observation areas"]
    elif phase == "major_operations":
        if day_number < 40:
            return ["Tololing Complex", "Point 5140", "Tiger Hill", "Point 4875"]
        elif day_number < 60:
            return ["Tiger Hill", "Point 5140", "Point 4875", "Batalik peaks"]
        else:
            return ["Remaining Batalik peaks", "Final positions"]
    elif phase == "conclusion":
        return ["Minimal contested areas"]
    else:
        return []

# Generate timeline once at module load
KARGIL_HISTORICAL_TIMELINE = generate_kargil_historical_timeline()

# ============================================================================
# KARGIL WAR SCENARIO - COMPLETE 92 DAYS
# ============================================================================
KARGIL_SCENARIO = {
    "name": "kargil_war_1999",
    "description": "Kargil War 1999 - Complete intelligence reconstruction from pre-infiltration through post-war consolidation",
    "start_date": "1999-05-08",
    "end_date": "1999-08-07",
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