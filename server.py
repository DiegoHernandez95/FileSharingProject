import socket
import threading
import json
import os

class IndexingServer:
    # hard coding peers because I don't think I'll need more than the 3 asked by the 
    # project guidelines
    
    # the server will authenticate the peers and deal with file interactions
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        
        self.users = {
            "peer1": "pass1",
            "peer2": "pass2",
            "peer3": "pass3"
        }
        self.file_index = {}
        self.connected_peers = {}
        
    def start(self):
        self.sock.listen(5)
        print(f"Server listening on {self.host}:{self.port}")
        threading.Thread(target=self.exit_command, daemon=True).start()
        
        while True:
            try:
                client, _ = self.sock.accept()
                threading.Thread(target=self.client_connection, args=(client,)).start()
            except Exception as e:
                print(f"Error accepting connection: {e}")
                break
            
    def client_connection(self, client):
        try:
            peer_id = self.authenticate_peer(client)
            if not peer_id:
                return
                
            while True:
                data = client.recv(1024).decode()
                if not data:
                    break
                    
                message = json.loads(data)
                command = message.get('command')
                
                if command == 'register':
                    self.register_file(peer_id, message, client)
                elif command == 'search':
                    self.search_files(client, message)
                elif command == 'update_files':
                    self.update_peer_files(peer_id, message)
                    
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client.close()
            
    def authenticate_peer(self, client):
        client.send("Login required. Enter peer ID:".encode())
        peer_id = client.recv(1024).decode().strip()
        
        client.send("Enter password:".encode())
        password = client.recv(1024).decode().strip()
        
        if peer_id in self.users and self.users[peer_id] == password:
            client.send("Authentication successful".encode())
            return peer_id
        client.send("Authentication failed".encode())
        return None
      
    def register_file(self, peer_id, message, client):
        domain_name = message.get('domain_name')
        port = message.get('port')
        self.connected_peers[peer_id] = (domain_name, port)
        
        if 'filename' in message:
            keyword = message.get('keyword')
            filename = message.get('filename')
            
            if keyword not in self.file_index:
                self.file_index[keyword] = []
            self.file_index[keyword].append((domain_name, port, filename))
            print(f"\nFile registered: {filename} with keyword '{keyword}' from {peer_id}")
            client.send("File registered".encode())
            return
        
        for file_info in message.get('files', []):
            keyword = file_info['keyword']
            filename = file_info['filename']
            if keyword not in self.file_index:
                self.file_index[keyword] = []
            self.file_index[keyword].append((domain_name, port, filename))
            print(f"\nFile registered: {filename} with keyword '{keyword}' from {peer_id}")
            
    def search_files(self, client, message):
        keyword = message.get('keyword')
        results = self.file_index.get(keyword, [])
        response = {
            'results': [{'domain_name': r[0], 'port': r[1], 'filename': r[2]} for r in results]
        }
        client.send(json.dumps(response).encode())
        
    def update_peer_files(self, peer_id):
        for keyword in list(self.file_index.keys()):
            self.file_index[keyword] = [
                entry for entry in self.file_index[keyword]
                if entry[0:2] != self.connected_peers[peer_id]
            ]
            if not self.file_index[keyword]:
                del self.file_index[keyword]

    def exit_command(self):
        while True:
            command = input("\nEnter '1' to close server: ")
            if command == '1':
                print("Shutting down server...")
                os._exit(0)

if __name__ == "__main__":
    server = IndexingServer()
    server.start()
