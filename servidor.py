import socket
import threading
import time
import json
import os
import random
import urllib.request

# Configurações de Rede
HOST = '0.0.0.0'
PORT_TCP = 6000
PORT_UDP = 5001
MAX_JOGADORES_POR_SALA = 2

# Variáveis de Controle
fila_espera = []
contador_salas = 0
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

def salvar_ranking(ranking):
    with open('ranking.json', 'w', encoding='utf-8') as f:
        json.dump(ranking, f, indent=4)

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

def gerenciar_partida(jogadores, id_sala):
    print(f" Sala {id_sala:02d} em andamento com {len(jogadores)} jogadores.")
    todas_p = carregar_json('perguntas.json', [{"p": "Pergunta erro", "r": "1"}])
    rodada = random.sample(todas_p, min(len(todas_p), 3))
    
    try:
        # Envia LOGO e Início
        for p in jogadores: 
            p['socket'].send(LOGO.encode())
            p['socket'].send(f"\n--- PARTIDA INICIADA (SALA {id_sala:02d}) ---\n".encode())
        
        for q in rodada:
            for p in jogadores: 
                p['socket'].send(f"\nPERGUNTA: {q['p']}\nSua resposta: ".encode())
            
            # Coleta respostas
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
                    p['socket'].send(f"✅ Correto! (+{pts} pts)\n".encode())
                else:
                    p['socket'].send(f"❌ Errado! A resposta era {q['r']}\n".encode())

        # Processamento de Ranking Global
        with lock:
            ranking = carregar_json('ranking.json', {})
            for p in jogadores:
                ranking[p['nome']] = ranking.get(p['nome'], 0) + p['pontos']
            salvar_ranking(ranking)

            resumo = f"\n--- RANKING FINAL DA SALA {id_sala:02d} ---\n"
            for p in jogadores: resumo += f"{p['nome']}: {p['pontos']} pts\n"
            
            top5 = sorted(ranking.items(), key=lambda x: x[1], reverse=True)[:5]
            resumo += "\n🏆 TOP 5 GERAL 🏆\n"
            for i, (n, pts) in enumerate(top5, 1):
                resumo += f"{i}. {n.ljust(15)} | {pts} pts\n"

        for p in jogadores:
            p['socket'].send((resumo + "\nEncerrando conexao em 10s...\n").encode())
            time.sleep(1) # Pequeno delay entre mensagens
        
        time.sleep(10)
        for p in jogadores: p['socket'].close()
        print(f"🏁 Sala {id_sala:02d} finalizada.")

    except Exception as e:
        print(f"⚠️ Erro na Sala {id_sala:02d}: {e}")

def monitor_matchmaking():
    global fila_espera, contador_salas
    while True:
        with lock:
            if len(fila_espera) >= MAX_JOGADORES_POR_SALA:
                contador_salas += 1
                sala_atual = [fila_espera.pop(0) for _ in range(MAX_JOGADORES_POR_SALA)]
                
                print(f"✨ Sala {contador_salas:02d} aberta.")
                # Dispara a thread da partida e continua ouvindo novos jogadores
                threading.Thread(target=gerenciar_partida, args=(sala_atual, contador_salas), daemon=True).start()
        time.sleep(0.5)

if __name__ == "__main__":
    print(f"{LOGO}\n[SERVIDOR QUIZ] Status: Online | Porta: {PORT_TCP}")
    print(f"Capacidade: {MAX_JOGADORES_POR_SALA} jogadores por sala.\n")

    threading.Thread(target=servico_discovery_udp, daemon=True).start()
    threading.Thread(target=monitor_matchmaking, daemon=True).start()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp.bind((HOST, PORT_TCP))
        tcp.listen(10)
        
        while True:
            conn, addr = tcp.accept()
            try:
                conn.send("Nickname: ".encode())
                nome = conn.recv(1024).decode().strip()
                if not nome: nome = f"User_{addr[1]}"
                
                with lock:
                    fila_espera.append({'socket': conn, 'nome': nome, 'pontos': 0})
                    print(f"👤 {nome} entrou na fila. ({len(fila_espera)}/{MAX_JOGADORES_POR_SALA})")
                    
                    msg = f"\nOla {nome}! Voce esta na fila. Jogadores: {len(fila_espera)}/{MAX_JOGADORES_POR_SALA}\n"
                    conn.send(msg.encode())
            except:
                conn.close()