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

PRODUCTOS = [
    {"nombre": "Auriculares Bluetooth", "categoria": "auriculares", "descripcion": "Auriculares Bluetooth recomendados.", "link": "https://meli.la/24qmdZs"},
    {"nombre": "Samsung Galaxy A16 4G 128GB 4GB RAM Gris", "categoria": "celulares", "descripcion": "Samsung Galaxy A16 4G con 128GB y 4GB de RAM.", "link": "https://meli.la/1KHdAX1"},
    {"nombre": "Samsung Galaxy A07 64GB 4GB RAM Negro", "categoria": "celulares", "descripcion": "Samsung Galaxy A07 64GB con 4GB de RAM.", "link": "https://meli.la/2mM8zKP"},
    {"nombre": "Auriculares Inalámbricos Fan Pro Air31 In-ear Blanco", "categoria": "auriculares", "descripcion": "Auriculares inalámbricos Bluetooth Fan Pro Air31.", "link": "https://meli.la/2o6pkqB"},
    {"nombre": "Moto G17 4+256GB Arándano Rosa", "categoria": "celulares", "descripcion": "Celular Moto G17 con 256GB.", "link": "https://meli.la/1Yw45rp"},
    {"nombre": "Samsung Galaxy Fit3 Pink Gold", "categoria": "smartwatch", "descripcion": "Smartband Samsung Galaxy Fit3 con pantalla AMOLED.", "link": "https://meli.la/2PEV1dh"},
    {"nombre": "Auriculares Sony WH-CH520 Azul", "categoria": "auriculares", "descripcion": "Auriculares Sony Bluetooth inalámbricos.", "link": "https://meli.la/1Ld2W5z"},
    {"nombre": "Samsung Galaxy A16 128GB 4GB RAM Gris", "categoria": "celulares", "descripcion": "Samsung Galaxy A16 con pantalla de 6.7 pulgadas.", "link": "https://meli.la/1S4HviG"},
    {"nombre": "Samsung Galaxy A07 64GB 4GB RAM Violeta Claro", "categoria": "celulares", "descripcion": "Samsung Galaxy A07 64GB con 4GB de RAM.", "link": "https://meli.la/1D4cUSm"},
    {"nombre": "Moto G06 64GB NFC Arabesque", "categoria": "celulares", "descripcion": "Celular Moto G06 de 64GB con NFC.", "link": "https://meli.la/1185xvh"},
    {"nombre": "Repetidor TP-Link RE200 AC750", "categoria": "wifi", "descripcion": "Extensor de señal Wi-Fi doble banda AC750.", "link": "https://meli.la/2Y4jnPw"},
    {"nombre": "Samsung Galaxy A17 128GB 4GB Azul", "categoria": "celulares", "descripcion": "Samsung Galaxy A17 con IA, cámara de 50MP, NFC e IP54.", "link": "https://meli.la/2EipnfR"},
    {"nombre": "Xiaomi Redmi Watch 5 Lite 1.96 Negro", "categoria": "smartwatch", "descripcion": "Smartwatch Xiaomi Redmi Watch 5 Lite.", "link": "https://meli.la/1qyrPgH"},
    {"nombre": "Xiaomi Redmi 15C 128GB Azul", "categoria": "celulares", "descripcion": "Xiaomi Redmi 15C con cámara de 50MP y batería de 6000mAh.", "link": "https://meli.la/1P81inE"},
    {"nombre": "Moto Edge 70 Fusion Country Air", "categoria": "celulares", "descripcion": "Motorola Moto Edge 70 Fusion.", "link": "https://meli.la/2saCKBw"},
    {"nombre": "Repetidor Wi-Fi TP-Link WA850RE V6", "categoria": "wifi", "descripcion": "Extensor de señal Wi-Fi TP-Link.", "link": "https://meli.la/2FQzR14"},
    {"nombre": "Xiaomi Redmi Buds 8 Lite Blanco", "categoria": "auriculares", "descripcion": "Auriculares inalámbricos Xiaomi Redmi Buds 8 Lite.", "link": "https://meli.la/2uAkJRK"},
    {"nombre": "Pava Eléctrica Novohome Digital 2 Litros", "categoria": "electrodomésticos", "descripcion": "Pava eléctrica digital con pantalla táctil.", "link": "https://meli.la/2SUMYh5"},
    {"nombre": "Secador de Pelo Ultracomb Tourmaline Ion Pro SC-4606", "categoria": "electrodomésticos", "descripcion": "Secador de pelo Ultracomb con 3 temperaturas.", "link": "https://meli.la/1tdWKjf"},
    {"nombre": "Pava Eléctrica Atma 1500W 1.8 Litros", "categoria": "electrodomésticos", "descripcion": "Pava eléctrica Atma color blanco.", "link": "https://meli.la/31Mmc9e"},
    {"nombre": "Aspiradora de Mano Vertical 2 en 1 Daewoo Moppy DVC-105", "categoria": "electrodomésticos", "descripcion": "Aspiradora Daewoo con accesorios.", "link": "https://meli.la/2Qm8FwD"},
    {"nombre": "Cafetera Nescafé Dolce Gusto Piccolo XS", "categoria": "electrodomésticos", "descripcion": "Cafetera para cápsulas monodosis.", "link": "https://meli.la/23pyFZB"},
    {"nombre": "Balanza de Cocina Digital 10kg", "categoria": "electrodomésticos", "descripcion": "Balanza electrónica de cocina con luz LED.", "link": "https://meli.la/2Ccfto8"},
    {"nombre": "Máquina 3 en 1 Donas Waflera Cupcake", "categoria": "electrodomésticos", "descripcion": "Máquina eléctrica antiadherente 3 en 1.", "link": "https://meli.la/2cZUcTW"},
    {"nombre": "Microondas Digital 20 Litros 8 Funciones", "categoria": "electrodomésticos", "descripcion": "Microondas digital con funciones táctiles.", "link": "https://meli.la/1dksPZG"},
    {"nombre": "Yogurtera Yelmo 1.4 Litros", "categoria": "electrodomésticos", "descripcion": "Máquina para hacer yogur con 8 frascos.", "link": "https://meli.la/1Q7GLB7"},
    {"nombre": "Xiaomi Redmi Buds 6 Play Rosa", "categoria": "auriculares", "descripcion": "Auriculares Xiaomi Redmi Buds 6 Play.", "link": "https://meli.la/2heTF3n"},
    {"nombre": "Inflador Inalámbrico Gadnic 150 PSI", "categoria": "automotor", "descripcion": "Compresor portátil inalámbrico con pantalla digital.", "link": "https://meli.la/2cUncnJ"},
    {"nombre": "Compresor de Aire Portátil Gadnic 150 PSI", "categoria": "automotor", "descripcion": "Compresor para neumáticos de 50W.", "link": "https://meli.la/1qfsbWw"},
    {"nombre": "Neumático Onyx NY-806 165/70 R13 79T", "categoria": "automotor", "descripcion": "Neumático rodado 13.", "link": "https://meli.la/2jjxo1H"},
    {"nombre": "Neumático Aplus 175/70R13 82T A609", "categoria": "automotor", "descripcion": "Cubierta para auto rodado 13.", "link": "https://meli.la/2W1LMrZ"},
    {"nombre": "Casco para Moto Integral Hawk RS1 Negro XL", "categoria": "motos", "descripcion": "Casco integral para moto talle XL.", "link": "https://meli.la/1zeSTas"},
    {"nombre": "Casco Moto Vertigo Dominium Fucsia S", "categoria": "motos", "descripcion": "Casco integral Vertigo talle S.", "link": "https://meli.la/1giSE9i"},
    {"nombre": "Kit Seguridad Auto 10 en 1", "categoria": "automotor", "descripcion": "Kit de seguridad para auto.", "link": "https://meli.la/23f2p69"},
    {"nombre": "Soporte TV Monitor de Pared 14 a 55 Pulgadas", "categoria": "tv", "descripcion": "Soporte de pared con brazo móvil.", "link": "https://meli.la/1r4iauF"},
    {"nombre": "Gamer Stick 4K M8 Lite +20000 Juegos", "categoria": "gaming", "descripcion": "Gamer Stick para TV con más de 20000 juegos.", "link": "https://meli.la/2psnRCH"},
    {"nombre": "Proyector Portátil 4K Bluetooth LED", "categoria": "tv", "descripcion": "Proyector portátil con Bluetooth, control y parlante.", "link": "https://meli.la/2nm17Cg"},
    {"nombre": "TV Stick Wi-Fi Smart TV Android HDMI", "categoria": "tv", "descripcion": "TV Stick para convertir el televisor en Smart TV.", "link": "https://meli.la/2Ur9uNo"},
    {"nombre": "Xiaomi Redmi Buds 6 Play Negro", "categoria": "auriculares", "descripcion": "Auriculares Xiaomi Redmi Buds 6 Play.", "link": "https://meli.la/1biaNuT"},
    {"nombre": "JBL Tune 720BT Negro", "categoria": "auriculares", "descripcion": "Auriculares JBL inalámbricos Bluetooth.", "link": "https://meli.la/1GZzaQH"},
    {"nombre": "Samsung Galaxy Tab A11 8.7 4GB 64GB Gris", "categoria": "tablets", "descripcion": "Tablet Samsung Galaxy Tab A11 Android.", "link": "https://meli.la/258QAWE"},
    {"nombre": "Mochila Viaje Carry On USB Impermeable Crema", "categoria": "mochilas", "descripcion": "Mochila de viaje con compartimientos y USB.", "link": "https://meli.la/2fmVJVn"},
    {"nombre": "Mochila Viaje Carry On para Avión Waggs Verde Oscuro", "categoria": "mochilas", "descripcion": "Mochila de viaje porta notebook.", "link": "https://meli.la/2x4YvfV"},
]

access_token = None
code_verifier = None


def crear_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def pagina_base(contenido, titulo="MarketRZ"):
    return f'''<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{html.escape(titulo)}</title><style>
:root{{--azul:#3483fa;--azul2:#1257b8;--fondo:#f5f7fa;--texto:#172033;--muted:#657184;--borde:#e2e8f0;--blanco:#fff;--naranja:#ff9d3d}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;font-family:Inter,Arial,Helvetica,sans-serif;background:var(--fondo);color:var(--texto)}}a{{color:inherit}}
.header{{background:linear-gradient(135deg,#3483fa 0%,#1257b8 100%);color:#fff;position:sticky;top:0;z-index:20;box-shadow:0 5px 22px #123b7328}}.header-inner{{max-width:1180px;margin:auto;padding:11px 24px;display:flex;align-items:center;gap:28px}}.logo{{display:flex;align-items:center;text-decoration:none}}.logo img{{width:168px;height:52px;object-fit:contain;background:#fff;border-radius:13px;padding:4px 8px;box-shadow:0 4px 14px #001d4a26}}.nav{{display:flex;gap:8px;margin-left:auto;font-size:14px}}.nav a{{text-decoration:none;padding:10px 13px;border-radius:10px;opacity:.96}}.nav a:hover{{background:#ffffff1c}}
.main{{max-width:1180px;margin:0 auto;padding:30px 24px 60px}}.hero{{position:relative;overflow:hidden;background:linear-gradient(135deg,#ffffff 0%,#edf5ff 100%);border:1px solid var(--borde);border-radius:26px;padding:42px;margin-bottom:30px;box-shadow:0 12px 36px #163b6810}}.hero:after{{content:"";position:absolute;width:250px;height:250px;border-radius:50%;background:#3483fa10;right:-90px;top:-100px}}.hero-brand{{display:flex;align-items:center;gap:15px;margin-bottom:24px;position:relative;z-index:1}}.hero-brand img{{width:150px;height:55px;object-fit:contain;border-radius:12px;background:#fff;padding:3px 8px;box-shadow:0 5px 18px #183d6a14}}.hero-brand-copy strong{{display:block;font-size:17px}}.hero-brand-copy span{{display:block;color:var(--muted);font-size:14px;margin-top:4px}}.hero h1{{position:relative;z-index:1;margin:0 0 12px;font-size:42px;line-height:1.12;letter-spacing:-.7px;max-width:780px}}.hero>p{{position:relative;z-index:1;margin:0 0 25px;color:var(--muted);font-size:17px;max-width:700px}}.search{{position:relative;z-index:2;display:flex;gap:10px;width:100%;max-width:900px}}.search input{{flex:1;min-width:0;padding:16px 18px;border:1px solid #cfd8e3;background:#fff;border-radius:13px;font-size:16px;outline:none;box-shadow:0 3px 12px #173b6810}}.search input:focus{{border-color:var(--azul);box-shadow:0 0 0 4px #3483fa1c}}.btn{{display:inline-flex;align-items:center;justify-content:center;padding:14px 20px;border:0;border-radius:12px;background:var(--azul);color:#fff;text-decoration:none;font-weight:700;cursor:pointer;transition:.18s transform,.18s background}}.btn:hover{{background:var(--azul2);transform:translateY(-1px)}}
.section-title{{display:flex;align-items:center;justify-content:space-between;margin:32px 0 14px}}.section-title h2{{margin:0;font-size:23px;letter-spacing:-.2px}}.section-title a{{color:var(--azul2);font-weight:700;text-decoration:none;font-size:14px}}.categories{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}}.category{{background:#fff;border:1px solid var(--borde);border-radius:14px;padding:13px 12px;text-decoration:none;font-size:14px;font-weight:600;display:flex;align-items:center;justify-content:center;gap:7px;transition:.18s;box-shadow:0 3px 10px #183d6a08}}.category:hover{{border-color:#a9c9f5;color:var(--azul2);transform:translateY(-2px)}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:17px}}.card{{background:#fff;border:1px solid var(--borde);border-radius:18px;padding:18px;display:flex;flex-direction:column;min-height:255px;box-shadow:0 6px 18px #183d6a0b;transition:.18s}}.card:hover{{transform:translateY(-3px);box-shadow:0 12px 26px #183d6a14}}.card .icon{{width:50px;height:50px;display:grid;place-items:center;border-radius:14px;background:#edf5ff;font-size:25px;margin-bottom:15px}}.card h3{{margin:0 0 8px;font-size:16px;line-height:1.35}}.card p{{margin:0 0 14px;color:var(--muted);font-size:14px;line-height:1.45}}.tag{{color:var(--azul2);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.6px;margin-bottom:7px}}.card .btn{{margin-top:auto;width:100%;padding:11px 14px;font-size:14px}}.footer{{text-align:center;color:#7b8797;font-size:13px;padding:28px 20px 38px}}.empty{{background:#fff;border:1px solid var(--borde);border-radius:18px;padding:38px;text-align:center;box-shadow:0 8px 24px #183d6a0b}}
@media(max-width:1050px){{.categories{{grid-template-columns:repeat(4,minmax(0,1fr))}}.grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}}}
@media(max-width:760px){{.header-inner{{padding:9px 14px}}.logo img{{width:145px;height:48px}}.nav{{display:none}}.main{{padding:18px 12px 40px}}.hero{{padding:25px 18px;border-radius:20px}}.hero-brand img{{width:132px;height:50px}}.hero h1{{font-size:30px}}.hero>p{{font-size:15px}}.search{{flex-direction:column}}.search input,.search .btn{{width:100%}}.categories{{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}}.category{{padding:12px 8px}}.grid{{grid-template-columns:1fr;gap:12px}}.card{{min-height:0;padding:16px}}.section-title h2{{font-size:20px}}}}
</style></head><body><header class="header"><div class="header-inner"><a class="logo" href="/"><img src="/static/logo-marketrz.svg" alt="MarketRZ"></a><nav class="nav"><a href="/">Inicio</a><a href="/buscar">Productos</a><a href="/login">Conectar Mercado Libre</a></nav></div></header><main class="main">{contenido}</main><footer class="footer">MarketRZ · Tecnología, productos y oportunidades</footer></body></html>'''


def icono_categoria(categoria):
    return {"celulares":"📱","auriculares":"🎧","smartwatch":"⌚","wifi":"📶","electrodomésticos":"🏠","automotor":"🚗","motos":"🏍️","tv":"📺","gaming":"🎮","tablets":"💻","mochilas":"🎒"}.get(categoria,"🛍️")


def tarjetas_productos(resultados):
    tarjetas = ""
    for p in resultados:
        nombre = html.escape(p["nombre"])
        categoria = html.escape(p["categoria"])
        descripcion = html.escape(p["descripcion"])
        link = html.escape(p["link"], quote=True)
        tarjetas += f'<article class="card"><div class="icon">{icono_categoria(p["categoria"])}</div><div class="tag">{categoria}</div><h3>{nombre}</h3><p>{descripcion}</p><a class="btn" href="{link}" target="_blank" rel="noopener noreferrer">Ver producto</a></article>'
    return tarjetas


@app.route("/")
def inicio():
    categorias = sorted(set(p["categoria"] for p in PRODUCTOS))
    botones = "".join(f'<a class="category" href="/buscar?q={html.escape(c, quote=True)}">{icono_categoria(c)} <span>{html.escape(c.title())}</span></a>' for c in categorias)
    contenido = f'''<section class="hero">
<div class="hero-brand"><img src="/static/logo-marketrz.svg" alt="MarketRZ"><div class="hero-brand-copy"><strong>MarketRZ</strong><span>Tecnología, productos y oportunidades</span></div></div>
<h1>Encontrá tu próximo producto en MarketRZ</h1>
<p>Explorá productos recomendados, descubrí nuevas opciones y accedé directamente a Mercado Libre.</p>
<form class="search" action="/buscar" method="get"><input name="q" placeholder="¿Qué producto buscás?" autocomplete="off"><button class="btn" type="submit">🔎 Buscar</button></form>
</section>
<div class="section-title"><h2>Explorá por categoría</h2></div>
<div class="categories">{botones}</div>
<div class="section-title"><h2>Productos destacados</h2><a href="/buscar">Ver todos →</a></div>
<div class="grid">{tarjetas_productos(PRODUCTOS[:8])}</div>'''
    return pagina_base(contenido)


@app.route("/login")
def login():
    global code_verifier
    if not CLIENT_ID:
        return pagina_base('<div class="empty"><h2>❌ Falta MELI_CLIENT_ID</h2><p>Revisá las variables de entorno de Render.</p></div>', "Conectar Mercado Libre")
    if not CLIENT_SECRET:
        return pagina_base('<div class="empty"><h2>❌ Falta MELI_CLIENT_SECRET</h2><p>Revisá las variables de entorno de Render.</p></div>', "Conectar Mercado Libre")
    code_verifier = secrets.token_urlsafe(64)
    challenge = crear_code_challenge(code_verifier)
    authorization_url = ("https://auth.mercadolibre.com.ar/authorization?response_type=code" f"&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}" f"&code_challenge={challenge}&code_challenge_method=S256")
    contenido = f'<section class="hero"><h1>🔐 Conectar Mercado Libre</h1><p>Autorizá MarketRZ para continuar con la integración.</p><a class="btn" href="{html.escape(authorization_url, quote=True)}">Continuar con Mercado Libre</a></section><script>window.location.href={authorization_url!r};</script>'
    return pagina_base(contenido, "Conectar Mercado Libre")


@app.route("/callback")
def callback():
    global access_token
    code = request.args.get("code")
    error = request.args.get("error")
    if error:
        desc = html.escape(request.args.get("error_description", ""))
        return pagina_base(f'<div class="empty"><h2>❌ Mercado Libre rechazó la autorización</h2><p>Error: {html.escape(error)}</p><pre>{desc}</pre><a class="btn" href="/login">Intentar nuevamente</a></div>', "Error de autorización")
    if not code:
        return pagina_base('<div class="empty"><h2>❌ No se recibió el código</h2><a class="btn" href="/login">Intentar nuevamente</a></div>', "Error de autorización")
    if not CLIENT_ID or not CLIENT_SECRET or not code_verifier:
        return pagina_base('<div class="empty"><h2>❌ Falta configuración de OAuth/PKCE</h2><a class="btn" href="/login">Intentar nuevamente</a></div>', "Error de configuración")
    try:
        response = requests.post("https://api.mercadolibre.com/oauth/token", data={"grant_type":"authorization_code","client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,"code":code,"redirect_uri":REDIRECT_URI,"code_verifier":code_verifier}, timeout=15)
    except requests.RequestException as exc:
        return pagina_base(f'<div class="empty"><h2>❌ Error de conexión</h2><pre>{html.escape(str(exc))}</pre></div>', "Error de conexión")
    if response.status_code != 200:
        return pagina_base(f'<div class="empty"><h2>❌ Error al obtener Access Token</h2><p>HTTP: {response.status_code}</p><pre>{html.escape(response.text)}</pre><a class="btn" href="/login">Intentar nuevamente</a></div>', "Error de token")
    try:
        token_response = response.json()
    except ValueError:
        return pagina_base('<div class="empty"><h2>❌ Mercado Libre devolvió una respuesta inválida</h2></div>', "Error de token")
    access_token = token_response.get("access_token")
    if not access_token:
        return pagina_base('<div class="empty"><h2>❌ No se recibió Access Token</h2></div>', "Error de token")
    return pagina_base('<section class="hero"><h1>✅ Mercado Libre conectado</h1><p>La autorización fue recibida correctamente.</p><a class="btn" href="/">Volver a MarketRZ</a></section>', "Mercado Libre conectado")


@app.route("/buscar")
def buscar():
    consulta = request.args.get("q", "").strip().lower()
    if consulta:
        resultados = [p for p in PRODUCTOS if consulta in p["nombre"].lower() or consulta in p["categoria"].lower() or consulta in p["descripcion"].lower()]
    else:
        resultados = PRODUCTOS
    if not resultados:
        contenido = '<div class="empty"><h2>😕 No encontramos ese producto.</h2><p>Probá con otra palabra o explorá las categorías.</p><a class="btn" href="/">Volver al inicio</a></div>'
        return pagina_base(contenido, "Sin resultados")
    titulo = f'Resultados para “{html.escape(consulta)}”' if consulta else "Todos los productos"
    contenido = f'<section class="hero"><h1>{titulo}</h1><p>{len(resultados)} producto(s) disponible(s).</p><form class="search" action="/buscar" method="get"><input name="q" value="{html.escape(consulta)}" placeholder="Buscar producto"><button class="btn" type="submit">🔎 Buscar</button></form></section><div class="grid">{tarjetas_productos(resultados)}</div>'
    return pagina_base(contenido, "Productos MarketRZ")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
