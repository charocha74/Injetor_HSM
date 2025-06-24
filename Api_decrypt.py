from flask import Flask, request, jsonify
#import binascii

app = Flask(__name__)

def montar_string(data):
    # Prefixo fixo
    resultado = "0000M200"

    # 2 posições para DataFormat
    data_format = data.get("DataFormat", "")
    if data_format == "H":
        resultado += "11"
    elif data_format == "B":
        resultado += "00"
    else:
        raise ValueError("DataFormat inválido. Esperado 'H' ou 'B'.")

    # 3 posições com base nos últimos caracteres do keyId
    key_id = data.get("keyId", "")
    if key_id.endswith("BDK"):
        resultado += "009"
    elif key_id.endswith("DEK"):
        resultado += "00B"
    else:
        raise ValueError("keyId deve terminar com 'BDK' ou 'DEK'.")

    # 1 caractere fixo
    resultado += "U"

    # Hash fixa
    resultado += "F8A9DE93D79D8CD285EA53E5AA2A2C2F"

    # KSNDescriptor (3 caracteres)
    resultado += data.get("KSNDescriptor", "")[:3]

    # KSN
    resultado += data.get("KSN", "")

    # Data
    data_hex = data.get("Data", "")
    tamanho = len(data_hex) // 2  # tamanho em bytes
    print(tamanho)
    tamanho_hex = f"{tamanho:04X}"  # 4 caracteres em hexadecimal
    print(tamanho_hex)
    resultado += tamanho_hex
    resultado += data_hex

    return resultado

@app.route('/montar', methods=['POST'])
def montar():
    try:
        conteudo = request.get_json()
        resultado = montar_string(conteudo)
        print("Mensagem montada:", resultado)

        # Grava no arquivo
        with open("mensagem_saida.txt", "w") as f:
            f.write(resultado + "\n")

        return jsonify({
            "mensagem_montada": resultado,
            "arquivo": "mensagem_saida.txt"
        })
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
