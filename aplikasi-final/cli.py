from chatbot.engine import load_themes, ChatbotEngine

def main():
    themes = load_themes("themes")
    theme = themes["menstrucare"]

    chatbot = ChatbotEngine(theme)

    print("=" * 45)
    print("🌸 MENSTRUCARE - CHATBOT EDUKASI MENSTRUASI")
    print("=" * 45)
    print(chatbot.get_greeting())
    print("Ketik 'keluar' untuk mengakhiri percakapan.")
    print("-" * 45)

    while True:
        pesan = input("Kamu: ").strip()

        if pesan.lower() in ["keluar", "exit", "quit"]:
            print("MenstruCare: Terima kasih sudah menggunakan MenstruCare. 🌸")
            break

        if not pesan:
            print("MenstruCare: Silakan masukkan pertanyaan terlebih dahulu.")
            continue

        hasil = chatbot.reply(pesan)

        print(f"MenstruCare: {hasil['reply']}")
        print(f"Intent: {hasil['intent']}")
        print(f"Skor: {hasil['score']:.2f}")
        print("-" * 45)


if __name__ == "__main__":
    main()