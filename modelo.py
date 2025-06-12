# backend/model.py
import requests
from bs4 import BeautifulSoup
import re
import datetime
# from transformers import pipeline
import os

# classifier = pipeline("sentiment-analysis",
#                       model="distilbert-base-uncased-finetuned-sst-2-english")

# URLs de listas de palabras positivas y negativas en inglés y español
URL_POSITIVAS_EN = "https://ptrckprry.com/course/wordlist/positive.txt"
URL_NEGATIVAS_EN = "https://ptrckprry.com/course/wordlist/negative.txt"
URL_POSITIVAS_ES = "https://raw.githubusercontent.com/olea/lemarios/master/palabras-positivas.txt"
URL_NEGATIVAS_ES = "https://raw.githubusercontent.com/olea/lemarios/master/palabras-negativas.txt"


def cargar_lista_palabras(url, archivo_cache):
    if os.path.exists(archivo_cache):
        with open(archivo_cache, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    else:
        resp = requests.get(url)
        palabras = [line.strip()
                    for line in resp.text.splitlines() if line.strip()]
        with open(archivo_cache, "w", encoding="utf-8") as f:
            f.write("\n".join(palabras))
        return palabras


palabras_positivas_en = cargar_lista_palabras(
    URL_POSITIVAS_EN, "positivas_en.txt")
palabras_negativas_en = cargar_lista_palabras(
    URL_NEGATIVAS_EN, "negativas_en.txt")
palabras_positivas_es = cargar_lista_palabras(
    URL_POSITIVAS_ES, "positivas_es.txt")
palabras_negativas_es = cargar_lista_palabras(
    URL_NEGATIVAS_ES, "negativas_es.txt")

alarm_words = [
    "¡increíble!", "no lo vas a creer", "impactante", "última hora", "alerta", "escándalo"
]


def detectar_idioma(texto):
    # Detección simple: si hay muchas palabras con tildes, asume español
    if re.search(r"[áéíóúñ]", texto.lower()):
        return "es"
    # Si hay palabras comunes en inglés
    if re.search(r"\b(the|and|is|are|of|to|in|that|it|for|on|with)\b", texto.lower()):
        return "en"
    # Por defecto, español
    return "es"


def analizar_sentimiento_simple(texto, idioma):
    texto = texto.lower()
    if idioma == "es":
        negativos = sum(palabra in texto for palabra in palabras_negativas_es)
        positivos = sum(palabra in texto for palabra in palabras_positivas_es)
    else:
        negativos = sum(palabra in texto for palabra in palabras_negativas_en)
        positivos = sum(palabra in texto for palabra in palabras_positivas_en)
    if negativos > positivos and negativos > 1:
        return "NEGATIVE"
    elif positivos > negativos and positivos > 1:
        return "POSITIVE"
    else:
        return "NEUTRAL"


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

        idioma = detectar_idioma(texto)

        dominios_confiables = ["bbc.com", "cnn.com",
                               "reuters.com", "elpais.com", "chequeado.com", "Enfoquecucutajuridico", "noticucuta", "elespectador", "Bolavip.Colombia", "bolavip.com", "elespectadorcom"]
        resultado["fuente_confiable"] = any(
            dominio in url for dominio in dominios_confiables)

        errores = re.findall(
            r'\b[kzxq]{3,}|[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s0-9.,;:¿?¡!()\']+', texto)
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

        emocion = analizar_sentimiento_simple(texto[:500], idioma)
        if emocion == "NEGATIVE":
            resultado["sin_sensacionalismo"] = False

        positivos = sum(valor is True for clave,
                        valor in resultado.items() if clave != "veredicto")
        resultado["veredicto"] = "Probablemente verdadera" if positivos >= 4 else "Posiblemente falsa"

        return resultado

    except Exception as e:
        resultado["veredicto"] = f"Error: {str(e)}"
        return resultado
