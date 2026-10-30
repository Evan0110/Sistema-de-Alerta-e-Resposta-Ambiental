"""Camada de persistência SQLite do SIRA.

O banco é criado em uma localização estável junto a este arquivo, não no
 diretório de trabalho do terminal. Os dados de demonstração são simulados.
"""
from pathlib import Path
import sqlite3
import os
from functools import lru_cache
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("SIRA_DB_PATH", str(BASE_DIR / "sira_dados.db")))


def configure_remote_storage(url, service_key):
    """Configura Supabase para a publicação web; sem configuração usa SQLite local."""
    global _supabase_config
    _supabase_config = (url.strip(), service_key.strip())
    _supabase_client.cache_clear()


_supabase_config = None


def _using_supabase():
    return bool(_supabase_config or (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY")))


def remote_storage_enabled():
    return _using_supabase()


@lru_cache(maxsize=1)
def _supabase_client():
    config = _supabase_config or (os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    if not config or not all(config):
        raise RuntimeError("Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY nos segredos do app.")
    from supabase import create_client
    return create_client(*config)

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
    if _using_supabase():
        client = _supabase_client()
        try:
            existing = client.table("alerts").select("id", count="exact").limit(1).execute()
            client.table("extension_participants").select("id", count="exact").limit(1).execute()
            client.table("extension_feedbacks").select("id", count="exact").limit(1).execute()
        except Exception as exc:
            print(f"SUPABASE_INIT_ERROR: {type(exc).__name__}: {exc!r}")
            raise RuntimeError(f"Erro Supabase ({type(exc).__name__}): {exc!r}") from exc
        if not existing.count:
            fields = ("title", "risk_type", "severity", "location", "lat", "lng", "issuer", "description", "instructions", "date_time")
            client.table("alerts").insert([dict(zip(fields, row)) for row in SEED_ALERTS]).execute()
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
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
                persona TEXT NOT NULL DEFAULT 'Público geral' CHECK (persona IN ('Operador', 'Público geral')),
                comments TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        # Migração compatível com bancos criados em versões anteriores.
        feedback_columns = {row[1] for row in conn.execute("PRAGMA table_info(extension_feedbacks)")}
        if "persona" not in feedback_columns:
            conn.execute("ALTER TABLE extension_feedbacks ADD COLUMN persona TEXT NOT NULL DEFAULT 'Público geral'")
        count = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        if count == 0:
            conn.executemany("""INSERT INTO alerts
                (title, risk_type, severity, location, lat, lng, issuer, description, instructions, date_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", SEED_ALERTS)


def list_alerts(risk_type="Todos", severity="Todas"):
    if _using_supabase():
        query = _supabase_client().table("alerts").select("*")
        if risk_type and risk_type != "Todos":
            query = query.eq("risk_type", risk_type)
        if severity and severity != "Todas":
            query = query.eq("severity", severity)
        response = query.order("date_time", desc=True).order("id", desc=True).execute()
        return response.data or []
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
    if _using_supabase():
        response = _supabase_client().table("alerts").insert(data).select().single().execute()
        return response.data
    fields = ("title", "risk_type", "severity", "location", "lat", "lng", "issuer", "description", "instructions", "date_time")
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO alerts (title, risk_type, severity, location, lat, lng, issuer, description, instructions, date_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(data[k] for k in fields),
        )
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)


def register_participant(data):
    if _using_supabase():
        response = _supabase_client().table("extension_participants").insert(data).select("id").single().execute()
        return response.data["id"]
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO extension_participants (name, email, organization, role) VALUES (?, ?, ?, ?)",
            (data["name"], data["email"], data["organization"], data["role"]),
        )
        return cur.lastrowid


def insert_feedback(data):
    if _using_supabase():
        response = _supabase_client().table("extension_feedbacks").insert(data).select("id").single().execute()
        return response.data["id"]
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO extension_feedbacks (participant_name, usability_rating, clarity_rating, persona, comments) VALUES (?, ?, ?, ?, ?)",
            (data["participant_name"], data["usability_rating"], data["clarity_rating"], data["persona"], data["comments"]),
        )
        return cur.lastrowid


def get_indicators():
    if _using_supabase():
        rows = list_alerts()
        total = len(rows)
        emergencies = sum(row["severity"] == "Emergência" for row in rows)
        risk_counts, severity_counts = {}, {}
        for row in rows:
            risk_counts[row["risk_type"]] = risk_counts.get(row["risk_type"], 0) + 1
            severity_counts[row["severity"]] = severity_counts.get(row["severity"], 0) + 1
        by_risk = [{"risk_type": key, "total": value} for key, value in sorted(risk_counts.items(), key=lambda item: (-item[1], item[0]))]
        by_severity = [{"severity": key, "total": value} for key, value in sorted(severity_counts.items(), key=lambda item: (-item[1], item[0]))]
        return {"total_alerts": total, "emergency_alerts": emergencies, "risk_types": len(by_risk), "by_risk": by_risk, "by_severity": by_severity}
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        emergencies = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity = 'Emergência'").fetchone()[0]
        by_risk = [dict(r) for r in conn.execute("SELECT risk_type, COUNT(*) AS total FROM alerts GROUP BY risk_type ORDER BY total DESC, risk_type").fetchall()]
        by_severity = [dict(r) for r in conn.execute("SELECT severity, COUNT(*) AS total FROM alerts GROUP BY severity ORDER BY total DESC, severity").fetchall()]
    return {"total_alerts": total, "emergency_alerts": emergencies, "risk_types": len(by_risk), "by_risk": by_risk, "by_severity": by_severity}

if __name__ == "__main__":
    init_db()
    print(f"Banco inicializado em: {DB_PATH}")
