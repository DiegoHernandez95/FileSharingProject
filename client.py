from Interactions import Interactions
import pwinput

# had to make some serious separation of responsibility
# it was clogging up this file so I just made it into a main function
def main():
    print("=== P2P File Sharing System ===")
    peer_id = input("Enter peer ID: ")
    password = pwinput.pwinput(prompt="Enter password: ")
    
    peer = Interactions(peer_id, password)
    peer.connect_to_server()
    peer.menu()

if __name__ == "__main__":
    main()
