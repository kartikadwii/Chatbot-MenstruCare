import csv
from pathlib import Path

from chatbot.engine import load_themes, ChatbotEngine


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "evaluasi" / "menstrucare.csv"
THEMES_PATH = BASE_DIR / "themes"


def evaluate():
    themes = load_themes(THEMES_PATH)
    chatbot = ChatbotEngine(themes["menstrucare"])

    total = 0
    benar = 0
    hasil_evaluasi = []

    with open(CSV_PATH, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            intent_asli = row["intent"].strip()
            kalimat = row["kalimat"].strip()

            if not intent_asli or not kalimat:
                continue

            hasil = chatbot.reply(kalimat)

            intent_prediksi = hasil["intent"]
            skor = hasil["score"]

            status = intent_asli == intent_prediksi

            total += 1

            if status:
                benar += 1

            hasil_evaluasi.append({
                "kalimat": kalimat,
                "intent_asli": intent_asli,
                "intent_prediksi": intent_prediksi,
                "skor": skor,
                "status": status
            })

    akurasi = (benar / total * 100) if total else 0

    print("=" * 60)
    print("EVALUASI CHATBOT MENSTRUCARE")
    print("=" * 60)

    for nomor, item in enumerate(hasil_evaluasi, start=1):
        status = "BENAR" if item["status"] else "SALAH"

        print(f"\n{nomor}. {item['kalimat']}")
        print(f"   Intent Asli     : {item['intent_asli']}")
        print(f"   Intent Prediksi : {item['intent_prediksi']}")
        print(f"   Skor            : {item['skor']:.2f}")
        print(f"   Status          : {status}")

    print("\n" + "=" * 60)
    print(f"Total Data       : {total}")
    print(f"Prediksi Benar   : {benar}")
    print(f"Prediksi Salah   : {total - benar}")
    print(f"Akurasi          : {akurasi:.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    evaluate()