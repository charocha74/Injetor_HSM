import socket
import struct
import datetime
#import sys
import time

def solicitar_input(mensagem, tipo, padrao):
    valor = input(mensagem)
    if tipo == int:
        return int(valor) if valor else padrao
    elif tipo == float:
        return float(valor) if valor else padrao
    else:
        return valor if valor else padrao

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
    tipo_mensagem = mensagem_recebida[6:8]
    return {
        "header": mensagem_recebida[2:6],
        "tipo_mensagem": mensagem_recebida[6:8],
        "codigo resposta": mensagem_recebida[8:10],
        "reposta": mensagem_recebida[10:],
    }

def imprimir_mensagem(mensagem_recebida):
    for chave, valor in mensagem_recebida.items():
        print(f"{chave.replace('_', ' ').upper()}: {valor}")

def envia_msg_hsm(s, qtde, qtde_trn, mensagem, intervalo):
    while qtde <= qtde_trn:
        try:
            t1 = datetime.datetime.now()
            print(f"Transação {qtde}: {mensagem}")
            enviar_mensagem(s, mensagem)
            mensagem_recebida = receber_mensagem(s)
            dados_mensagem_recebida = processar_mensagem(mensagem_recebida)
            imprimir_mensagem(dados_mensagem_recebida)
            t2 = datetime.datetime.now()
            print(f"Tempo: {(t2 - t1).total_seconds()}")
            time.sleep(intervalo)
            qtde += 1
        except (BrokenPipeError, ConnectionResetError):
            print("Falha ao enviar mensagem")
            s.close()
            time.sleep(intervalo)
            s = conectar_servidor(host_servidor, porta_servidor)
            envia_msg_hsm(s, qtde, qtde_trn, mensagem, intervalo)
            break

#Configurações do cliente
host_servidor = solicitar_input("Digite o endereço IP (padrão 127.0.0.1): ", str, "127.0.0.1" )
qtde_trn = solicitar_input("Digite a quantidade de transações (padrão 1): ", int, 1)
mensagem = solicitar_input("Digite o mensagem: (padrão '0000NO00'): ", str, "0000NO00")
porta_servidor = solicitar_input("Digite a porta tcp (padrão 1500): ", int, 1500)
intervalo = solicitar_input("Digite a intervalo (em ms): ", int, 1.0)

#Conecta ao servidor
print(f"Conectando em {host_servidor}: {porta_servidor}")
s = conectar_servidor(host_servidor, porta_servidor)
print(f"Conectado em {host_servidor}: {porta_servidor}")

try:
    envia_msg_hsm(s, 1, qtde_trn, mensagem, intervalo)
finally:
    #Fecha Conexão
    s.close()
    print("Conexão fechada")