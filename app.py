from flask import Flask, request, jsonify
import os

# --- APP CONFIG ---
app = Flask(__name__) # Corrigido para __name__ com dois sublinhados

# --- CONFIG (Render ENV) ---
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "").strip()
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "").strip()

# URL de redirecionamento OAUTH
OAUTH_REDIRECT_URI = (
    os.getenv("OAUTH_REDIRECT_URI", "").strip()
    or os.getenv("FACEBOOK_REDIRECT_URI", "").strip()
    or "https://tec9-marketing-bot.onrender.com"
)

# Token de Verificação do Webhook (CUIDADO: Deve ser igual ao da Meta)
VERIFY_TOKEN = (
    os.getenv("VERIFY_TOKEN", "").strip()
    or os.getenv("META_VERIFY_TOKEN", "").strip()
)

DEFAULT_SCOPE = "pages_show_list,pages_manage_metadata"
OAUTH_SCOPE = os.getenv("OAUTH_SCOPE", DEFAULT_SCOPE).strip()

# --- ROTAS ---

# 1. Rota Inicial (Para saber se o bot está vivo)
@app.route("/")
def home():
    return "Tec bot rodando no Render ✅", 200

# 2. Rota do Webhook (A QUE A META PRECISA PARA VALIDAR)
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Validação do Facebook (Método GET)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            print("VERIFICATION_FAILED")
            return "Token de verificação inválido", 403

    # Recebimento de Mensagens (Método POST)
    if request.method == "POST":
        data = request.json
        print("Evento recebido:", data)
        return "EVENT_RECEIVED", 200

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
