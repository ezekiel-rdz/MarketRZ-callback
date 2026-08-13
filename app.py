import os
import base64
import hashlib
import secrets
import html

import requests
from flask import Flask, request

app = Flask(__name__)

CLIENT_ID = os.environ.get("MELI_CLIENT_ID")
CLIENT_SECRET = os.environ.get("MELI_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "https://marketrz-callback.onrender.com/callback")

# Links generados desde el programa de afiliados de Mercado Libre.
# Agregá aquí nuevos productos cuando los generes en Mercado Libre.
PRODUCTOS = [
    {
        "nombre": "Producto recomendado de Mercado Libre",
        "categoria": "celular",
        "descripcion": "Producto recomendado mediante tu enlace de afiliado.",
        "link": "https://meli.la/1ADMxSm"
    }
]

access_token = None
code_verifier = None


def crear_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


@app.route("/")
def inicio():
    return """
    <!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>MarketRZ</title></head>
    <body style="font-family:Arial;max-width:850px;margin:40px auto;padding:20px;background:#f5f5f5">
    <div style="background:white;padding:25px;border-radius:14px">
    <h1>🛒 MarketRZ</h1><p>Productos recomendados de Mercado Libre.</p>
    <form action="/buscar" method="get">
      <input name="q" placeholder="¿Qué producto buscás?" style="width:65%;padding:12px;border-radius:8px;border:1px solid #ccc">
      <button type="submit" style="padding:12px 18px;border:0;border-radius:8px">🔎 Buscar</button>
    </form>
    <p><a href="/buscar">Ver productos recomendados</a></p>
    <hr><p><a href="/login">🔐 Conectar Mercado Libre</a></p>
    </div></body></html>
    """


@app.route("/login")
def login():
    global code_verifier
    if not CLIENT_ID:
        return "<h1>❌ Falta MELI_CLIENT_ID</h1><p>Revisá Render.</p>"
    if not CLIENT_SECRET:
        return "<h1>❌ Falta MELI_CLIENT_SECRET</h1><p>Revisá Render.</p>"

    code_verifier = secrets.token_urlsafe(64)
    challenge = crear_code_challenge(code_verifier)
    authorization_url = (
        "https://auth.mercadolibre.com.ar/authorization"
        "?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&code_challenge={challenge}"
        "&code_challenge_method=S256"
    )
    return f"""
    <html><head><meta charset="UTF-8"><title>MarketRZ</title></head><body>
    <h1>🛒 MarketRZ</h1><p>Redirigiendo a Mercado Libre...</p>
    <p><a href="{authorization_url}">🔐 Conectar Mercado Libre</a></p>
    <script>window.location.href={authorization_url!r};</script>
    </body></html>
    """


@app.route("/callback")
def callback():
    global access_token
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        desc = html.escape(request.args.get("error_description", ""))
        return f"<h1>❌ Mercado Libre rechazó la autorización</h1><p>Error: {html.escape(error)}</p><pre>{desc}</pre><a href='/login'>Intentar nuevamente</a>"
    if not code:
        return "<h1>❌ No se recibió el código</h1><a href='/login'>Intentar nuevamente</a>"
    if not CLIENT_ID or not CLIENT_SECRET or not code_verifier:
        return "<h1>❌ Falta configuración de OAuth/PKCE</h1><a href='/login'>Intentar nuevamente</a>"

    try:
        response = requests.post(
            "https://api.mercadolibre.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": code_verifier
            }, timeout=15)
    except requests.RequestException as exc:
        return f"<h1>❌ Error de conexión</h1><pre>{html.escape(str(exc))}</pre>"

    if response.status_code != 200:
        return f"<h1>❌ Error al obtener Access Token</h1><p>HTTP: {response.status_code}</p><pre>{html.escape(response.text)}</pre><a href='/login'>Intentar nuevamente</a>"

    try:
        token_response = response.json()
    except ValueError:
        return "<h1>❌ Mercado Libre devolvió una respuesta inválida</h1>"

    access_token = token_response.get("access_token")
    if not access_token:
        return "<h1>❌ No se recibió Access Token</h1>"

    return "<h1>✅ Mercado Libre conectado</h1><p>La autorización fue recibida correctamente.</p><p><a href='/'>🏠 Volver a MarketRZ</a></p>"


@app.route("/buscar")
def buscar():
    consulta = request.args.get("q", "").strip().lower()

    if consulta:
        resultados = [
            p for p in PRODUCTOS
            if consulta in p["nombre"].lower()
            or consulta in p["categoria"].lower()
            or consulta in p["descripcion"].lower()
        ]
    else:
        resultados = PRODUCTOS

    if not resultados:
        return """
        <h1>🛒 MarketRZ</h1>
        <h2>😕 No encontramos ese producto en tus recomendaciones.</h2>
        <p>MarketRZ ahora trabaja con los links de afiliado que generás en Mercado Libre.</p>
        <p><a href='/'>🏠 Volver</a></p>
        """

    tarjetas = ""
    for p in resultados:
        nombre = html.escape(p["nombre"])
        categoria = html.escape(p["categoria"])
        descripcion = html.escape(p["descripcion"])
        link = html.escape(p["link"], quote=True)
        tarjetas += f"""
        <div style="background:white;padding:20px;margin:15px 0;border-radius:12px;box-shadow:0 2px 10px #0001">
          <h2>🛍️ {nombre}</h2>
          <p><strong>Categoría:</strong> {categoria}</p>
          <p>{descripcion}</p>
          <a href="{link}" target="_blank" rel="noopener noreferrer" style="background:#3483fa;color:white;padding:12px 18px;border-radius:8px;text-decoration:none;display:inline-block">🛒 Ver producto en Mercado Libre</a>
        </div>
        """

    return f"""
    <!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>MarketRZ</title></head>
    <body style="font-family:Arial;max-width:850px;margin:40px auto;padding:20px;background:#f5f5f5">
      <h1>🛒 MarketRZ</h1>
      <p>Productos recomendados con tus enlaces de afiliado.</p>
      <form action="/buscar" method="get">
        <input name="q" value="{html.escape(consulta)}" placeholder="Buscar producto" style="width:65%;padding:12px;border:1px solid #ccc;border-radius:8px">
        <button type="submit" style="padding:12px 18px;border:0;border-radius:8px">🔎 Buscar</button>
      </form>
      {tarjetas}
      <p><a href="/">🏠 Volver al inicio</a></p>
    </body></html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
