import os
import base64
import hashlib
import secrets

import requests
from flask import Flask, request

app = Flask(__name__)

CLIENT_ID = "6535647082019046"
CLIENT_SECRET = "yNeC9jzE4rr056hSoXHggWmH5H0TTDyX"
REDIRECT_URI = "https://marketrz-callback.onrender.com/callback"

# Guardamos temporalmente el code_verifier para la prueba
code_verifier = secrets.token_urlsafe(64)

def crear_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

@app.route("/")
def inicio():
    return """
    <h1>MarketRZ</h1>
    <p>El callback está funcionando correctamente.</p>
    <p><a href="/login">Conectar Mercado Libre</a></p>
    """

@app.route("/login")
def login():
    challenge = crear_code_challenge(code_verifier)

    url = (
        "https://auth.mercadolibre.com.ar/authorization"
        "?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&code_challenge={challenge}"
        "&code_challenge_method=S256"
    )

    return f"""
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url={url}">
        </head>
        <body>
            <p>Redirigiendo a Mercado Libre...</p>
        </body>
    </html>
    """

@app.route("/callback")
def callback():
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return f"""
        <h1>MarketRZ</h1>
        <p>Mercado Libre devolvió un error:</p>
        <p>{error}</p>
        """

    if not code:
        return """
        <h1>MarketRZ</h1>
        <p>No se recibió ningún código de autorización.</p>
        """

    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
    }

    response = requests.post(
        "https://api.mercadolibre.com/oauth/token",
        data=data,
        headers=headers,
        timeout=30,
    )

    if response.status_code != 200:
        return f"""
        <h1>MarketRZ</h1>
        <p>Error al obtener el token.</p>
        <p>Código HTTP: {response.status_code}</p>
        <pre>{response.text}</pre>
        """

    token_data = response.json()

    # IMPORTANTE:
    # No mostramos el access_token ni el refresh_token en pantalla.
    return """
    <h1>¡Mercado Libre conectado correctamente!</h1>
    <p>MarketRZ recibió la autorización y obtuvo el acceso correctamente.</p>
    <p>Ya podemos continuar con la integración.</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
