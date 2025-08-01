
import socket
from time import sleep

HOST = '127.0.0.1'
PORT = 1111

def send_command(sock, cmd):
    print(f"[CLIENT] Sending: {cmd}")
    sock.sendall(cmd.encode())
    response = sock.recv(1024).decode()
    print(f"[CLIENT] Received: {response}")
    return response

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))

        # Step 1: Handshake
        response = send_command(sock, "CMD=ARE YOU OK!")
        if response.strip() != "REPLY=OK!":
            print("[CLIENT] Server not ready. Exiting.")
            return

        print("[CLIENT] Server OK. Starting server control loop...")
 

        while True:
            # Step 2: Startup
            response = send_command(sock, "CMD=STARTUP!")
            if response.strip() != "REPLY=STARTUP COMPLETED!":
                print("[CLIENT] Server failed to start up. Exiting.")
                return
            print("[CLIENT] Server startup successful. Proceeding to move_to_next.")

            #Step3: Clamping
            response = send_command(sock, "CMD=CLAMPING!")
            if response.strip() != "REPLY=CLAMPING COMPLETED!":
                print("[CLIENT] Server failed to clamp digital output port(DO). Exiting.")
                return
            print("[CLIENT] Server clamp digital output porter(DO) OK.")             

            #Step 4: Move to next repeatedly
            while True:
                response = send_command(sock, "CMD=MOVE2NEXT!")
                if response.strip() == "REPLY=FINISHED!":
                    print("[CLIENT] Motion sequence loop complete. Starting next loop before release.\n")
                    ##Step2: Release
                    response = send_command(sock, "CMD=RELEASE!")
                    if response.strip() != "REPLY=RELEASE COMPLETED!":
                        print("[CLIENT] Server failed to release digital output port(DO). Exiting.")
                        return       
                    print("[CLIENT] Server release digital output porter(DO) OK.") 
                    break
                elif response.strip() == "REPLY=MOVE2NEXT COMPLETED!":
                    sleep(0.5)  # simulate waiting between moves
                else:
                    print("[CLIENT] Unexpected response. Aborting loop.")
                    return


            sleep(1)  # optional: wait before restarting loop

if __name__ == "__main__":
    main()

