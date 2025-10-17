from flask import Flask, request, jsonify
import json
import socket
import configparser
import os
import struct

# /d:/GIT/Injetor_HSM/api_nonce.py
# Exponha uma API GET que recebe o conteúdo JSON (do nonce.json) via parâmetro `nonce`
# Exemplo de chamada:
#   GET /send_nonce?nonce={"randomValueLength":64}
#
# Requisitos implementados (ajustado para prefixo de 2 bytes com tamanho da mensagem):
# - valida existência de randomValueLength (int)
# - verifica múltiplo de 8 e <= 256 (assumido 256 como limite)
# - lê IP e PORT do arquivo hsm.cfg (seção [hsm], chaves ip e port)
# - envia comando TCP com 2 bytes iniciais (big-endian) contendo o tamanho da mensagem seguida da mensagem "0000N0<tamanho>"
# - retorna JSON com o retorno da conexão TCP excluindo as 8 primeiras posições

app = Flask(__name__)

HSM_CFG_PATH = os.path.join(os.path.dirname(__file__), "hsm.cfg")
MAX_LENGTH = 256  # conforme requisito ("não pode ser maior que 256")
MULTIPLE_OF = 8
TCP_TIMEOUT = 5.0  # segundos

def read_hsm_config(cfg_path=HSM_CFG_PATH):
    cfg = configparser.ConfigParser()
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"Config file not found: {cfg_path}")
    cfg.read(cfg_path)
    if 'hsm' not in cfg:
        raise KeyError("Missing [hsm] section in config")
    ip = cfg['hsm'].get('ip_address')
    port = cfg['hsm'].getint('port', fallback=None)
    if not ip or port is None:
        raise KeyError("hsm.cfg must contain ip and port in [hsm] section")
    return ip, port

def send_tcp_command(ip, port, message_str):
    """
    Envia mensagem com prefixo de 2 bytes (big-endian) contendo o tamanho da mensagem (em bytes),
    seguido pelo corpo da mensagem (codificado em UTF-8). Retorna a resposta decodada.
    """
    body = message_str.encode('utf-8')
    if len(body) > 0xFFFF:
        raise ValueError("message too long for 2-byte length prefix")
    prefix = struct.pack('>H', len(body))  # 2 bytes big-endian
    data = prefix + body

    with socket.create_connection((ip, port), timeout=TCP_TIMEOUT) as s:
        s.sendall(data)
        chunks = []
        try:
            s.settimeout(TCP_TIMEOUT)
            while True:
                data_recv = s.recv(4096)
                if not data_recv:
                    break
                chunks.append(data_recv)
                if len(data_recv) < 4096:
                    break
        except socket.timeout:
            pass
        resp_bytes = b"".join(chunks)
        try:
            return resp_bytes.decode('utf-8', errors='replace')
        except Exception:
            return resp_bytes.decode('latin-1', errors='replace')

@app.route('/send_nonce', methods=['POST'])
def send_nonce():
    # Suporta POST com JSON no body (application/json) ou formulário/query com campos 'nonce' (JSON string) ou 'file'
    payload = None
    nonce_param = request.values.get('nonce')  # combina args e form
    file_param = request.values.get('file')

    # Se houver JSON no body e for um objeto, usa diretamente
    try:
        json_body = request.get_json(silent=True)
    except Exception:
        json_body = None

    if isinstance(json_body, dict):
        payload = json_body
    else:
        if file_param:
            if not os.path.exists(file_param):
                return jsonify({"error": "arquivo não encontrado"}), 400
            try:
                with open(file_param, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
            except Exception as e:
                return jsonify({"error": "conteúdo JSON inválido no arquivo", "detail": str(e)}), 400
        elif nonce_param:
            try:
                payload = json.loads(nonce_param)
            except Exception as e:
                return jsonify({"error": "conteúdo JSON inválido em 'nonce'", "detail": str(e)}), 400
        else:
            return jsonify({"error": "parâmetro 'nonce' (JSON) ou 'file' requerido"}), 400

    if not isinstance(payload, dict):
        return jsonify({"error": "conteudo invalido: payload deve ser um objeto JSON"}), 400

    if 'randomValueLength' not in payload:
        return jsonify({"error": "conteudo invalido: campo 'randomValueLength' ausente"}), 400
    try:
        length = int(payload['randomValueLength'])
    except Exception:
        return jsonify({"error": "conteudo invalido: 'randomValueLength' deve ser inteiro"}), 400

    if length <= 0 or (length % MULTIPLE_OF) != 0 or length > MAX_LENGTH:
        return jsonify({"error": "conteudo invalido"}), 400

    # Construir comando (corpo) e enviar via TCP com prefixo de 2 bytes indicando o tamanho do corpo
    command_body = f"0000N0{length}"
    try:
        ip, port = read_hsm_config()
    except Exception as e:
        return jsonify({"error": "configuração hsm inválida", "detail": str(e)}), 500

    try:
        resp = send_tcp_command(ip, port, command_body)
    except Exception as e:
        return jsonify({"error": "falha na conexão TCP", "detail": str(e)}), 502

    # Excluir as 8 primeiras posições (caracteres) do retorno e devolver JSON
    result = resp[8:] if len(resp) > 8 else ""
    return jsonify({"sent_command_body": command_body, "response_without_8": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)