"""
Penyimpanan riwayat percakapan MenstruCare menggunakan SQLite.
"""

import sqlite3
from pathlib import Path

# 1. SKEMA DATABASE
SKEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL,
    theme       TEXT    NOT NULL,
    sender      TEXT    NOT NULL CHECK (sender IN ('user', 'bot')),
    text        TEXT    NOT NULL,
    intent      TEXT,
    score       REAL,
    created_at  TIMESTAMP DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_session_theme
ON messages (session_id, theme);
"""

# 2. CLASS CHAT HISTORY
class ChatHistory:

    def __init__(self, db_path: str | Path):

        self.db_path = str(db_path)

        with self._connect() as conn:
            conn.executescript(SKEMA)

    # Koneksi database
    def _connect(self):

        conn = sqlite3.connect(self.db_path)

        conn.row_factory = sqlite3.Row

        return conn
    
    # Menambahkan pesan
    def add(
        self,
        session_id,
        theme,
        sender,
        text,
        intent=None,
        score=None
    ):

        if sender not in ("user", "bot"):
            raise ValueError("Sender harus berupa 'user' atau 'bot'.")

        if not text or not text.strip():
            raise ValueError("Pesan tidak boleh kosong.")

        sql = """
            INSERT INTO messages (
                session_id,
                theme,
                sender,
                text,
                intent,
                score
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """

        with self._connect() as conn:

            conn.execute(
                sql,
                (
                    session_id,
                    theme,
                    sender,
                    text,
                    intent,
                    score
                )
            )

    # Mengambil riwayat percakapan
    def get(self, session_id, theme, limit=50):

        limit = max(1, min(int(limit), 500))

        with self._connect() as conn:

            rows = conn.execute(
                """
                SELECT
                    sender,
                    text,
                    intent,
                    score,
                    created_at

                FROM messages

                WHERE session_id = ?
                AND theme = ?

                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, theme, limit)
            ).fetchall()

        return [
            dict(row)
            for row in reversed(rows)
        ]

    # Menghapus riwayat percakapan
    def clear(self, session_id, theme):

        with self._connect() as conn:

            conn.execute(
                """
                DELETE FROM messages

                WHERE session_id = ?
                AND theme = ?
                """,
                (session_id, theme)
            )

    # Statistik intent
    def stats(self, theme):

        """Menghitung jumlah pertanyaan pengguna per intent."""

        with self._connect() as conn:

            rows = conn.execute(
                """
                SELECT
                    COALESCE(intent, '(tidak dikenali)') AS intent,
                    COUNT(*) AS jumlah

                FROM messages

                WHERE theme = ?
                AND sender = 'user'

                GROUP BY intent

                ORDER BY jumlah DESC
                """,
                (theme,)
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # Pertanyaan yang tidak dikenali
    def unknown_questions(self, theme, limit=20):

        """Mengambil pertanyaan yang belum dikenali chatbot."""

        limit = max(1, min(int(limit), 500))

        with self._connect() as conn:

            rows = conn.execute(
                """
                SELECT
                    text,
                    score,
                    created_at

                FROM messages

                WHERE theme = ?
                AND sender = 'user'
                AND intent IS NULL

                ORDER BY id DESC
                LIMIT ?
                """,
                (theme, limit)
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # Ringkasan statistik admin
    def summary(self, theme):

        """Menghasilkan ringkasan penggunaan chatbot."""

        with self._connect() as conn:

            result = conn.execute(
                """
                SELECT

                    COUNT(*) AS total,

                    SUM(
                        CASE
                            WHEN intent IS NULL THEN 1
                            ELSE 0
                        END
                    ) AS gagal,

                    COUNT(DISTINCT session_id) AS sesi

                FROM messages

                WHERE theme = ?
                AND sender = 'user'
                """,
                (theme,)
            ).fetchone()

        total = result["total"] or 0

        gagal = result["gagal"] or 0

        sesi = result["sesi"] or 0

        persen_dikenali = (
            round(100 * (total - gagal) / total, 1)
            if total else 0.0
        )

        return {
            "total": total,
            "tidak_dikenali": gagal,
            "sesi": sesi,
            "persen_dikenali": persen_dikenali
        }