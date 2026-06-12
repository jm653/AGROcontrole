from flask import Flask, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime
import os

app = Flask(__name__)

def coletar_cotacao():
    url = "https://www.cotacaodocafe.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    texto = soup.get_text(" ", strip=True)

    arabica_match = re.search(r"Café Arábica R\$ [0-9.,]+", texto)
    conilon_match = re.search(r"Café Conilon R\$ [0-9.,]+", texto)

    arabica = arabica_match.group(0) if arabica_match else "Não encontrado"
    conilon = conilon_match.group(0) if conilon_match else "Não encontrado"

    arabica_valor = re.search(r"R\$ [0-9.,]+", arabica).group(0) if arabica_match else None
    conilon_valor = re.search(r"R\$ [0-9.,]+", conilon).group(0) if conilon_match else None

    if not os.path.exists("cotacao_cafe.csv"):
        with open("cotacao_cafe.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["datahora", "arabica", "conilon"])

    with open("cotacao_cafe.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), arabica_valor, conilon_valor])

    return arabica_valor, conilon_valor

@app.route("/api/cafe")
def cotacao_cafe():
    arabica, conilon = coletar_cotacao()
    return jsonify({
        "arabica": arabica if arabica else "Não encontrado",
        "conilon": conilon if conilon else "Não encontrado"
    })

@app.route("/api/historico")
def historico_cafe():
    dados = []
    if os.path.exists("cotacao_cafe.csv"):
        with open("cotacao_cafe.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) == 3:
                    datahora, arabica, conilon = row
                    dados.append({
                        "datahora": datahora,
                        "arabica": arabica,
                        "conilon": conilon
                    })
    return jsonify(dados)

if __name__ == "__main__":
    app.run(debug=True, port=5001)