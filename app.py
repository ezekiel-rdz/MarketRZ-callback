from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def inicio():
    return "MarketRZ está funcionando correctamente."

@app.route("/callback")
def callback():
    codigo = request.args.get("code")

    if codigo:
        return f"""
        <h1>MarketRZ</h1>
        <p>Autorización recibida correctamente.</p>
        <p>El código fue recibido por MarketRZ.</p>
        """

    return """
    <h1>MarketRZ</h1>
    <p>Callback funcionando correctamente.</p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
