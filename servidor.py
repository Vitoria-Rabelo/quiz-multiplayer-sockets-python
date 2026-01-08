import socket
import threading
import time
import json
import os
import random

HOST = '0.0.0.0'
PORT_TCP = 6000
PORT_UDP = 5001
MIN_JOGADORES = 2

ranking_global = {}
fila_espera = []
lock = threading.Lock()

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

def iniciar_partida(jogadores):
    todas_perguntas = carregar_json('perguntas.json', [])
    if not todas_perguntas: return
    rodada = random.sample(todas_perguntas, min(len(todas_perguntas), 3))
    
    try:
        for p in jogadores: 
            p['socket'].send(LOGO.encode())
            time.sleep(0.1)
            p['socket'].send("\n--- PARTIDA INICIADA ---\n".encode())
        
        for q in rodada:
            for p in jogadores: 
                p['socket'].send(f"\nPERGUNTA: {q['p']}\nSua resposta: ".encode())
            
            for p in jogadores:
                inicio = time.time()
                resp = p['socket'].recv(1024).decode().strip()
                fim = time.time()
                
                if resp == q['r']:
                    pts = max(2, int(11 - (fim - inicio)))
                    p['pontos'] += pts
                    p['socket'].send(f"Correto! (+{pts} pts)\n".encode())
                else:
                    p['socket'].send("Errado! (0 pts)\n".encode())

        with lock:
            global ranking_global
            ranking_global = carregar_json('ranking.json', {})
            for p in jogadores:
                ranking_global[p['nome']] = ranking_global.get(p['nome'], 0) + p['pontos']
            salvar_ranking()

            resumo = "\n--- RANKING DA RODADA ---\n"
            for p in jogadores: resumo += f"{p['nome']}: {p['pontos']} pts\n"
            resumo += "\n🏆 TOP 5 HISTORICO 🏆\n"
            top5 = sorted(ranking_global.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (nome, pts) in enumerate(top5, 1):
                resumo += f"{i}. {nome.ljust(15)} | {pts} pts\n"

        for p in jogadores:
            p['socket'].send(resumo.encode())
            time.sleep(0.5)
            p['socket'].close()
    except: pass

def monitor_fila():
    while True:
        if len(fila_espera) >= MIN_JOGADORES:
            with lock:
                sala = [fila_espera.pop(0) for _ in range(MIN_JOGADORES)]
            threading.Thread(target=iniciar_partida, args=(sala,)).start()
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=servico_discovery_udp, daemon=True).start()
    threading.Thread(target=monitor_fila, daemon=True).start()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp.bind((HOST, PORT_TCP))
        tcp.listen(5)
        print("Servidor Quiz Online Pronto!")
        while True:
            conn, addr = tcp.accept()
            conn.send("Nickname: ".encode())
            nome = conn.recv(1024).decode().strip()
            with lock: fila_espera.append({'socket': conn, 'nome': nome, 'pontos': 0})
            conn.send(f"Aguardando oponente...\n".encode())