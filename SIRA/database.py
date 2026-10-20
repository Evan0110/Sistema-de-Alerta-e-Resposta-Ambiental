"""Camada de persistência SQLite do SIRA.

O banco é criado em uma localização estável junto a este arquivo, não no
 diretório de trabalho do terminal. Os dados de demonstração são simulados.
"""
from pathlib import Path
import sqlite3
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sira_dados.db"

SEED_ALERTS = [
    ("Alagamento em área urbana (simulado)", "Enchente", "Alerta", "Campinas - SP", -22.9056, -47.0608,
     "SIRA — dado demonstrativo", "Registro fictício para demonstração do sistema.",
     "Consulte os canais oficiais da Defesa Civil. Em risco imediato, afaste-se da área alagada.", "2026-10-20 08:00"),
    ("Instabilidade em encosta (simulado)", "Deslizamento", "Atenção", "Ouro Preto - MG", -20.3856, -43.5035,
     "SIRA — dado demonstrativo", "Registro fictício para demonstração do sistema.",
     "Evite encostas com sinais de movimentação e acompanhe orientações oficiais.", "2026-10-19 14:30"),
    ("Foco de incêndio florestal (simulado)", "Queimada", "Emergência", "Brasília - DF", -15.7797, -47.9297,
     "SIRA — dado demonstrativo", "Registro fictício para demonstração do sistema.",
     "Afaste-se da fumaça e acione os serviços oficiais de emergência quando necessário.", "2026-10-18 16:10"),
    ("Estiagem prolongada (simulado)", "Seca", "Atenção", "Petrolina - PE", -9.3891, -40.5031,
     "SIRA — dado demonstrativo", "Registro fictício para demonstração do sistema.",
     "Use água de forma consciente e consulte comunicados oficiais de abastecimento.", "2026-10-17 09:00"),
    ("Índice de qualidade do ar (simulado)", "Qualidade do Ar", "Alerta", "São Paulo - SP", -23.5505, -46.6333,
     "SIRA — dado demonstrativo", "Registro fictício para demonstração do sistema.",
     "Confira as orientações dos órgãos de saúde e monitoramento ambiental locais.", "2026-10-16 12:15"),
    ("Suspeita de contaminação hídrica (simulado)", "Contaminação de Água", "Atenção", "Santos - SP", -23.9608, -46.3336,
     "SIRA — dado demonstrativo", "Registro fictício para demonstração do sistema.",
     "Não consuma água de origem suspeita sem orientação da autoridade sanitária competente.", "2026-10-15 10:45"),
]

@contextmanager
def get_connection():
    """Abre conexão com configuração de timeout e fecha mesmo em caso de erro."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                risk_type TEXT NOT NULL,
                severity TEXT NOT NULL CHECK (severity IN ('Emergência','Alerta','Atenção')),
                location TEXT NOT NULL,
                lat REAL NOT NULL CHECK (lat BETWEEN -90 AND 90),
                lng REAL NOT NULL CHECK (lng BETWEEN -180 AND 180),
                issuer TEXT NOT NULL,
                description TEXT NOT NULL,
                instructions TEXT NOT NULL,
                date_time TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS extension_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                organization TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS extension_feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_name TEXT NOT NULL,
                usability_rating INTEGER NOT NULL CHECK (usability_rating BETWEEN 1 AND 5),
                clarity_rating INTEGER NOT NULL CHECK (clarity_rating BETWEEN 1 AND 5),
                comments TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        count = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        if count == 0:
            conn.executemany("""INSERT INTO alerts
                (title, risk_type, severity, location, lat, lng, issuer, description, instructions, date_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", SEED_ALERTS)


def list_alerts(risk_type="Todos", severity="Todas"):
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []
    if risk_type and risk_type != "Todos":
        query += " AND risk_type = ?"
        params.append(risk_type)
    if severity and severity != "Todas":
        query += " AND severity = ?"
        params.append(severity)
    query += " ORDER BY date_time DESC, id DESC"
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def insert_alert(data):
    fields = ("title", "risk_type", "severity", "location", "lat", "lng", "issuer", "description", "instructions", "date_time")
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO alerts (title, risk_type, severity, location, lat, lng, issuer, description, instructions, date_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(data[k] for k in fields),
        )
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def register_participant(data):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO extension_participants (name, email, organization, role) VALUES (?, ?, ?, ?)",
            (data["name"], data["email"], data["organization"], data["role"]),
        )
        return cur.lastrowid


def insert_feedback(data):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO extension_feedbacks (participant_name, usability_rating, clarity_rating, comments) VALUES (?, ?, ?, ?)",
            (data["participant_name"], data["usability_rating"], data["clarity_rating"], data["comments"]),
        )
        return cur.lastrowid


def get_indicators():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        emergencies = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity = 'Emergência'").fetchone()[0]
        by_risk = [dict(r) for r in conn.execute("SELECT risk_type, COUNT(*) AS total FROM alerts GROUP BY risk_type ORDER BY total DESC, risk_type").fetchall()]
        by_severity = [dict(r) for r in conn.execute("SELECT severity, COUNT(*) AS total FROM alerts GROUP BY severity ORDER BY total DESC, severity").fetchall()]
    return {"total_alerts": total, "emergency_alerts": emergencies, "risk_types": len(by_risk), "by_risk": by_risk, "by_severity": by_severity}

if __name__ == "__main__":
    init_db()
    print(f"Banco inicializado em: {DB_PATH}")
