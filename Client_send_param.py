import socket
import struct
import datetime
import time
import argparse

def conectar_servidor(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s

def enviar_mensagem(s, mensagem):
    tamanho_mensagem = len(mensagem)
    tamanho_bytes = struct.pack('!H', tamanho_mensagem)
    mensagem_enviada = tamanho_bytes + mensagem.encode()
    s.sendall(mensagem_enviada)

def receber_mensagem(s):
    mensagem_recebida = s.recv(1024)
    return mensagem_recebida.decode()

def processar_mensagem(mensagem_recebida):
    return {
        "header": mensagem_recebida[2:6],
        "tipo_mensagem": mensagem_recebida[6:8],
        "codigo resposta": mensagem_recebida[8:10],
        "reposta": mensagem_recebida[10:],
    }

def imprimir_mensagem(mensagem_recebida):
    for chave, valor in mensagem_recebida.items():
        print(f"{chave.replace('_', ' ').upper()}: {valor}")

def envia_msg_hsm(s, qtde, qtde_trn, mensagem, intervalo, host, port):
    while qtde <= qtde_trn:
        try:
            t1 = datetime.datetime.now()
            print(f"Transação {qtde}: {mensagem}")
            enviar_mensagem(s, mensagem)
            mensagem_recebida = receber_mensagem(s)
            dados_mensagem_recebida = processar_mensagem(mensagem_recebida)
            imprimir_mensagem(dados_mensagem_recebida)
            t2 = datetime.datetime.now()
            print(f"Tempo: {(t2 - t1).total_seconds()}s")
            time.sleep(intervalo)
            qtde += 1
        except (BrokenPipeError, ConnectionResetError):
            print("Falha ao enviar mensagem. Reconectando...")
            s.close()
            time.sleep(intervalo)
            s = conectar_servidor(host, port)
            envia_msg_hsm(s, qtde, qtde_trn, mensagem, intervalo, host, port)
            break

# Argumentos de linha de comando
parser = argparse.ArgumentParser(description="Cliente para envio de mensagens TCP.")
parser.add_argument('--host', type=str, default='127.0.0.1', help='Endereço IP do servidor (padrão: 127.0.0.1)')
parser.add_argument('--port', type=int, default=1500, help='Porta TCP do servidor (padrão: 1500)')
parser.add_argument('--qtde', type=int, default=1, help='Quantidade de transações (padrão: 1)')
parser.add_argument('--mensagem', type=str, default='0000NO00', help='Mensagem a ser enviada (padrão: "0000NO00")')
parser.add_argument('--intervalo', type=float, default=1.0, help='Intervalo entre mensagens em segundos (padrão: 1.0)')

args = parser.parse_args()

print(f"Conectando em {args.host}:{args.port}")
s = conectar_servidor(args.host, args.port)
print(f"Conectado em {args.host}:{args.port}")

try:
    envia_msg_hsm(s, 1, args.qtde, args.mensagem, args.intervalo, args.host, args.port)
finally:
    s.close()
    print("Conexão fechada")
