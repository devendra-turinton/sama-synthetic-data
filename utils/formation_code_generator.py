import logging
from typing import Dict, List, Tuple
from config import INDIAN_FORMATIONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FormationCodeGenerator:
    """
    Generate unique 10-character formation codes for Indian Army units.
    Format: [CMD(2)][CORPS(2)][DIV(2)][BDE(2)][UNIT(2)]
    Example: NC140870A1 = Northern Command > XIV Corps > 8 Div > 70 Bde > Unit A1
    """
    
    def __init__(self):
        self.formations = INDIAN_FORMATIONS
        self.unit_registry = {}  # Track all generated units
        self.unit_counter = {}  # Counter for generating unique unit codes
        
    def generate_unit_hierarchy(self, 
                                cmd_code: str,
                                corps_code: str, 
                                div_code: str,
                                bde_code: str,
                                num_units: int = 3) -> List[Dict]:
        """
        Generate unit hierarchy with formation codes.
        Default: 3 units per brigade (following 3:1 ratio)
        """
        units = []
        
        # Get full names from structure
        cmd_data = self.formations["commands"].get(cmd_code, {})
        corps_data = cmd_data.get("corps", {}).get(corps_code, {})
        div_data = corps_data.get("divisions", {}).get(div_code, {})
        bde_data = div_data.get("brigades", {}).get(bde_code, {})
        
        # Create key for unit counter
        counter_key = f"{cmd_code}{corps_code}{div_code}{bde_code}"
        if counter_key not in self.unit_counter:
            self.unit_counter[counter_key] = 0
        
        for i in range(num_units):
            self.unit_counter[counter_key] += 1
            unit_suffix = self._generate_unit_suffix(self.unit_counter[counter_key])
            
            # Generate 10-char formation code
            fmn_code = f"{cmd_code}{corps_code}{div_code}{bde_code}{unit_suffix}"
            
            unit = {
                "fmn_code": fmn_code,
                "cmd_name": cmd_data.get("name", ""),
                "corps_name": corps_data.get("name", ""),
                "div_name": div_data.get("name", ""),
                "bde_name": bde_data.get("name", ""),
                "unit_name": f"{bde_data.get('name', '')} Battalion {unit_suffix}",
                "level": "Battalion"
            }
            
            units.append(unit)
            self.unit_registry[fmn_code] = unit
            
        return units
    
    def _generate_unit_suffix(self, counter: int) -> str:
        """Generate 2-char alphanumeric suffix for units (A1, A2, B1, etc.)"""
        # Use letters A-Z and numbers 1-9
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        letter_idx = (counter - 1) // 9
        number = ((counter - 1) % 9) + 1
        
        if letter_idx < len(letters):
            return f"{letters[letter_idx]}{number}"
        else:
            # Fallback for very large numbers
            return f"{counter:02d}"
    
    def generate_brigade_units(self, cmd_code: str, corps_code: str, 
                               div_code: str, bde_code: str) -> Dict:
        """Generate unit info for a specific brigade"""
        return {
            "brigade_id": f"{cmd_code}{corps_code}{div_code}{bde_code}",
            "units": self.generate_unit_hierarchy(cmd_code, corps_code, div_code, bde_code)
        }
    
    def generate_support_unit(self, cmd_code: str, corps_code: str,
                             unit_type: str = "intelligence") -> Dict:
        """Generate support unit (BSF, Intelligence, etc.)"""
        # Support units get special codes
        support_codes = {
            "intelligence": "IN",
            "bsf": "BF",
            "signals": "SG",
            "artillery": "AR"
        }
        
        type_code = support_codes.get(unit_type, "SU")
        counter_key = f"{cmd_code}{corps_code}{type_code}"
        
        if counter_key not in self.unit_counter:
            self.unit_counter[counter_key] = 0
        
        self.unit_counter[counter_key] += 1
        unit_num = f"{self.unit_counter[counter_key]:02d}"
        
        # Support units use special format: [CMD][CORPS][TYPE][00][NUM]
        fmn_code = f"{cmd_code}{corps_code}{type_code}00{unit_num}"
        
        cmd_data = self.formations["commands"].get(cmd_code, {})
        corps_data = cmd_data.get("corps", {}).get(corps_code, {})
        
        unit = {
            "fmn_code": fmn_code,
            "cmd_name": cmd_data.get("name", ""),
            "corps_name": corps_data.get("name", ""),
            "div_name": "",
            "bde_name": "",
            "unit_name": self._get_support_unit_name(unit_type, self.unit_counter[counter_key]),
            "level": "Corps"
        }
        
        self.unit_registry[fmn_code] = unit
        return unit
    
    def _get_support_unit_name(self, unit_type: str, counter: int) -> str:
        """Get realistic support unit names"""
        names = {
            "intelligence": [
                "Intelligence Fusion Cell",
                "Electronic Warfare Unit 112",
                "Imagery Analysis Cell 06",
                "SIGINT Company 14 Corps"
            ],
            "bsf": [
                "BSF Observation Post Delta-7",
                "BSF Observation Post Alpha-3",
                "BSF Battalion 125",
                "BSF Battalion 136"
            ]
        }
        
        unit_names = names.get(unit_type, [f"{unit_type.title()} Unit {counter}"])
        idx = (counter - 1) % len(unit_names)
        return unit_names[idx]
    
    def get_random_unit_by_level(self, level: str = "Battalion") -> Dict:
        """Get a random unit at specified hierarchy level"""
        if not self.unit_registry:
            # Initialize with some default units if registry is empty
            self.initialize_default_units()
        
        level_units = [u for u in self.unit_registry.values() if u["level"] == level]
        if level_units:
            import random
            return random.choice(level_units)
        return None
    
    def initialize_default_units(self):
        """Initialize registry with key Kargil units"""
        # Generate units for key brigades involved in Kargil
        key_brigades = [
            ("NC", "14", "08", "70"),  # 70 Infantry Brigade
            ("NC", "14", "08", "79"),  # 79 Mountain Brigade
            ("NC", "14", "03", "56"),  # 56 Mountain Brigade
        ]
        
        for cmd, corps, div, bde in key_brigades:
            self.generate_unit_hierarchy(cmd, corps, div, bde)
        
        # Generate intelligence and BSF units
        for _ in range(3):
            self.generate_support_unit("NC", "14", "intelligence")
            self.generate_support_unit("NC", "14", "bsf")
    
    def get_unit_info(self, fmn_code: str) -> Dict:
        """Retrieve unit information by formation code"""
        return self.unit_registry.get(fmn_code, {})
    
    def decode_formation_code(self, fmn_code: str) -> Dict:
        """Decode a 10-character formation code into hierarchy"""
        if len(fmn_code) != 10:
            return {"error": "Invalid formation code length"}
        
        return {
            "cmd_code": fmn_code[0:2],
            "corps_code": fmn_code[2:4],
            "div_code": fmn_code[4:6],
            "bde_code": fmn_code[6:8],
            "unit_code": fmn_code[8:10]
        }