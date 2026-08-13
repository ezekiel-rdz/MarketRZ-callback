import os
import base64
import hashlib
import secrets
import random

import requests
from flask import Flask, request

app = Flask(__name__)

# =========================================================
# CONFIGURACIÓN
# =========================================================

CLIENT_ID = os.environ.get("MELI_CLIENT_ID")
CLIENT_SECRET = os.environ.get("MELI_CLIENT_SECRET")

REDIRECT_URI = os.environ.get(
    "REDIRECT_URI",
    "https://marketrz-callback.onrender.com/callback"
)

# Token temporal
access_token = None

# PKCE
code_verifier = None


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

        <p>
            El servidor está funcionando correctamente.
        </p>

        <p>
            <a href="/login">
                🔐 Conectar Mercado Libre
            </a>
        </p>

        <p>
            <a href="/buscar">
                🔎 Buscar publicación aleatoria
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
        <h1>❌ Falta MELI_CLIENT_ID</h1>

        <p>
        Revisá las variables de entorno de Render.
        </p>
        """

    if not CLIENT_SECRET:

        return """
        <h1>❌ Falta MELI_CLIENT_SECRET</h1>

        <p>
        Revisá las variables de entorno de Render.
        </p>
        """

    # Crear nuevo PKCE
    code_verifier = secrets.token_urlsafe(64)

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

        <title>
            MarketRZ - Conectar
        </title>

        <meta
            http-equiv="refresh"
            content="0; url={authorization_url}"
        >

    </head>

    <body>

        <h1>🛒 MarketRZ</h1>

        <p>
            Redirigiendo a Mercado Libre...
        </p>

        <p>
            Si no ocurre automáticamente:
        </p>

        <p>
            <a href="{authorization_url}">
                🔐 Conectar Mercado Libre
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

    # -----------------------------------------------------
    # ERROR DE AUTORIZACIÓN
    # -----------------------------------------------------

    if error:

        error_description = request.args.get(
            "error_description",
            ""
        )

        return f"""
        <h1>
            ❌ Mercado Libre rechazó la autorización
        </h1>

        <p>
            Error: {error}
        </p>

        <pre>{error_description}</pre>

        <p>
            <a href="/login">
                🔐 Intentar nuevamente
            </a>
        </p>
        """

    # -----------------------------------------------------
    # NO HAY CODE
    # -----------------------------------------------------

    if not code:

        return """
        <h1>
            ❌ No se recibió el código
        </h1>

        <p>
        Mercado Libre no envió el código de autorización.
        </p>

        <a href="/login">
            Intentar nuevamente
        </a>
        """

    # -----------------------------------------------------
    # COMPROBAR CONFIGURACIÓN
    # -----------------------------------------------------

    if not CLIENT_ID:

        return """
        <h1>
            ❌ Falta MELI_CLIENT_ID
        </h1>
        """

    if not CLIENT_SECRET:

        return """
        <h1>
            ❌ Falta MELI_CLIENT_SECRET
        </h1>
        """

    if not code_verifier:

        return """
        <h1>
            ❌ Falta PKCE
        </h1>

        <p>
        Volvé a iniciar la conexión desde /login.
        </p>

        <a href="/login">
            🔐 Intentar nuevamente
        </a>
        """

    # =====================================================
    # OBTENER ACCESS TOKEN
    # =====================================================

    token_url = (
        "https://api.mercadolibre.com/oauth/token"
    )

    token_data = {

        "grant_type":
            "authorization_code",

        "client_id":
            CLIENT_ID,

        "client_secret":
            CLIENT_SECRET,

        "code":
            code,

        "redirect_uri":
            REDIRECT_URI,

        "code_verifier":
            code_verifier
    }

    try:

        response = requests.post(
            token_url,
            data=token_data,
            timeout=15
        )

    except requests.RequestException as e:

        return f"""
        <h1>
            ❌ Error de conexión
        </h1>

        <pre>{str(e)}</pre>
        """

    if response.status_code != 200:

        return f"""
        <h1>
            ❌ Error al obtener Access Token
        </h1>

        <p>
            HTTP: {response.status_code}
        </p>

        <pre>{response.text}</pre>

        <a href="/login">
            Intentar nuevamente
        </a>
        """

    try:

        token_response = response.json()

    except ValueError:

        return """
        <h1>
            ❌ Mercado Libre devolvió una respuesta inválida
        </h1>
        """

    access_token = token_response.get(
        "access_token"
    )

    if not access_token:

        return """
        <h1>
            ❌ No se recibió Access Token
        </h1>
        """

    # =====================================================
    # COMPROBAR TOKEN CON /USERS/ME
    # =====================================================

    try:

        user_response = requests.get(
            "https://api.mercadolibre.com/users/me",
            headers={
                "Authorization":
                    f"Bearer {access_token}"
            },
            timeout=15
        )

    except requests.RequestException as e:

        return f"""
        <h1>
            ❌ Error comprobando el token
        </h1>

        <pre>{str(e)}</pre>
        """

    if user_response.status_code != 200:

        return f"""
        <h1>
            ❌ El token no fue aceptado
        </h1>

        <p>
            HTTP:
            {user_response.status_code}
        </p>

        <pre>{user_response.text}</pre>

        <a href="/login">
            Intentar nuevamente
        </a>
        """

    try:

        usuario = user_response.json()

    except ValueError:

        usuario = {}

    nickname = usuario.get(
        "nickname",
        "No disponible"
    )

    user_id = usuario.get(
        "id",
        "No disponible"
    )

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            MarketRZ conectado
        </title>

    </head>

    <body>

        <h1>
            ✅ Mercado Libre conectado
        </h1>

        <p>
            El token funciona correctamente.
        </p>

        <hr>

        <h3>
            👤 Usuario
        </h3>

        <p>
            {nickname}
        </p>

        <h3>
            🆔 ID
        </h3>

        <p>
            {user_id}
        </p>

        <hr>

        <p>
            <a href="/buscar">
                🔎 Buscar publicación aleatoria
            </a>
        </p>

    </body>

    </html>
    """


# =========================================================
# BUSCAR PUBLICACIÓN ALEATORIA
# =========================================================

@app.route("/buscar")
def buscar():

    # =====================================================
    # IMPORTANTE:
    # La búsqueda de publicaciones se realiza sobre
    # Mercado Libre Argentina.
    # =====================================================

    palabras = [
        "celular",
        "notebook",
        "televisor",
        "auriculares",
        "zapatillas",
        "playstation",
        "computadora",
        "monitor",
        "tablet",
        "smartwatch"
    ]

    palabra = random.choice(
        palabras
    )

    # Buscar 20 resultados para poder elegir
    # uno aleatoriamente.

    search_url = (
        "https://api.mercadolibre.com/sites/MLA/search"
    )

    params = {
        "q": palabra,
        "limit": 20
    }

    try:

        response = requests.get(
            search_url,
            params=params,
            timeout=15
        )

    except requests.RequestException as e:

        return f"""
        <h1>
            ❌ Error de conexión
        </h1>

        <pre>{str(e)}</pre>
        """

    # =====================================================
    # ERROR DE BÚSQUEDA
    # =====================================================

    if response.status_code != 200:

        return f"""
        <h1>
            ❌ Error buscando publicaciones
        </h1>

        <p>
            HTTP:
            {response.status_code}
        </p>

        <pre>{response.text}</pre>

        <p>
            Palabra utilizada:
            {palabra}
        </p>

        <a href="/buscar">
            🔄 Intentar nuevamente
        </a>
        """

    try:

        datos = response.json()

    except ValueError:

        return """
        <h1>
            ❌ Mercado Libre devolvió JSON inválido
        </h1>
        """

    resultados = datos.get(
        "results",
        []
    )

    if not resultados:

        return f"""
        <h1>
            ❌ No encontramos publicaciones
        </h1>

        <p>
            Búsqueda:
            {palabra}
        </p>

        <a href="/buscar">
            🔄 Intentar nuevamente
        </a>
        """

    # =====================================================
    # ELEGIR PUBLICACIÓN ALEATORIA
    # =====================================================

    producto = random.choice(
        resultados
    )

    item_id = producto.get(
        "id",
        "No disponible"
    )

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
        "#"
    )

    thumbnail = producto.get(
        "thumbnail"
    )

    seller = producto.get(
        "seller",
        {}
    )

    seller_id = seller.get(
        "id",
        "No disponible"
    )

    # =====================================================
    # IMAGEN
    # =====================================================

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

    # =====================================================
    # RESULTADO
    # =====================================================

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            MarketRZ - Producto encontrado
        </title>

    </head>

    <body>

        <h1>
            🛒 MarketRZ
        </h1>

        <h2>
            🎯 Publicación encontrada
        </h2>

        <p>
            MarketRZ buscó automáticamente
            una publicación en Mercado Libre Argentina.
        </p>

        <hr>

        {imagen_html}

        <h3>
            📌 Título
        </h3>

        <p>
            {titulo}
        </p>

        <h3>
            🆔 ID de publicación
        </h3>

        <p>
            {item_id}
        </p>

        <h3>
            💰 Precio
        </h3>

        <p>
            {precio} {moneda}
        </p>

        <h3>
            📦 Condición
        </h3>

        <p>
            {condicion}
        </p>

        <h3>
            🏷️ Categoría
        </h3>

        <p>
            {categoria}
        </p>

        <h3>
            👤 Vendedor
        </h3>

        <p>
            {seller_id}
        </p>

        <h3>
            🔎 Búsqueda utilizada
        </h3>

        <p>
            {palabra}
        </p>

        <h3>
            🔗 Publicación
        </h3>

        <p>

            <a
                href="{permalink}"
                target="_blank"
            >
                Ver publicación en Mercado Libre
            </a>

        </p>

        <hr>

        <p>

            <a href="/buscar">
                🎲 Buscar otra publicación
            </a>

        </p>

        <p>

            <a href="/">
                🏠 Volver al inicio
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
