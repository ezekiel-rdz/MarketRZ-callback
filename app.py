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

    # Crear nuevo PKCE para esta autorización
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
    # ERROR DE MERCADO LIBRE
    # -----------------------------------------------------

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
            <a href="/login">
                🔐 Intentar nuevamente
            </a>
        </p>
        """

    # -----------------------------------------------------
    # SIN CODE
    # -----------------------------------------------------

    if not code:

        return """
        <h1>❌ No se recibió el código</h1>

        <p>
        Mercado Libre no envió el código de autorización.
        </p>

        <a href="/login">
            Intentar nuevamente
        </a>
        """

    # -----------------------------------------------------
    # VERIFICAR VARIABLES
    # -----------------------------------------------------

    if not CLIENT_ID:

        return """
        <h1>❌ Falta MELI_CLIENT_ID</h1>
        """

    if not CLIENT_SECRET:

        return """
        <h1>❌ Falta MELI_CLIENT_SECRET</h1>
        """

    if not code_verifier:

        return """
        <h1>❌ Falta PKCE</h1>

        <p>
        Volvé a iniciar la autorización desde /login.
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
        <h1>❌ Error de conexión</h1>

        <pre>{str(e)}</pre>
        """

    # -----------------------------------------------------
    # ERROR TOKEN
    # -----------------------------------------------------

    if response.status_code != 200:

        return f"""
        <h1>❌ Error al obtener el Access Token</h1>

        <p>
        HTTP: {response.status_code}
        </p>

        <pre>{response.text}</pre>

        <p>
            <a href="/login">
                Intentar nuevamente
            </a>
        </p>
        """

    try:

        token_response = response.json()

    except ValueError:

        return """
        <h1>❌ Respuesta inválida</h1>
        """

    access_token = token_response.get(
        "access_token"
    )

    if not access_token:

        return """
        <h1>❌ No se recibió Access Token</h1>
        """

    # =====================================================
    # PRUEBA AUTOMÁTICA DEL TOKEN
    # =====================================================

    test_url = (
        "https://api.mercadolibre.com/users/me"
    )

    test_headers = {

        "Authorization":
            f"Bearer {access_token}",

        "Accept":
            "application/json"
    }

    try:

        test_response = requests.get(
            test_url,
            headers=test_headers,
            timeout=15
        )

    except requests.RequestException as e:

        return f"""
        <h1>❌ Error probando el token</h1>

        <pre>{str(e)}</pre>
        """

    # =====================================================
    # TOKEN FUNCIONA
    # =====================================================

    if test_response.status_code == 200:

        try:

            usuario = test_response.json()

        except ValueError:

            usuario = {}

        user_id = usuario.get(
            "id",
            "No disponible"
        )

        nickname = usuario.get(
            "nickname",
            "No disponible"
        )

        return f"""
        <!DOCTYPE html>

        <html>

        <head>

            <title>
                MarketRZ - Token OK
            </title>

        </head>

        <body>

            <h1>
                ✅ TOKEN FUNCIONA
            </h1>

            <h2>
                Mercado Libre autorizó correctamente a MarketRZ
            </h2>

            <hr>

            <h3>
                👤 Usuario
            </h3>

            <p>
                {nickname}
            </p>

            <h3>
                🆔 ID de usuario
            </h3>

            <p>
                {user_id}
            </p>

            <hr>

            <p>
                ✅ Client ID correcto
            </p>

            <p>
                ✅ Client Secret correcto
            </p>

            <p>
                ✅ PKCE correcto
            </p>

            <p>
                ✅ Access Token válido
            </p>

            <p>
                ✅ API de Mercado Libre responde correctamente
            </p>

            <hr>

            <p>
                Ahora podemos probar el acceso a productos.
            </p>

            <p>
                <a href="/promocionar">
                    📦 Probar producto
                </a>
            </p>

        </body>

        </html>
        """

    # =====================================================
    # TOKEN NO AUTORIZADO
    # =====================================================

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            MarketRZ - Error de autorización
        </title>

    </head>

    <body>

        <h1>
            ❌ EL TOKEN NO PUDO SER VALIDADO
        </h1>

        <p>
            Código HTTP:
            <strong>
                {test_response.status_code}
            </strong>
        </p>

        <h3>
            Respuesta de Mercado Libre:
        </h3>

        <pre>
{test_response.text}
        </pre>

        <hr>

        <p>
        Esto nos permitirá determinar si el problema
        está en el token o específicamente en el acceso
        a publicaciones.
        </p>

        <p>
            <a href="/login">
                🔐 Intentar nuevamente
            </a>
        </p>

    </body>

    </html>
    """


# =========================================================
# ANALIZAR PRODUCTO
# =========================================================

@app.route(
    "/promocionar",
    methods=["GET", "POST"]
)
def promocionar():

    if request.method == "GET":

        return """
        <!DOCTYPE html>

        <html>

        <head>

            <title>
                MarketRZ - Producto
            </title>

        </head>

        <body>

            <h1>
                🛒 MarketRZ
            </h1>

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
                    style="width:400px;"
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
        <h1>
            🔐 Mercado Libre no está conectado
        </h1>

        <p>
        Primero conectá tu cuenta.
        </p>

        <a href="/login">
            🔐 Conectar Mercado Libre
        </a>
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
        <h1>
            ❌ Enlace no válido
        </h1>

        <p>
        No encontramos un ID de publicación MLA.
        </p>

        <a href="/promocionar">
            Volver
        </a>
        """

    item_id = match.group(1).upper()

    api_url = (
        f"https://api.mercadolibre.com/items/{item_id}"
    )

    api_headers = {

        "Authorization":
            f"Bearer {access_token}",

        "Accept":
            "application/json"
    }

    try:

        response = requests.get(
            api_url,
            headers=api_headers,
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
            ❌ Mercado Libre rechazó la consulta
        </h1>

        <p>
            Código HTTP:
            {response.status_code}
        </p>

        <pre>
{response.text}
        </pre>

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
        <h1>
            ❌ Respuesta inválida
        </h1>
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

        <title>
            MarketRZ - Resultado
        </title>

    </head>

    <body>

        <h1>
            🛒 MarketRZ
        </h1>

        <h2>
            ✅ Producto encontrado
        </h2>

        {imagen_html}

        <h3>
            📌 Título
        </h3>

        <p>
            {titulo}
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

        <a href="/promocionar">
            🔎 Analizar otro producto
        </a>

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
