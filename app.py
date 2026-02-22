from flask import Flask

app = Flask(__name__)

@app.get("/")
def home():
    return "Tec9 bot rodando no Render ✅"

if __name__ == "__main__":
    app.run()
