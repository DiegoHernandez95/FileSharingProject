import os
import socket
import json
import base64
import threading
from crypto import CryptoFunctions
from fileManager import FileManager
from fileTransfer import FileTransfer
from Crypto.PublicKey import RSA

# all the high level peer interactions
class Peer:
    def __init__(self, peer_id, password, host='localhost', port=0):
        self.peer_id = peer_id
        self.password = password
        self.host = host
        self.port = port
        
        self.crypto = CryptoFunctions()
        self.file_manager = FileManager(peer_id)
        
        self.server_socket = None
        self.peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_socket.bind((host, port))
        self.actual_port = self.peer_socket.getsockname()[1]
        self.listen_socket = None
        self.peer_keys = {}
            
    def connect_to_server(self, server_host='localhost', server_port=5000):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((server_host, server_port))
        
        self.server_socket.recv(1024)
        self.server_socket.send(self.peer_id.encode())
        
        self.server_socket.recv(1024)
        self.server_socket.send(self.password.encode())
        
        response = self.server_socket.recv(1024).decode()
        if response != "Authentication successful":
            raise Exception("Authentication failed")
        
        self.peer_socket.listen(5)
        print(f"Listening for peer connections on port {self.actual_port}")
        threading.Thread(target=self.start_listening, daemon=True).start()
        
        for filename, keyword in self.files.items():
            request = {
                'command': 'register',
                'filename': filename,
                'keyword': keyword,
                'domain_name': self.host,
                'port': self.actual_port
            }
            self.server_socket.send(json.dumps(request).encode())
            reg_response = self.server_socket.recv(1024).decode()
            if reg_response != "File registered":
                print(f"Warning: Failed to re-register file {filename}")
        
    def request_file(self, peer_host, peer_port, filename, signature_type='RSA'):
        print(f"Starting file request from {peer_host}:{peer_port}")
        peer_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            peer_sock.connect((peer_host, peer_port))
            public_key_pem = self.public_key.export_key().decode()
            
            key_exchange = {
                'command': 'exchange_key',
                'peer_id': self.peer_id,
                'public_key': public_key_pem,
                'aes_key': base64.b64encode(self.crypto.aes_key).decode(),
                'aes_iv': base64.b64encode(self.crypto.aes_iv).decode()
            }
            peer_sock.send(json.dumps(key_exchange).encode())
            
            peer_key_data = json.loads(peer_sock.recv(1024).decode())
            peer_id = peer_key_data.get('peer_id')
            peer_public_key_pem = peer_key_data.get('public_key')
            
            if peer_id and peer_public_key_pem:
                peer_public_key = RSA.import_key(peer_public_key_pem.encode())
                self.peer_keys[peer_id] = peer_public_key
            
            peer_sock.recv(1024)
            
            request = {
                'command': 'get_file',
                'filename': filename,
                'signature_type': signature_type
            }
            peer_sock.send(json.dumps(request).encode())
            
            metadata = json.loads(peer_sock.recv(1024).decode())
            if metadata.get('error'):
                raise Exception(metadata['error'])
            
            temp_path = f"temp_{os.path.basename(filename)}.encrypted"
            
            success = FileTransfer.receive_file(peer_sock, temp_path)
            if not success:
                raise Exception("File transfer failed")
            
            with open(temp_path, 'rb') as f:
                encrypted_data = f.read()
            
            signature = base64.b64decode(metadata['signature'])
            print("\nVerifying digital signature...")
            print(f"Signature (base64): {base64.b64encode(signature).decode()}")
            
            if signature_type == 'RSA':
                if not self.crypto.verify_rsa_signature(encrypted_data, signature, self.peer_keys[metadata['peer_id']]):
                    raise Exception("RSA signature verification failed")
                print(f"RSA signature from {metadata['peer_id']} verified successfully")
            else:
                if not self.crypto.verify_dsa_signature(encrypted_data, signature, self.peer_keys[metadata['peer_id']]):
                    raise Exception("DSA signature verification failed")
                print(f"DSA signature from {metadata['peer_id']} verified successfully")
            
            decrypted_data = self.decrypt_file(encrypted_data, metadata['peer_id'])
            output_path = f"received_{os.path.basename(filename)}"
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            os.remove(temp_path)
            print("Download completed successfully")
            
        except Exception as e:
            print(f"Error in request_file: {e}")
            raise
        finally:
            peer_sock.close()

    def start_listening(self):
        while True:
            try:
                client, _ = self.peer_socket.accept()
                threading.Thread(target=self.peer_request, args=(client,)).start()
            except Exception as e:
                print(f"Error accepting connection: {e}")
                break
            
    def peer_request(self, client):
        try:
            while True:
                data = client.recv(1024).decode()
                if not data:
                    break
                    
                request = json.loads(data)
                command = request.get('command')
                
                if command == 'exchange_key':
                    peer_id = request.get('peer_id')
                    peer_public_key_pem = request.get('public_key')
                    peer_aes_key = base64.b64decode(request.get('aes_key'))
                    peer_aes_iv = base64.b64decode(request.get('aes_iv'))
                    
                    self.crypto.peer_aes_keys[peer_id] = (peer_aes_key, peer_aes_iv)
                    peer_public_key = RSA.import_key(peer_public_key_pem.encode())
                    self.peer_keys[peer_id] = peer_public_key
                    public_key_pem = self.public_key.export_key().decode()
                    
                    response = {
                        'peer_id': self.peer_id,
                        'public_key': public_key_pem,
                        'aes_key': base64.b64encode(self.crypto.aes_key).decode(),
                        'aes_iv': base64.b64encode(self.crypto.aes_iv).decode()
                    }
                    client.send(json.dumps(response).encode())
                    client.send(b"ready")
                    continue
                    
                elif command == 'get_file':
                    filename = request['filename']
                    signature_type = request.get('signature_type', 'RSA')
                    
                    if filename not in self.files:
                        response = {'error': 'File not found'}
                        client.send(json.dumps(response).encode())
                        break
                    
                    temp_path = f"temp_send_{os.path.basename(filename)}.encrypted"
                    
                    with open(filename, 'rb') as f:
                        file_data = f.read()
                    encrypted_data = self.crypto.encrypt_file(file_data, peer_id)
                    
                    with open(temp_path, 'wb') as f:
                        f.write(encrypted_data)
                    
                    if signature_type == 'RSA':
                        signature = self.crypto.create_rsa_signature(encrypted_data)
                    else:
                        signature = self.crypto.create_dsa_signature(encrypted_data)
                    
                    metadata = {
                        'peer_id': self.peer_id,
                        'signature': base64.b64encode(signature).decode()
                    }
                    client.send(json.dumps(metadata).encode())
                    
                    success = FileTransfer.send_file(client, temp_path)
                    
                    os.remove(temp_path)
                    
                    if not success:
                        raise Exception("File transfer failed")
                    
                    break
                
        except Exception as e:
            print(f"Error handling peer request: {e}")
        finally:
            client.close()

    def search_files(self, keyword):
        if not self.server_socket:
            raise Exception("Not connected to server")
        
        request = {
            'command': 'search',
            'keyword': keyword
        }
        self.server_socket.send(json.dumps(request).encode())
        response = json.loads(self.server_socket.recv(1024).decode())
        return response.get('results', [])

    def add_file(self, filename, keyword, signature_type='RSA'):
        if not os.path.exists(filename):
            raise Exception("File does not exist")
        
        self.file_manager.add_file(filename, keyword)
        request = {
            'command': 'register',
            'filename': filename,
            'keyword': keyword,
            'signature_type': signature_type,
            'domain_name': self.host,
            'port': self.actual_port
        }
        self.server_socket.send(json.dumps(request).encode())
        response = self.server_socket.recv(1024).decode()
        if response != "File registered":
            raise Exception("Failed to register file")

    @property
    def files(self):
        return self.file_manager.get_files()

    @property
    def public_key(self):
        return self.crypto.public_key

    @property
    def private_key(self):
        return self.crypto.private_key

    def encrypt_file(self, data, peer_id=None):
        return self.crypto.encrypt_file(data, peer_id)

    def decrypt_file(self, data, peer_id=None):
        return self.crypto.decrypt_file(data, peer_id)