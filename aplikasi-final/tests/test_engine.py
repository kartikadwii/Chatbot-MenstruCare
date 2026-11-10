import pytest

from chatbot.engine import ChatbotEngine, load_themes, preprocess


@pytest.fixture
def engine():
    themes = load_themes("themes")
    return ChatbotEngine(themes["menstrucare"])


def test_preprocess():
    hasil = preprocess("Apa itu MENSTRUASI?")
    assert isinstance(hasil, list)
    assert len(hasil) > 0


def test_preprocess_lowercase():
    hasil = preprocess("HALO MENSTRUCARE")
    assert all(token == token.lower() for token in hasil)


def test_salam_dikenali(engine):
    result = engine.reply("Halo")
    assert result["intent"] == "salam"


def test_pengertian_menstruasi(engine):
    result = engine.reply("Apa itu menstruasi?")
    assert result["intent"] == "pengertian_menstruasi"


def test_siklus_menstruasi(engine):
    result = engine.reply("Berapa hari siklus menstruasi normal?")
    assert result["intent"] == "siklus_menstruasi"


def test_lama_menstruasi(engine):
    result = engine.reply("Berapa lama menstruasi berlangsung?")
    assert result["intent"] == "lama_menstruasi"


def test_nyeri_haid(engine):
    result = engine.reply("Bagaimana cara mengatasi nyeri menstruasi?")
    assert result["intent"] == "nyeri_haid"


def test_pms(engine):
    result = engine.reply("Apa itu PMS?")
    assert result["intent"] == "pms"


def test_telat_haid(engine):
    result = engine.reply("Mengapa menstruasi saya terlambat?")
    assert result["intent"] == "telat_haid"


def test_warna_darah_haid(engine):
    result = engine.reply("Mengapa darah menstruasi berwarna cokelat?")
    assert result["intent"] == "warna_darah_haid"


def test_kebersihan_menstruasi(engine):
    result = engine.reply("Bagaimana menjaga kebersihan saat haid?")
    assert result["intent"] == "kebersihan_menstruasi"


def test_makanan_saat_haid(engine):
    result = engine.reply("Makanan apa yang baik saat menstruasi?")
    assert result["intent"] == "makanan_saat_haid"


def test_olahraga_saat_haid(engine):
    result = engine.reply("Bolehkah olahraga saat menstruasi?")
    assert result["intent"] == "olahraga_saat_haid"


def test_gangguan_menstruasi(engine):
    result = engine.reply("Mengapa darah haid terlalu banyak?")
    assert result["intent"] == "gangguan_menstruasi"


def test_salam_penutup(engine):
    result = engine.reply("Terima kasih")
    assert result["intent"] == "salam_penutup"


def test_reply_memiliki_format(engine):
    result = engine.reply("Halo")

    assert "reply" in result
    assert "intent" in result
    assert "score" in result


def test_reply_tidak_kosong(engine):
    result = engine.reply("Halo")

    assert isinstance(result["reply"], str)
    assert len(result["reply"]) > 0


def test_get_bot_info(engine):
    info = engine.get_bot_info()

    assert isinstance(info, dict)
    assert info["id"] == "menstrucare"


def test_get_greeting(engine):
    greeting = engine.get_greeting()

    assert isinstance(greeting, str)
    assert len(greeting) > 0


def test_get_suggestions(engine):
    suggestions = engine.get_suggestions()

    assert isinstance(suggestions, list)
    assert len(suggestions) > 0