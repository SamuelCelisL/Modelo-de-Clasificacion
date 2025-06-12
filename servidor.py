# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from modelo import analizar_noticia
import os


app = Flask(__name__)
CORS(app)  # Permite conexión desde React


@app.route('/analizar', methods=['POST'])
def analizar():
    data = request.get_json()
    url = data.get('url', '')

    if not url:
        return jsonify({"error": "Falta la URL"}), 400

    resultado = analizar_noticia(url)
    return jsonify(resultado)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
