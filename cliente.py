import socket
import sys

def buscar_ip_local():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(1.5)
        try:
            s.sendto("ONDE_ESTA_O_SERVIDOR?".encode(), ("<broadcast>", 5001))
            data, addr = s.recvfrom(1024)
            return addr[0]
        except: return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        endereco = sys.argv[1]
    else:
        endereco = buscar_ip_local() or input("Endereço do Servidor (IP ou Ngrok): ")

    if ":" in endereco:
        ip, porta = endereco.split(":")
        porta = int(porta)
    else:
        ip = endereco
        porta = 6000

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
        try:
            tcp.connect((ip, porta))
            while True:
                data = tcp.recv(4096)
                if not data: 
                    print("\nConexão encerrada pelo servidor.")
                    break
                msg = data.decode()
                print(msg, end="", flush=True)
                
                # Responde se for Nickname, Pergunta ou Lobby (>)
                if any(x in msg for x in ["Sua resposta:", "Nickname:", ">"]):
                    tcp.send((input() + "\n").encode())
        except Exception as e:
            print(f"\nErro: {e}")