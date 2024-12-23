from Crypto.PublicKey import RSA, DSA
from Crypto.Signature import pkcs1_15, DSS
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# loading both RSA and DSA keys takes quite a while
# so only RSA keys will be generated on start up
class CryptoFunctions:
    def __init__(self):
        self.private_key = RSA.generate(2048)
        self.public_key = self.private_key.publickey()
        
        self.dsa_private_key = None
        self.dsa_public_key = None
        
        self.aes_key = get_random_bytes(32)
        self.aes_iv = get_random_bytes(16)
        
        self.peer_aes_keys = {}
            
    def create_rsa_signature(self, data):
        h = SHA256.new(data)
        signature = pkcs1_15.new(self.private_key).sign(h)
        return signature
        
    def create_dsa_signature(self, data):
        if not self.dsa_private_key:
            self.dsa_private_key = DSA.generate(2048)
            self.dsa_public_key = self.dsa_private_key.publickey()
        h = SHA256.new(data)
        verifier = DSS.new(self.dsa_private_key, 'fips-186-3')
        signature = verifier.sign(h)
        return signature
        
    def verify_rsa_signature(self, data, signature, public_key):
        try:
            h = SHA256.new(data)
            pkcs1_15.new(public_key).verify(h, signature)
            return True
        except Exception:
            return False
            
    def verify_dsa_signature(self, data, signature, public_key):
        try:
            h = SHA256.new(data)
            verifier = DSS.new(public_key, 'fips-186-3')
            verifier.verify(h, signature)
            return True
        except Exception as e:
            print(f"DSA signature verification failed: {e}")
            return False
            
    def encrypt_file(self, data, peer_id=None):
        if peer_id and peer_id in self.peer_aes_keys:
            key, iv = self.peer_aes_keys[peer_id]
        else:
            key, iv = self.aes_key, self.aes_iv
            
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(data, AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        return encrypted_data
        
    def decrypt_file(self, encrypted_data, peer_id=None):
        if peer_id and peer_id in self.peer_aes_keys:
            key, iv = self.peer_aes_keys[peer_id]
        else:
            key, iv = self.aes_key, self.aes_iv
            
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(encrypted_data)
        decrypted_data = unpad(decrypted_padded, AES.block_size)
        return decrypted_data
