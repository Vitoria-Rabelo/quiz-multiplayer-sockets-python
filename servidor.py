import socket
import threading
import time
import json
import os
import random

HOST = '0.0.0.0'
PORT_TCP = 6000
PORT_UDP = 5001
MAX_JOGADORES = 4
MIN_JOGADORES = 2

ranking_global = {}
fila_espera = []
lock = threading.Lock()
partida_em_preparacao = False

LOGO = r"""
_________________________________________
|                                       |
|   / __ \  | |  | |  | |  |___  /      |
|  | |  | | | |  | |  | |     / /       |
|  | |_ | | | |__| |  | |    / /__      |
|   \__\_\   \____/   |_|   /_____|     |
|_______________________________________|
      ||       ||       ||       ||
"""

def carregar_json(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return padrao
    return padrao

def salvar_ranking():
    with open('ranking.json', 'w', encoding='utf-8') as f:
        json.dump(ranking_global, f, indent=4)

def servico_discovery_udp():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', PORT_UDP))
        while True:
            try:
                data, addr = s.recvfrom(1024)
                if data.decode() == "ONDE_ESTA_O_SERVIDOR?":
                    s.sendto("SERVIDOR_AQUI".encode(), addr)
            except: pass

def gerenciar_partida(jogadores):
    todas_p = carregar_json('perguntas.json', [])
    if not todas_p: return
    rodada = random.sample(todas_p, min(len(todas_p), 3))
    
    try:
        for p in jogadores: 
            p['socket'].send(LOGO.encode())
            p['socket'].send("\n--- PARTIDA INICIADA ---\n".encode())
        
        for q in rodada:
            for p in jogadores: 
                p['socket'].send(f"\nPERGUNTA: {q['p']}\nSua resposta: ".encode())
            
            for p in jogadores:
                inicio = time.time()
                try:
                    p['socket'].settimeout(15)
                    resp = p['socket'].recv(1024).decode().strip()
                except: resp = ""
                fim = time.time()
                
                if resp == q['r']:
                    pts = max(2, int(11 - (fim - inicio)))
                    p['pontos'] += pts
                    p['socket'].send(f"Correto! (+{pts} pts)\n".encode())
                else:
                    p['socket'].send(f"Errado! A resposta era {q['r']}\n".encode())

        # Processamento de Ranking
        with lock:
            global ranking_global
            ranking_global = carregar_json('ranking.json', {})
            resumo = "\n--- RESULTADO DA RODADA ---\n"
            for p in jogadores:
                ranking_global[p['nome']] = ranking_global.get(p['nome'], 0) + p['pontos']
                resumo += f"{p['nome']}: {p['pontos']} pts\n"
            salvar_ranking()

            resumo += "\n🏆 TOP 5 HISTORICO 🏆\n"
            top5 = sorted(ranking_global.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (n, pts) in enumerate(top5, 1):
                resumo += f"{i}. {n.ljust(15)} | {pts} pts\n"

        for p in jogadores:
            p['socket'].send((resumo + "\nA janela fechara em 10 segundos.\n").encode())
            time.sleep(10)
            p['socket'].close()
    except Exception as e:
        print(f"Erro na partida: {e}")

def monitor_lobby():
    global fila_espera
    while True:
        with lock:
            # Se atingir 4, começa na hora
            if len(fila_espera) >= MAX_JOGADORES:
                sala = [fila_espera.pop(0) for _ in range(MAX_JOGADORES)]
                threading.Thread(target=gerenciar_partida, args=(sala,)).start()
        time.sleep(1)

def aguardar_comando_inicio(conn, jogador_info):
    global fila_espera
    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if data == "1":
                with lock:
                    if len(fila_espera) >= MIN_JOGADORES:
                        sala_completa = []
                        while fila_espera:
                            sala_completa.append(fila_espera.pop(0))
                        
                        print(f"🚀 Partida iniciada por comando de {jogador_info['nome']}")
                        threading.Thread(target=gerenciar_partida, args=(sala_completa,)).start()
                        break 
                    else:
                        conn.send("Aguarde pelo menos 2 jogadores para iniciar.\n> ".encode())
            if not data: break
    except: pass

if __name__ == "__main__":
    print(f"{LOGO}\nServidor Quiz Online Pronto na porta {PORT_TCP}!")
    threading.Thread(target=servico_discovery_udp, daemon=True).start()
    threading.Thread(target=monitor_lobby, daemon=True).start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp.bind((HOST, PORT_TCP))
        tcp.listen(5)
        while True:
            conn, addr = tcp.accept()
            conn.send("Nickname: ".encode())
            nome = conn.recv(1024).decode().strip()
            
            novo_j = {'socket': conn, 'nome': nome, 'pontos': 0}
            with lock:
                fila_espera.append(novo_j)
                msg = f"\nBem-vindo, {nome}! ({len(fila_espera)}/{MAX_JOGADORES})\n"
                if len(fila_espera) >= MIN_JOGADORES:
                    msg += "Digite '1' para iniciar agora ou aguarde mais jogadores...\n> "
                else:
                    msg += "Aguardando mais jogadores...\n"
                
                # Avisa todos na fila
                for j in fila_espera:
                    try: j['socket'].send(msg.encode())
                    except: pass
            
            # Thread para ouvir se este jogador específico quer iniciar o jogo
            threading.Thread(target=aguardar_comando_inicio, args=(conn, novo_j), daemon=True).start()