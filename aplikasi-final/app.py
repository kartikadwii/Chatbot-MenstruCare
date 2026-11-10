import os
import uuid
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session
)

from chatbot.engine import load_themes, ChatbotEngine
from chatbot.database import ChatHistory

# Menentukan lokasi folder utama aplikasi
BASE_DIR = Path(__file__).resolve().parent

# Menentukan lokasi folder tema chatbot
THEMES_DIR = BASE_DIR / "themes"

# Menentukan lokasi database SQLite
DATABASE_PATH = BASE_DIR / "menstrucare.db"

# Membuat aplikasi Flask
app = Flask(__name__)

# Mengatur secret key untuk mengelola session pengguna
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "menstrucare-secret-key-development"
)

# Memuat seluruh tema chatbot dari folder themes
THEMES = load_themes(THEMES_DIR)

# Menentukan tema chatbot yang digunakan
DEFAULT_THEME = "menstrucare"

# Memastikan tema MenstruCare tersedia
if DEFAULT_THEME not in THEMES:
    raise RuntimeError("Tema MenstruCare tidak ditemukan.")

# Membuat engine chatbot berdasarkan tema yang tersedia
ENGINES = {
    theme_id: ChatbotEngine(theme)
    for theme_id, theme in THEMES.items()
}

# Menghubungkan aplikasi dengan database riwayat percakapan
chat_history = ChatHistory(DATABASE_PATH)

# Membuat ID session unik untuk setiap pengguna
def get_session_id():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    return session["session_id"]

# Menampilkan halaman utama MenstruCare
@app.route("/")
def index():
    theme = THEMES[DEFAULT_THEME]

    return render_template(
        "index.html",
        theme=theme
    )

# Menampilkan halaman chatbot
@app.route("/chat")
def chat():
    theme = THEMES[DEFAULT_THEME]

    return render_template(
        "chat.html",
        theme=theme
    )

# API untuk menerima dan memproses pesan pengguna
@app.route("/api/chat", methods=["POST"])
def api_chat():
    # Mengambil pesan dari request JSON
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    # Memeriksa apakah pesan kosong
    if not message:
        return jsonify({
            "success": False,
            "error": "Pesan tidak boleh kosong."
        }), 400

    # Membatasi panjang pesan maksimal 1000 karakter
    if len(message) > 1000:
        return jsonify({
            "success": False,
            "error": "Pesan terlalu panjang. Maksimal 1000 karakter."
        }), 400

    # Mengambil ID session dan engine chatbot
    session_id = get_session_id()
    engine = ENGINES[DEFAULT_THEME]

    # Memproses pesan menggunakan mesin chatbot
    result = engine.reply(message)

    # Menyimpan pesan pengguna ke database
    chat_history.add(
        session_id=session_id,
        theme=DEFAULT_THEME,
        sender="user",
        text=message,
        intent=result["intent"],
        score=result["score"]
    )

    # Menyimpan jawaban chatbot ke database
    chat_history.add(
        session_id=session_id,
        theme=DEFAULT_THEME,
        sender="bot",
        text=result["reply"],
        intent=result["intent"],
        score=result["score"]
    )

    # Mengirimkan hasil jawaban chatbot dalam format JSON
    return jsonify({
        "success": True,
        "reply": result["reply"],
        "intent": result["intent"],
        "score": result["score"]
    })

# API untuk mengambil riwayat percakapan pengguna
@app.route("/api/history", methods=["GET"])
def api_history():
    # Mengambil ID session pengguna
    session_id = get_session_id()

    # Mengambil riwayat percakapan dari database
    history = chat_history.get(
        session_id=session_id,
        theme=DEFAULT_THEME
    )

    # Mengirimkan riwayat dalam format JSON
    return jsonify({
        "success": True,
        "history": history
    })

# API untuk menghapus riwayat percakapan pengguna
@app.route("/api/clear", methods=["POST"])
def api_clear():
    # Mengambil ID session pengguna
    session_id = get_session_id()

    # Menghapus riwayat berdasarkan session dan tema
    chat_history.clear(
        session_id=session_id,
        theme=DEFAULT_THEME
    )

    # Mengirimkan pesan bahwa riwayat berhasil dihapus
    return jsonify({
        "success": True,
        "message": "Riwayat percakapan berhasil dihapus."
    })

# Menampilkan halaman dashboard admin
@app.route("/laporan")
def admin():
    return render_template("laporan.html")

# API untuk mengambil statistik penggunaan chatbot
@app.route("/api/admin/stats", methods=["GET"])
def admin_stats():
    return jsonify({
        "success": True,

        # Mengambil ringkasan statistik percakapan
        "summary": chat_history.summary(DEFAULT_THEME),

        # Mengambil jumlah pertanyaan berdasarkan intent
        "intents": chat_history.stats(DEFAULT_THEME),

        # Mengambil pertanyaan yang belum dikenali chatbot
        "unknown_questions": chat_history.unknown_questions(
            DEFAULT_THEME
        )
    })

# Menangani halaman yang tidak ditemukan (404)
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

# Menjalankan aplikasi Flask
if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )