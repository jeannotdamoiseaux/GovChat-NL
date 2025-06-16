import os
import json
import uuid
import hashlib
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

class SubsidyFileStorage:
    """Helper voor het opslaan van subsidiecriteria in bestanden binnen de uploads map"""
    
    def __init__(self, base_dir: str = None):
        # Gebruik een absoluut pad voor de map
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        if base_dir is None:
            # Zorg voor een absoluut pad naar de uploads/subsidies map
            self.base_dir = os.path.join(self.root_dir, "uploads", "subsidies")
        else:
            self.base_dir = base_dir
        
        print(f"SubsidyFileStorage initialiseren...")
        print(f"Root directory: {self.root_dir}")
        print(f"Subsidy storage directory: {self.base_dir}")
            
        # Zorg dat de map bestaat
        try:
            os.makedirs(self.base_dir, exist_ok=True)
            print(f"Directory succesvol aangemaakt/gecontroleerd: {self.base_dir}")
            # Test schrijfpermissies
            test_file = os.path.join(self.base_dir, "test_write.txt")
            with open(test_file, 'w') as f:
                f.write("Test write access")
            os.remove(test_file)
            print("Schrijfpermissies gecontroleerd: OK")
        except Exception as e:
            print(f"FOUT bij maken/testen van directory: {e}")
            print(traceback.format_exc())
            # Probeer fallback naar tijdelijke map
            try:
                import tempfile
                self.base_dir = os.path.join(tempfile.gettempdir(), "subsidies")
                os.makedirs(self.base_dir, exist_ok=True)
                print(f"Fallback naar tijdelijke directory: {self.base_dir}")
            except Exception as e2:
                print(f"Kon ook geen fallback directory maken: {e2}")
    
    def _generate_filename(self, user_id: str) -> str:
        """Genereer een unieke bestandsnaam voor een nieuwe set criteria"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_id = str(uuid.uuid4())[:8]  # Kortere UUID voor in bestandsnamen
        
        return f"subsidy_{user_id}_{timestamp}_{random_id}.json"
    
    def save_criteria(self, user_id: str, criteria: Dict, name: str = None, input_text: str = None) -> str:
        """Sla subsidiecriteria op in een JSON bestand"""
        if not user_id:
            print("FOUT: User ID ontbreekt")
            raise ValueError("User ID moet opgegeven worden")
        
        try:
            # Genereer unieke ID voor deze set criteria
            subsidy_id = str(uuid.uuid4())
            
            # Bereken hash van input tekst indien opgegeven
            content_hash = None
            if input_text:
                content_hash = hashlib.md5(input_text.encode('utf-8')).hexdigest()
            
            # Timestamp voor metadata
            timestamp = datetime.now().isoformat()
            
            # Bereid data voor opslag voor
            data = {
                "id": subsidy_id,
                "user_id": user_id,
                "timestamp": timestamp,
                "name": name or f"Subsidie {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "content_hash": content_hash,
                "criteria": criteria.get("criteria", []),
                "summary": criteria.get("summary", "")
            }
            
            # Genereer bestandsnaam 
            filename = f"subsidy_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{subsidy_id[:8]}.json"
            filepath = os.path.join(self.base_dir, filename)
            
            print(f"Opslaan subsidie data naar bestand: {filepath}")
            
            # Sla op als JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"Succesvol opgeslagen: {subsidy_id}")
            return subsidy_id
            
        except Exception as e:
            print(f"FOUT bij opslaan subsidie data: {e}")
            print(traceback.format_exc())
            raise
    
    def get_criteria_by_id(self, subsidy_id: str, user_id: str = None) -> Optional[Dict]:
        """Haal criteria op basis van ID"""
        for filename in os.listdir(self.base_dir):
            if not filename.endswith('.json'):
                continue
                
            filepath = os.path.join(self.base_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check of dit het gezochte item is
                if data.get("id") == subsidy_id:
                    # Als user_id is opgegeven, valideer toegang
                    if user_id and data.get("user_id") != user_id:
                        continue
                    
                    return data
            except (json.JSONDecodeError, IOError):
                continue
                
        return None
    
    def list_criteria_for_user(self, user_id: str) -> List[Dict]:
        """Lijst alle criteria op die zijn opgeslagen voor een gebruiker"""
        result = []
        
        try:
            # Controleer of de directory bestaat
            if not os.path.exists(self.base_dir):
                print(f"Directory does not exist: {self.base_dir}")
                return []
                
            files = os.listdir(self.base_dir)
            print(f"Found {len(files)} files in {self.base_dir}")
            
            for filename in files:
                if not filename.endswith('.json'):
                    continue
                    
                filepath = os.path.join(self.base_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Alleen items voor deze gebruiker
                    if data.get("user_id") == user_id:
                        result.append(data)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error reading file {filepath}: {e}")
                    continue
            
            # Sorteer op timestamp (nieuwste eerst)
            result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
        except Exception as e:
            print(f"Error in list_criteria_for_user: {e}")
        
        print(f"Returning {len(result)} items for user {user_id}")
        return result
    
    def delete_criteria(self, subsidy_id: str, user_id: str) -> bool:
        """Verwijder een criteria bestand op basis van ID"""
        for filename in os.listdir(self.base_dir):
            if not filename.endswith('.json'):
                continue
                
            filepath = os.path.join(self.base_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check of dit het gezochte item is en van deze gebruiker
                if data.get("id") == subsidy_id and data.get("user_id") == user_id:
                    # Gevonden, verwijder bestand
                    os.remove(filepath)
                    return True
            except (json.JSONDecodeError, IOError):
                continue
                
        return False
    
    def find_by_content_hash(self, content_hash: str, user_id: str) -> Optional[Dict]:
        """Zoek criteria op basis van de content hash (voor deduplicatie)"""
        if not content_hash:
            return None
            
        for filename in os.listdir(self.base_dir):
            if not filename.endswith('.json'):
                continue
                
            filepath = os.path.join(self.base_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check of dit een match is op hash en gebruiker
                if data.get("content_hash") == content_hash and data.get("user_id") == user_id:
                    return data
            except (json.JSONDecodeError, IOError):
                continue
                
        return None