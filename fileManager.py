import json

# functions to save add or get files
class FileManager:
    def __init__(self, peer_id):
        self.filename = f"{peer_id}_files.json"
        self.files = {}
        try:
            with open(self.filename, 'r') as f:
                self.files = json.load(f)
        except FileNotFoundError:
            pass
        
    def _save_files(self):
        with open(self.filename, 'w') as f:
            json.dump(self.files, f)
            
    def add_file(self, filename, keyword):
        self.files[filename] = keyword
        self._save_files()
        
    def get_files(self):
        return self.files
