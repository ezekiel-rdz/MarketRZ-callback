import os
import base64
import hashlib
import secrets
import re

import requests
from flask import Flask, request

app = Flask(__name__)

# =========================================================
# CONFIGURACIÓN
# =========================================================

CLIENT_ID = os.environ.get("6535647082019046")
CLIENT_SECRET = os.environ.get("yNeC9jzE4rr056hSoXHggWmH5H0TTDyX")

REDIRECT_URI = os.environ.get(
    "REDIRECT_URI",
    "https://marketrz-callback.onrender.com/callback"
)

# Token temporal de Mercado Libre
access_token = None

# PKCE
code_verifier = secrets.token_urlsafe(64)


# =========================================================
# CREAR CODE CHALLENGE
# =========================================================

def crear_code_challenge(verifier):
    digest = hashlib.sha256(
        verifier.encode("utf-8")
    ).digest()

    return base64.urlsafe_b64encode(
        digest
    ).decode("utf-8").rstrip("=")


# =========================================================
# INICIO
# =========================================================

@app.route("/")
def inicio():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MarketRZ</title>
    </head>
    <body>

        <h1>🛒 MarketRZ</h1>

        <p>El servidor está funcionando correctamente.</p>

        <p>
            <a href="/login">
                🔐 Conectar Mercado Libre
            </a>
        </p>

        <p>
            <a href="/promocionar">
                📦 Analizar un producto
            </a>
        </p>

    </body>
    </html>
    """


# =========================================================
# LOGIN
# =========================================================

@app.route("/login")
def login():

    global code_verifier

    if not CLIENT_ID:
        return """
        <h1>❌ Falta CLIENT_ID</h1>
        <p>
        Configurá CLIENT_ID en las variables de entorno de Render.
        </p>
        """

    code_challenge = crear_code_challenge(
        code_verifier
    )

    authorization_url = (
        "https://auth.mercadolibre.com.ar/authorization"
        "?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&code_challenge={code_challenge}"
        "&code_challenge_method=S256"
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh"
              content="0; url={authorization_url}">
    </head>

    <body>

        <p>
            Redirigiendo a Mercado Libre...
        </p>

        <p>
            Si no te redirige automáticamente:
        </p>

        <p>
            <a href="{authorization_url}">
                Hacé clic acá
            </a>
        </p>

    </body>
    </html>
    """


# =========================================================
# CALLBACK
# =========================================================

@app.route("/callback")
def callback():

    global access_token

    code = request.args.get("code")
    error = request.args.get("error")

    if error:

        error_description = request.args.get(
            "error_description",
            ""
        )

        return f"""
        <h1>❌ Mercado Libre rechazó la autorización</h1>

        <p>
            Error: {error}
        </p>

        <pre>{error_description}</pre>

        <p>
            <a href="/">
                Volver a MarketRZ
            </a>
        </p>
        """

    if not code:
        return """
        <h1>❌ No se recibió el código de autorización</h1>

        <p>
        Mercado Libre no envió el parámetro "code".
        </p>

        <a href="/login">
            Intentar nuevamente
        </a>
        """

    if not CLIENT_ID:
        return """
        <h1>❌ Falta CLIENT_ID</h1>
        """

    if not CLIENT_SECRET:
        return """
        <h1>❌ Falta CLIENT_SECRET</h1>
        """

    # =====================================================
    # SOLICITAR ACCESS TOKEN
    # =====================================================

    token_url = "https://api.mercadolibre.com/oauth/token"

    token_data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier
    }

    try:

        response = requests.post(
            token_url,
            data=token_data,
            timeout=15
        )

    except requests.RequestException as e:

        return f"""
        <h1>❌ Error de conexión</h1>

        <p>
        No se pudo comunicar con Mercado Libre.
        </p>

        <pre>{str(e)}</pre>
        """

    if response.status_code != 200:

        return f"""
        <h1>❌ Error al obtener el token</h1>

        <p>
        Código HTTP: {response.status_code}
        </p>

        <pre>{response.text}</pre>

        <p>
            <a href="/login">
                Intentar nuevamente
            </a>
        </p>
        """

    try:

        token_data_response = response.json()

    except ValueError:

        return """
        <h1>❌ Mercado Libre devolvió una respuesta inválida</h1>
        """

    access_token = token_data_response.get(
        "access_token"
    )

    if not access_token:

        return """
        <h1>❌ No se recibió el Access Token</h1>
        """

    return """
    <!DOCTYPE html>
    <html>

    <head>
        <title>MarketRZ conectado</title>
    </head>

    <body>

        <h1>✅ Mercado Libre conectado correctamente</h1>

        <p>
        MarketRZ recibió la autorización correctamente.
        </p>

        <p>
            <a href="/promocionar">
                📦 Analizar un producto
            </a>
        </p>

    </body>

    </html>
    """


# =========================================================
# PROMOCIONAR / ANALIZAR PRODUCTO
# =========================================================

@app.route("/promocionar", methods=["GET", "POST"])
def promocionar():

    if request.method == "GET":

        return """
        <!DOCTYPE html>
        <html>

        <head>
            <title>MarketRZ - Analizar producto</title>
        </head>

        <body>

            <h1>🛒 MarketRZ</h1>

            <h2>
                Analizar producto de Mercado Libre
            </h2>

            <form method="POST">

                <label>
                    Pegá el enlace del producto:
                </label>

                <br><br>

                <input
                    type="text"
                    name="url"
                    placeholder="https://www.mercadolibre.com.ar/..."
                    style="width: 400px;"
                    required
                >

                <br><br>

                <button type="submit">
                    🔎 Analizar producto
                </button>

            </form>

        </body>

        </html>
        """

    if not access_token:

        return """
        <h1>🔐 Mercado Libre no está conectado</h1>

        <p>
        Primero tenés que conectar tu cuenta.
        </p>

        <p>
            <a href="/login">
                🔐 Conectar Mercado Libre
            </a>
        </p>
        """

    url = request.form.get(
        "url",
        ""
    ).strip()

    match = re.search(
        r"(MLA\d+)",
        url,
        re.IGNORECASE
    )

    if not match:

        return """
        <h1>❌ Enlace no válido</h1>

        <p>
        No encontramos un ID de publicación
        de Mercado Libre.
        </p>

        <p>
        Verificá que hayas pegado un enlace válido.
        </p>

        <p>
            <a href="/promocionar">
                Volver
            </a>
        </p>
        """

    item_id = match.group(1).upper()

    api_url = (
        f"https://api.mercadolibre.com/items/{item_id}"
    )

    api_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    try:

        response = requests.get(
            api_url,
            headers=api_headers,
            timeout=15
        )

    except requests.RequestException as e:

        return f"""
        <h1>❌ Error de conexión</h1>

        <p>
        MarketRZ no pudo comunicarse con Mercado Libre.
        </p>

        <pre>{str(e)}</pre>

        <p>
            <a href="/promocionar">
                Volver
            </a>
        </p>
        """

    if response.status_code != 200:

        return f"""
        <h1>❌ Mercado Libre rechazó la consulta</h1>

        <p>
        Código de respuesta: {response.status_code}
        </p>

        <pre>{response.text}</pre>

        <p>
            <a href="/promocionar">
                Volver
            </a>
        </p>
        """

    try:

        producto = response.json()

    except ValueError:

        return """
        <h1>❌ Respuesta inválida</h1>

        <p>
        Mercado Libre no devolvió JSON válido.
        </p>
        """

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

    permalink = producto.get(
        "permalink",
        url
    )

    thumbnail = producto.get(
        "thumbnail"
    )

    imagen_html = ""

    if thumbnail:

        imagen_html = f"""
        <p>
            <img
                src="{thumbnail}"
                width="300"
                alt="Producto"
            >
        </p>
        """

    return f"""
    <!DOCTYPE html>
    <html>

    <head>
        <title>MarketRZ - Resultado</title>
    </head>

    <body>

        <h1>🛒 MarketRZ</h1>

        <h2>✅ Producto encontrado</h2>

        {imagen_html}

        <h3>📌 Título</h3>

        <p>
        {titulo}
        </p>

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
            <a href="{permalink}" target="_blank">
                Ver publicación en Mercado Libre
            </a>
        </p>

        <hr>

        <p>
            <a href="/promocionar">
                🔎 Analizar otro producto
            </a>
        </p>

    </body>

    </html>
    """


# =========================================================
# INICIAR SERVIDOR
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
