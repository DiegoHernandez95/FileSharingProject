import os
from peer import Peer


# peers are located in the server.py file
# user names and passwords are stored there
class Interactions(Peer):
    def __init__(self, peer_id, password, host='localhost', port=0):
        super().__init__(peer_id, password, host, port)
        
    def menu(self):
        while True:
            print("\nAvailable commands:")
            print("1. Add file")
            print("2. Search for file")
            print("3. Download file")
            print("4. List my files")
            print("5. Exit")
            
            try:
                choice = input("\nEnter your choice (1-5): ")
                
                if choice == '1':
                    self.add_file_options()
                elif choice == '2':
                    self.search_file()
                elif choice == '3':
                    self.download_file()
                elif choice == '4':
                    self.list_files()
                elif choice == '5':
                    print("Exiting...")
                    break
                else:
                    print("Invalid choice!")
                    
            except Exception as e:
                print(f"Error: {e}")
                
    def add_file_options(self):
        try:
            filename = input("Enter filename: ")
            if not os.path.exists(filename):
                print("File does not exist!")
                return
            
            keyword = input("Enter keyword for the file: ")
            
            print("\nChoose signature type for this file:")
            print("1. RSA")
            print("2. DSA")
            sig_choice = input("Enter choice (1-2): ")
            signature_type = 'RSA' if sig_choice == '1' else 'DSA'
            
            super().add_file(filename, keyword, signature_type)
            print(f"File {filename} added successfully with keyword: {keyword} and {signature_type} signature")
        except Exception as e:
            print(f"Error adding file: {e}")
        
    def search_file(self):
        keyword = input("Enter keyword to search: ")
        results = self.search_files(keyword)
        
        if not results:
            print("No files found with that keyword.")
            return
            
        print("\nFound files:")
        for i, peer in enumerate(results, 1):
            print(f"{i}. {peer['filename']} at {peer['domain_name']}:{peer['port']}")
            
    def download_file(self):
        try:
            keyword = input("Enter keyword to search: ")
            results = self.search_files(keyword)
            
            if not results:
                print("No files found with that keyword.")
                return
            
            print("\nAvailable files:")
            for i, peer in enumerate(results, 1):
                print(f"{i}. {peer['filename']} at {peer['domain_name']}:{peer['port']}")
            
            choice = int(input("\nEnter the number of the file to download (0 to cancel): "))
            if choice == 0:
                return
            if choice < 1 or choice > len(results):
                print("Invalid choice!")
                return
            
            peer = results[choice - 1]
            print(f"\nDownloading {peer['filename']}...")
            try:
                self.request_file(peer['domain_name'], peer['port'], 
                                peer['filename'], peer.get('signature_type', 'RSA'))
                print(f"Digital signature verified: Valid {peer.get('signature_type', 'RSA')} signature")
            except Exception as e:
                print(f"Error during file transfer: {e}")
            
        except ValueError as ve:
            print(f"Invalid input: {ve}")
        except Exception as e:
            print(f"Error: {e}")
            
    def list_files(self):
        if not self.files:
            print("No files available.")
            return
            
        print("\nMy files:")
        for filename, keyword in self.files.items():
            print(f"File: {filename}, Keyword: {keyword}")