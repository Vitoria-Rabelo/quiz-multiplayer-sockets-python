import socket

def buscar_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(2.0)
        for alvo in ['<broadcast>', '127.0.0.1']:
            try:
                s.sendto("ONDE_ESTA_O_SERVIDOR?".encode(), (alvo, 5001))
                data, addr = s.recvfrom(1024)
                return addr[0]
            except: continue
    return None

if __name__ == "__main__":
    ip = buscar_ip() or input("IP do Servidor: ")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
        try:
            tcp.connect((ip, 6000))
            while True:
                data = tcp.recv(4096)
                if not data: break
                msg = data.decode()
                print(msg, end="", flush=True)
                
                if "Sua resposta:" in msg or "Nickname:" in msg:
                    resp = input()
                    tcp.send(f"{resp}\n".encode())
        except Exception as e:
            print(f"\nConexao encerrada: {e}")