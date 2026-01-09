# Quiz Multiplayer: Socket-Based Network Application

Implementação original de um sistema de Quiz competitivo para a disciplina de **Redes de Computadores**. O projeto demonstra o uso de sockets para comunicação global e multithreading para gerenciamento de lobby dinâmico.

## 🛠️ Tecnologias e Protocolos

O sistema opera na camada de **Transporte** do modelo OSI:

* **TCP (Porta 6000):** Fluxo principal de dados, garantindo entrega confiável e ordenada.
* **UDP (Porta 5001):** Serviço de **Broadcast Discovery** para localização automática do servidor em redes locais.
* **Multithreading:** Gerenciamento de múltiplas threads para permitir que o servidor aceite novos jogadores enquanto outros estão em partida.
* **Tunelamento (Ngrok):** Utilizado para permitir conexões externas (WAN), atravessando NATs e Firewalls.

---

## 🚀 Como Executar

### 1. Iniciar o Servidor
```bash
python3 servidor.py
```

### 2. Conectar Clientes

Rede (LAN)  (Autodescoberta via UDP)
```bash
python3 cliente.py
```

Rede (WAN)
```bash
brew install ngrok
python3 cliente.py 0.tcp.sa.ngrok.io:XXXXX
```
