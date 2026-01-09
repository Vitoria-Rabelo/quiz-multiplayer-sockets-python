import socket
import sys

def buscar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(1.0)
        try:
            s.sendto("ONDE_ESTA_O_SERVIDOR?".encode(), ("<broadcast>", 5001))
            data, addr = s.recvfrom(1024)
            return addr[0]
        except: return "127.0.0.1"

if __name__ == "__main__":
    endereco = sys.argv[1] if len(sys.argv) > 1 else buscar_servidor()
    porta = 6000
    
    if ":" in endereco:
        endereco, porta_str = endereco.split(":")
        porta = int(porta_str)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
        try:
            tcp.connect((endereco, porta))
            while True:
                data = tcp.recv(4096)
                if not data: break
                msg = data.decode()
                print(msg, end="", flush=True)
                
                if "Sua resposta:" in msg or "Nickname:" in msg:
                    tcp.send((input() + "\n").encode())
        except Exception as e:
            print(f"\nConexao encerrada: {e}")