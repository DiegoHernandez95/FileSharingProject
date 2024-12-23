class FileTransfer:
    @staticmethod
    def send_file(sock, filepath):
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            sock.sendall(len(data).to_bytes(8, byteorder='big'))
            sock.sendall(data)
            return True
        except Exception as e:
            print(f"Error sending file: {e}")
            return False

    @staticmethod
    def receive_file(sock, filepath):
        try:
            size_bytes = sock.recv(8)
            if not size_bytes:
                return False
            filesize = int.from_bytes(size_bytes, byteorder='big')
            
            data = sock.recv(filesize)
            with open(filepath, 'wb') as f:
                f.write(data)
            return len(data) == filesize
        except Exception as e:
            print(f"Error receiving file: {e}")
            return False