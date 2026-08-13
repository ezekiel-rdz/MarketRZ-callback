import os
import base64
import hashlib
import secrets
import re

import requests
from flask import Flask, request

app = Flask(__name__)

CLIENT_ID = "6535647082019046"
CLIENT_SECRET = "yNeC9jzE4rr056hSoXHggWmH5H0TTDyX"
REDIRECT_URI = "https://marketrz-callback.onrender.com/callback"

code_verifier = secrets.token_urlsafe(64)

# Token temporal de Mercado Libre
access_token = None


def crear_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


@app.route("/")
def inicio():
    return """
    <h1>🛒 MarketRZ</h1>

    <p>El callback está funcionando correctamente.</p>

    <p>
        <a href="/login">🔐 Conectar Mercado Libre</a>
    </p>

    <p>
        <a href="/promocionar">📦 Analizar producto</a>
    </p>
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
    global access_token

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
        <h1>❌ Error al obtener el token</h1>
        <p>Código HTTP: {response.status_code}</p>
        <pre>{response.text}</pre>
        """

    token_data = response.json()

    access_token = token_data.get("access_token")

    if not access_token:
        return """
        <h1>❌ No se recibió el token</h1>
        """

    return """
    <h1>✅ Mercado Libre conectado correctamente</h1>

    <p>
        MarketRZ recibió la autorización correctamente.
    </p>

    <p>
        <a href="/promocionar">
            📦 Analizar un producto
        </a>
    </p>
    """


@app.route("/promocionar", methods=["GET", "POST"])
def promocionar():

    if request.method == "GET":
        return """
        <html>

        <head>
            <title>MarketRZ - Analizar producto</title>
        </head>

        <body>

            <h1>🛒 MarketRZ</h1>

            <h2>Analizar producto de Mercado Libre</h2>

            <form method="POST">

                <input
                    type="url"
                    name="url"
                    placeholder="Pegá aquí el enlace de Mercado Libre"
                    style="width:500px; padding:10px;"
                    required
                >

                <br><br>

                <button type="submit">
                    🔍 Analizar producto
                </button>

            </form>

        </body>

        </html>
        """

    url = request.form.get("url", "").strip()

    match = re.search(
        r"(MLA\d+)",
        url,
        re.IGNORECASE
    )

    if not match:
        return """
        <h1>❌ No pude encontrar la publicación</h1>

        <p>
        Verificá que hayas pegado un enlace válido de Mercado Libre.
        </p>

        <a href="/promocionar">
            Volver
        </a>
        """

    item_id = match.group(1).upper()

    if not access_token:
        return """
        <h1>🔐 Mercado Libre no está conectado</h1>

        <p>
        Primero tenés que conectar tu cuenta.
        </p>

        <a href="/login">
            Conectar Mercado Libre
        </a>
        """

    api_url = (
        f"https://api.mercadolibre.com/items/{item_id}"
    )

    api_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            api_url,
            headers=api_headers,
            timeout=15,
        )

    except requests.RequestException:
        return """
        <h1>❌ Error de conexión</h1>

        <p>
        MarketRZ no pudo comunicarse con Mercado Libre.
        </p>

        <a href="/promocionar">
            Volver
        </a>
        """

    if response.status_code != 200:
        return f"""
        <h1>❌ Mercado Libre rechazó la consulta</h1>

        <p>
        Código de respuesta: {response.status_code}
        </p>

        <pre>{response.text}</pre>

        <a href="/promocionar">
            Volver
        </a>
        """

    producto = response.json()

    titulo = producto.get(
        "title",
        "Sin título"
    )

    precio = producto.get(
        "price",
        "No disponible"
    )

    moneda = producto.get(
        "currency_id",
        ""
    )

    condicion = producto.get(
        "condition",
        "No disponible"
    )

    categoria = producto.get(
        "category_id",
        "No disponible"
    )

    imagen = ""

    pictures = producto.get(
        "pictures",
        []
    )

    if pictures:
        imagen = (
            pictures[0].get("secure_url")
            or pictures[0].get("url", "")
        )

    imagen_html = ""

    if imagen:
        imagen_html = f"""
        <img
            src="{imagen}"
            width="300"
            alt="Producto"
        >
        """

    return f"""
    <html>

    <head>
        <title>MarketRZ - Producto</title>
    </head>

    <body>

        <h1>🛒 MarketRZ</h1>

        <h2>{titulo}</h2>

        {imagen_html}

        <h3>💰 Precio</h3>

        <p>
            {precio} {moneda}
        </p>

        <h3>📦 Condición</h3>

        <p>
            {condicion}
        </p>

        <h3>🏷️ Categoría</h3>

        <p>
            {categoria}
        </p>

        <h3>🔗 Publicación</h3>

        <p>
            <a
                href="{url}"
                target="_blank"
            >
                Ver producto en Mercado Libre
            </a>
        </p>

        <br>

        <a href="/promocionar">
            🔄 Analizar otro producto
        </a>

    </body>

    </html>
    """


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
