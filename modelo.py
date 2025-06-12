# backend/model.py
import requests
from bs4 import BeautifulSoup
import re
import datetime
from transformers import pipeline

classifier = pipeline("sentiment-analysis")

alarm_words = ["¡increíble!", "no lo vas a creer",
               "impactante", "última hora", "alerta", "escándalo"]


def analizar_noticia(url):
    resultado = {
        "fuente_confiable": False,
        "buena_redaccion": False,
        "fecha_actual": False,
        "tiene_fuentes": False,
        "sin_sensacionalismo": True,
        "veredicto": "Análisis incompleto"
    }

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        texto = soup.get_text(separator=' ', strip=True)

        dominios_confiables = ["bbc.com", "cnn.com",
                               "reuters.com", "elpais.com", "chequeado.com"]
        resultado["fuente_confiable"] = any(
            dominio in url for dominio in dominios_confiables)

        errores = re.findall(
            r'\b[kzxq]{3,}|[^a-zA-Z\s0-9.,;:¿?¡!()\']+', texto)
        resultado["buena_redaccion"] = len(errores) < 5

        fechas = re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', texto)
        if fechas:
            try:
                fecha_detectada = datetime.datetime.strptime(
                    fechas[0], '%d/%m/%Y')
                resultado["fecha_actual"] = abs(
                    (datetime.datetime.now() - fecha_detectada).days) < 90
            except:
                pass

        resultado["tiene_fuentes"] = bool(
            re.search(r"https?://\S+", texto)) or "según" in texto.lower()

        resultado["sin_sensacionalismo"] = not any(
            word in texto.lower() for word in alarm_words)

        emocion = classifier(texto[:500])
        if emocion[0]["label"] == "NEGATIVE" and emocion[0]["score"] > 0.85:
            resultado["sin_sensacionalismo"] = False

        positivos = sum(valor is True for clave,
                        valor in resultado.items() if clave != "veredicto")
        resultado["veredicto"] = "Probablemente verdadera" if positivos >= 4 else "Posiblemente falsa"

        return resultado

    except Exception as e:
        resultado["veredicto"] = f"Error: {str(e)}"
        return resultado
