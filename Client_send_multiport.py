import socket
import struct
import datetime
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
    try:
        dados = s.recv(1024)
        return dados.decode()
    except ConnectionResetError:
        return ""

def processar_mensagem(mensagem_recebida):
    if len(mensagem_recebida) < 10:
        return {"erro": "mensagem incompleta ou inválida"}
    return {
        "header": mensagem_recebida[2:6],
        "tipo_mensagem": mensagem_recebida[6:8],
        "codigo_resposta": mensagem_recebida[8:10],
        "resposta": mensagem_recebida[10:],
    }

def imprimir_mensagem(mensagem_recebida):
    for chave, valor in mensagem_recebida.items():
        print(f"{chave.replace('_', ' ').upper()}: {valor}")

def envia_msg_hsm(conexoes, qtde_trn, mensagem, intervalo):
    total_conexoes = len(conexoes)
    print(f"\n➡️ Enviando {qtde_trn} mensagens balanceadas entre {total_conexoes} conexões...\n")

    for i in range(1, qtde_trn + 1):
        indice = (i - 1) % total_conexoes  # Round-robin
        s = conexoes[indice]
        try:
            ip_origem, porta_origem = s.getsockname()
            ip_destino, porta_destino = s.getpeername()

            print(f"🔹 [Conn {indice + 1}] Transação {i}")
            print(f"   Origem: {ip_origem}:{porta_origem} → Destino: {ip_destino}:{porta_destino}")
            print(f"   Mensagem enviada: {mensagem}")

            t1 = datetime.datetime.now()
            enviar_mensagem(s, mensagem)
            resposta = receber_mensagem(s)

            if resposta:
                dados_mensagem = processar_mensagem(resposta)
                print(f"   Resposta recebida:")
                imprimir_mensagem(dados_mensagem)
            else:
                print(f"   ⚠️ Sem resposta do servidor.")

            t2 = datetime.datetime.now()
            print(f"   Tempo: {(t2 - t1).total_seconds()}s\n")

            time.sleep(intervalo)  # intervalo já em segundos
        except (BrokenPipeError, ConnectionResetError):
            print(f"[Conn {indice + 1}] ❌ Falha na conexão. Tentando reconectar...")
            try:
                conexoes[indice] = conectar_servidor(ip_destino, porta_destino)
                print(f"[Conn {indice + 1}] 🔄 Reconectado com sucesso.")
            except Exception as e:
                print(f"[Conn {indice + 1}] Erro ao reconectar: {e}")

# =============================
# Configurações do cliente
# =============================

host_servidor = solicitar_input("Digite o endereço IP (padrão 127.0.0.1): ", str, "127.0.0.1")
porta_servidor = solicitar_input("Digite a porta TCP (padrão 1500): ", int, 1500)
qtde_conexoes = solicitar_input("Digite a quantidade de conexões simultâneas (padrão 1): ", int, 1)
qtde_trn = solicitar_input("Digite a quantidade de transações (padrão 1): ", int, 1)
mensagem = solicitar_input("Digite a mensagem (padrão '0000NO00'): ", str, "0000NO00")
intervalo = solicitar_input("Digite o intervalo entre mensagens (em segundos, ex: 1 ou 0.2): ", float, 1.0)

# =============================
# Abertura das conexões
# =============================

print(f"\nConectando {qtde_conexoes} conexões em {host_servidor}:{porta_servidor}...")
conexoes = []
for i in range(qtde_conexoes):
    try:
        s = conectar_servidor(host_servidor, porta_servidor)
        ip_origem, porta_origem = s.getsockname()
        print(f"✅ Conexão {i + 1} estabelecida: {ip_origem}:{porta_origem} → {host_servidor}:{porta_servidor}")
        conexoes.append(s)
    except Exception as e:
        print(f"❌ Falha ao conectar {i + 1}: {e}")

if not conexoes:
    print("Nenhuma conexão ativa. Encerrando.")
    exit(1)

# =============================
# Envio das mensagens
# =============================

try:
    envia_msg_hsm(conexoes, qtde_trn, mensagem, intervalo)
finally:
    for i, s in enumerate(conexoes):
        ip_origem, porta_origem = s.getsockname()
        ip_destino, porta_destino = s.getpeername()
        s.close()
        print(f"🔒 Conexão {i + 1} encerrada: {ip_origem}:{porta_origem} → {ip_destino}:{porta_destino}")
    print("✅ Todas as conexões encerradas.")
