"""
Mesin chatbot berbasis aturan (rule-based) untuk MenstruCare.

Alur kerja:
1. Praproses:
   - Mengubah teks menjadi huruf kecil.
   - Menghapus tanda baca.
   - Menormalisasi bahasa tidak baku.
   - Menghapus stopword.

2. Pencocokan:
   - Menggunakan algoritma Jaccard.
   - Menggunakan Fuzzy Matching (SequenceMatcher).
   - Menggunakan perhitungan cakupan kata.

3. Keputusan:
   - Memilih intent dengan skor tertinggi.
   - Membandingkan skor dengan threshold.
   - Memberikan respons fallback jika tidak cocok.
"""

import json
import random
import re

from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# 1. NORMALISASI KATA TIDAK BAKU
NORMALISASI = {
    "gak": "tidak",
    "ga": "tidak",
    "nggak": "tidak",
    "enggak": "tidak",
    "tdk": "tidak",

    "gimana": "bagaimana",
    "gmn": "bagaimana",
    "bgmn": "bagaimana",

    "brp": "berapa",
    "berapakah": "berapa",

    "yg": "yang",
    "dgn": "dengan",
    "utk": "untuk",

    "sy": "saya",
    "aku": "saya",
    "gue": "saya",
    "gw": "saya",

    "haid": "menstruasi",
    "mens": "menstruasi",

    "sakit": "nyeri",
    "kram": "nyeri",

    "telat": "terlambat",
    "blm": "belum",

    "makasih": "terima kasih",
    "thanks": "terima kasih",
    "thx": "terima kasih",

    "hai": "halo",
    "hi": "halo",
    "hello": "halo",
    "hallo": "halo",

    "kak": "",
    "min": "",
    "dong": "",
    "sih": "",
    "nih": ""
}

# 2. STOPWORD BAHASA INDONESIA
STOPWORDS = {
    "yang", "di", "ke", "dari", "dan", "atau",
    "itu", "ini", "untuk", "dengan", "adalah",
    "saya", "mau", "ingin", "tolong", "bisa",
    "pada", "akan", "juga", "ada", "tentang",
    "mohon", "info", "informasi", "apakah",
    "kah", "ya"
}

# 3. BOBOT KEMIRIPAN
BOBOT_JACCARD = 0.4
BOBOT_FUZZY = 0.3
BOBOT_CAKUPAN = 0.3

# 4. STRUKTUR WAJIB FILE JSON
KUNCI_WAJIB_TEMA = [
    "id",
    "name",
    "bot_name",
    "avatar",
    "color",
    "description",
    "greeting",
    "suggestions",
    "fallback",
    "intents"
]

# 5. PRA-PROSES TEKS
def preprocess(teks: str) -> list[str]:

    """Membersihkan dan menormalisasi kalimat pengguna."""

    teks = teks.lower()

    teks = re.sub(r"[^a-z0-9\s]", " ", teks)

    tokens = []

    for kata in teks.split():

        kata = NORMALISASI.get(kata, kata)

        for k in kata.split():

            if k and k not in STOPWORDS:

                tokens.append(k)

    return tokens

# 6. MENGHITUNG KEMIRIPAN KALIMAT
def similarity(tokens_a: list[str], tokens_b: list[str]) -> float:

    """Menghitung skor kemiripan menggunakan tiga metode."""

    if not tokens_a or not tokens_b:
        return 0.0

    set_a = set(tokens_a)
    set_b = set(tokens_b)

    # Jaccard Similarity
    jaccard = len(set_a & set_b) / len(set_a | set_b)

    # Fuzzy Matching
    fuzzy = SequenceMatcher(
        None,
        " ".join(tokens_a),
        " ".join(tokens_b)
    ).ratio()

    # Cakupan kata
    cakupan = len(set_a & set_b) / len(set_b)

    skor = (
        BOBOT_JACCARD * jaccard
        + BOBOT_FUZZY * fuzzy
        + BOBOT_CAKUPAN * cakupan
    )

    return round(skor, 4)

# 7. VALIDASI KNOWLEDGE MAPPING
def validate_theme(theme: dict) -> list[str]:

    """Memeriksa kelengkapan struktur knowledge mapping."""

    masalah = [
        f"Kunci '{k}' tidak ditemukan."
        for k in KUNCI_WAJIB_TEMA
        if k not in theme
    ]

    if masalah:
        return masalah

    if not theme["fallback"]:
        masalah.append("Daftar fallback kosong.")

    if not theme["intents"]:
        masalah.append("Daftar intents kosong.")

    tags = set()
    pola_milik = {}

    for i, intent in enumerate(theme["intents"]):

        for k in ("tag", "patterns", "responses"):

            if k not in intent:
                masalah.append(
                    f"Intent ke-{i + 1}: kunci '{k}' tidak ditemukan."
                )

        tag = intent.get("tag", f"#{i + 1}")

        if tag in tags:
            masalah.append(
                f"Tag '{tag}' digunakan lebih dari sekali."
            )

        tags.add(tag)

        if not intent.get("patterns"):
            masalah.append(
                f"Intent '{tag}': patterns kosong."
            )

        if not intent.get("responses"):
            masalah.append(
                f"Intent '{tag}': responses kosong."
            )

        for pola in intent.get("patterns", []):

            kunci = " ".join(preprocess(pola))

            if not kunci:
                masalah.append(
                    f"Intent '{tag}': pola '{pola}' kosong setelah praproses."
                )

            elif kunci in pola_milik and pola_milik[kunci] != tag:

                masalah.append(
                    f"Pola '{pola}' ditemukan pada dua intent berbeda."
                )

            pola_milik.setdefault(kunci, tag)

    return masalah

# 8. MEMUAT KNOWLEDGE MAPPING
def load_themes(folder: str | Path) -> dict[str, dict]:

    """Memuat semua file JSON dalam folder themes."""

    themes = {}

    for path in sorted(Path(folder).glob("*.json")):

        with open(path, encoding="utf-8") as file:
            data = json.load(file)

        masalah = validate_theme(data)

        if masalah:

            raise ValueError(
                f"File tema {path.name} tidak valid:\n- "
                + "\n- ".join(masalah)
            )

        themes[data["id"]] = data

    return themes

# 9. CLASS CHATBOT ENGINE
class ChatbotEngine:

    """Mesin chatbot untuk satu knowledge mapping."""

    def __init__(self, theme: dict, threshold: float = 0.45):

        self.theme = theme
        self.threshold = threshold

        # Memproses pola sekali saat engine dibuat.
        self._patterns = [
            (intent["tag"], pola, preprocess(pola))

            for intent in theme["intents"]

            for pola in intent["patterns"]
        ]

        self._responses = {
            intent["tag"]: intent["responses"]

            for intent in theme["intents"]
        }

    # Mencari kandidat intent
    def explain(self, pesan: str, top: int = 3) -> list[dict]:

        """Menampilkan kandidat intent beserta skor kemiripan."""

        tokens = preprocess(pesan)

        terbaik = {}

        for tag, pola, pola_tokens in self._patterns:

            skor = similarity(tokens, pola_tokens)

            if tag not in terbaik or skor > terbaik[tag]["score"]:

                terbaik[tag] = {
                    "intent": tag,
                    "pattern": pola,
                    "score": skor
                }

        return sorted(
            terbaik.values(),
            key=lambda x: x["score"],
            reverse=True
        )[:top]

    # Klasifikasi intent
    def classify(self, pesan: str) -> tuple[str | None, float]:

        """Menentukan intent berdasarkan skor tertinggi."""

        kandidat = self.explain(pesan, top=1)

        if not kandidat:
            return None, 0.0

        best = kandidat[0]

        if best["score"] < self.threshold:
            return None, best["score"]

        return best["intent"], best["score"]

    # Placeholder dinamis
    def _isi_placeholder(self, teks: str) -> str:

        """Mengganti placeholder dinamis dalam respons."""

        now = datetime.now()

        return (
            teks
            .replace("{waktu}", now.strftime("%H:%M"))
            .replace("{tanggal}", now.strftime("%d-%m-%Y"))
            .replace("{nama_bot}", self.theme["bot_name"])
        )

    # Menghasilkan respons chatbot
    def reply(self, pesan: str) -> dict:

        """Memproses pesan dan menghasilkan jawaban chatbot."""

        if not pesan or not pesan.strip():

            return {
                "reply": "Pesannya masih kosong. Silakan ketik pertanyaanmu.",
                "intent": None,
                "score": 0.0
            }

        tag, skor = self.classify(pesan)

        if tag is None:

            teks = random.choice(
                self.theme["fallback"]
            )

        else:

            teks = random.choice(
                self._responses[tag]
            )

        return {
            "reply": self._isi_placeholder(teks),
            "intent": tag,
            "score": skor
        }

    # Informasi chatbot
    def get_bot_info(self) -> dict:

        return {
            "id": self.theme["id"],
            "name": self.theme["name"],
            "bot_name": self.theme["bot_name"],
            "avatar": self.theme["avatar"],
            "color": self.theme["color"],
            "description": self.theme["description"]
        }

    # Pesan sambutan
    def get_greeting(self) -> str:

        return self.theme["greeting"]

    # Rekomendasi pertanyaan
    def get_suggestions(self) -> list[str]:

        return self.theme["suggestions"]