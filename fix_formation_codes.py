#!/usr/bin/env python3
"""
Fix Formation Codes Data Type Issue

This script converts formation codes from string format (e.g., 'NC14087001') 
to numeric format suitable for BIGINT database fields. It processes all SQL 
insert files and creates cleaned versions.

The conversion strategy:
- Extract numeric part from formation codes
- Convert to pure integers
- Update SQL insert files with numeric values
"""

import os
import re
import logging
from typing import Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('formation_code_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FormationCodeFixer:
    def __init__(self, data_dir: str = "data/output"):
        self.data_dir = data_dir
        self.sql_files = [
            'elint_kargil_war_1999_inserts.sql',
            'en_activity_kargil_war_1999_inserts.sql',
            'imint_data_kargil_war_1999_inserts.sql',
            'tac_int_kargil_war_1999_inserts.sql',
            'e_sitrep_mst_kargil_war_1999_inserts.sql'
        ]
        self.formation_code_map: Dict[str, int] = {}
    
    def extract_numeric_from_fmn_code(self, fmn_code_str: str) -> int:
        """
        Extract numeric portion from formation code string.
        
        Examples:
        'NC14087001' -> 14087001
        'NC14080000' -> 14080000
        'NC14035601' -> 14035601
        """
        # Remove quotes and extract numbers
        clean_code = fmn_code_str.strip("'\"")
        
        # Extract numeric part (remove NC prefix)
        numeric_match = re.search(r'(\d+)', clean_code)
        if numeric_match:
            numeric_code = int(numeric_match.group(1))
            self.formation_code_map[fmn_code_str] = numeric_code
            return numeric_code
        else:
            logger.warning(f"Could not extract numeric part from: {fmn_code_str}")
            return 0
    
    def fix_sql_file(self, file_path: str) -> Tuple[bool, int]:
        """
        Fix formation codes in a single SQL file.
        
        Returns:
            Tuple of (success: bool, fixes_count: int)
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False, 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_count = 0
            
            # Pattern to match fmn_code with string values
            # Look for fmn_code) VALUES (..., 'NCxxxxxxxx');
            fmn_pattern = r"(fmn_code\)\s+VALUES\s+\([^)]+,\s*)'([^']+)'(\);)"
            
            def replace_fmn_code(match):
                nonlocal fixes_count
                prefix = match.group(1)
                fmn_code_str = match.group(2)
                suffix = match.group(3)
                
                # Convert to numeric
                numeric_code = self.extract_numeric_from_fmn_code(f"'{fmn_code_str}'")
                fixes_count += 1
                
                return f"{prefix}{numeric_code}{suffix}"
            
            # Apply the pattern replacement
            content = re.sub(fmn_pattern, replace_fmn_code, content)
            
            # Also handle cases where fmn_code is in middle of VALUES clause
            middle_pattern = r"(,\s*)'([^']*NC\d+[^']*)'(\s*,)"
            
            def replace_middle_fmn_code(match):
                nonlocal fixes_count
                prefix = match.group(1)
                fmn_code_str = match.group(2)
                suffix = match.group(3)
                
                # Check if this looks like a formation code
                if re.match(r'NC\d+', fmn_code_str):
                    numeric_code = self.extract_numeric_from_fmn_code(f"'{fmn_code_str}'")
                    fixes_count += 1
                    return f"{prefix}{numeric_code}{suffix}"
                else:
                    return match.group(0)  # No change
            
            content = re.sub(middle_pattern, replace_middle_fmn_code, content)
            
            # Write back only if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Fixed {fixes_count} formation codes in {file_path}")
            else:
                logger.info(f"No formation code issues found in {file_path}")
            
            return True, fixes_count
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return False, 0
    
    def fix_all_files(self) -> Dict[str, Tuple[bool, int]]:
        """
        Fix formation codes in all SQL files.
        
        Returns:
            Dictionary mapping file names to (success, fixes_count) tuples
        """
        results = {}
        total_fixes = 0
        
        logger.info("Starting formation code fixes...")
        
        for sql_file in self.sql_files:
            file_path = os.path.join(self.data_dir, sql_file)
            success, fixes_count = self.fix_sql_file(file_path)
            results[sql_file] = (success, fixes_count)
            total_fixes += fixes_count
            
            if success:
                logger.info(f"✅ {sql_file}: {fixes_count} fixes")
            else:
                logger.error(f"❌ {sql_file}: Failed to process")
        
        logger.info(f"Formation code fixing completed. Total fixes: {total_fixes}")
        return results
    
    def create_formation_mapping_report(self) -> str:
        """
        Create a report showing the formation code mappings.
        """
        report = "Formation Code Mappings:\n"
        report += "=" * 50 + "\n"
        
        for original, numeric in sorted(self.formation_code_map.items()):
            report += f"{original} -> {numeric}\n"
        
        return report


def main():
    """Main function to fix formation codes."""
    try:
        fixer = FormationCodeFixer()
        results = fixer.fix_all_files()
        
        # Print summary
        print("\nFormation Code Fix Summary:")
        print("=" * 40)
        
        total_fixes = 0
        for file_name, (success, fixes) in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {file_name}: {fixes} fixes")
            total_fixes += fixes
        
        print(f"\nTotal fixes applied: {total_fixes}")
        
        # Create mapping report
        if fixer.formation_code_map:
            mapping_report = fixer.create_formation_mapping_report()
            print(f"\n{mapping_report}")
            
            # Save mapping report to file
            with open("formation_code_mapping.txt", "w") as f:
                f.write(mapping_report)
            print("📄 Formation code mapping saved to: formation_code_mapping.txt")
    
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()