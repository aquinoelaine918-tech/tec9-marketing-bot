# ================= CONFIG =================

# Render ENV (obrigatórios)
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "").strip()
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "").strip()

# IMPORTANTE:
# Aceita tanto OAUTH_REDIRECT_URI quanto FACEBOOK_REDIRECT_URI
OAUTH_REDIRECT_URI = (
    os.getenv("OAUTH_REDIRECT_URI", "").strip()
    or os.getenv("FACEBOOK_REDIRECT_URI", "").strip()
    or "https://tec9-marketing-bot.onrender.com/auth/callback"
)

# 🔥 CORREÇÃO DO VERIFY TOKEN (ACEITA OS DOIS NOMES)
VERIFY_TOKEN = (
    os.getenv("VERIFY_TOKEN", "").strip()
    or os.getenv("META_VERIFY_TOKEN", "").strip()
).strip()

# Scopes configuráveis via env
DEFAULT_SCOPE = "pages_show_list,pages_manage_metadata"
OAUTH_SCOPE = os.getenv("OAUTH_SCOPE", DEFAULT_SCOPE).strip()
