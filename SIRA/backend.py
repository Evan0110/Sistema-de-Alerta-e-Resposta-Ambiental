"""API REST local do SIRA (Flask)."""
from datetime import datetime
import re
from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest
import database

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

RISK_TYPES = {"Enchente", "Deslizamento", "Queimada", "Seca", "Qualidade do Ar", "Contaminação de Água"}
SEVERITIES = {"Emergência", "Alerta", "Atenção"}
ROLES = {"Cidadão / Morador", "Agente de Defesa Civil", "Estudante / Pesquisador", "Gestor Público"}
ALERT_FIELDS = ("title", "risk_type", "severity", "location", "lat", "lng", "issuer", "description", "instructions", "date_time")

class ValidationError(ValueError):
    pass


def json_body():
    if not request.is_json:
        raise ValidationError("Envie o conteúdo como JSON (Content-Type: application/json).")
    try:
        data = request.get_json(silent=False)
    except BadRequest as exc:
        raise ValidationError("JSON inválido.") from exc
    if not isinstance(data, dict):
        raise ValidationError("O corpo da requisição deve ser um objeto JSON.")
    return data


def required_text(data, key, label=None, max_len=2000):
    value = data.get(key)
    label = label or key
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"O campo '{label}' é obrigatório e deve ser texto.")
    value = value.strip()
    if len(value) > max_len:
        raise ValidationError(f"O campo '{label}' excede o limite de {max_len} caracteres.")
    return value


def validate_alert(data):
    result = {key: data.get(key) for key in ALERT_FIELDS}
    for key in ("title", "risk_type", "severity", "location", "issuer", "description", "instructions", "date_time"):
        result[key] = required_text(data, key, max_len=2000 if key in ("description", "instructions") else 200)
    if result["risk_type"] not in RISK_TYPES:
        raise ValidationError("Tipo de risco inválido.")
    if result["severity"] not in SEVERITIES:
        raise ValidationError("Severidade inválida.")
    for key, low, high, label in (("lat", -90, 90, "latitude"), ("lng", -180, 180, "longitude")):
        value = data.get(key)
        if isinstance(value, bool):
            raise ValidationError(f"{label.capitalize()} deve ser numérica.")
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValidationError(f"{label.capitalize()} deve ser numérica.")
        if not low <= value <= high:
            raise ValidationError(f"{label.capitalize()} deve estar entre {low} e {high}.")
        result[key] = value
    # Aceita os dois formatos usados na interface, mas armazena um formato estável.
    date_value = result["date_time"]
    parsed = None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(date_value, fmt)
            break
        except ValueError:
            pass
    if parsed is None:
        raise ValidationError("Data/hora inválida. Use AAAA-MM-DD HH:MM.")
    result["date_time"] = parsed.strftime("%Y-%m-%d %H:%M")
    return result


def handle_validation(func):
    """Transforma erros de validação em respostas 400 claras."""
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as exc:
            return jsonify({"error": str(exc)}), 400
    return wrapper

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "SIRA API"})

@app.get("/api/alerts")
@handle_validation
def get_alerts():
    risk = request.args.get("risk_type", "Todos")
    severity = request.args.get("severity", "Todas")
    if risk not in RISK_TYPES | {"Todos"}:
        raise ValidationError("Filtro de tipo de risco inválido.")
    if severity not in SEVERITIES | {"Todas"}:
        raise ValidationError("Filtro de severidade inválido.")
    return jsonify(database.list_alerts(risk, severity))

@app.post("/api/alerts")
@handle_validation
def post_alert():
    data = validate_alert(json_body())
    created = database.insert_alert(data)
    return jsonify(created), 201

@app.get("/api/indicators")
def indicators():
    return jsonify(database.get_indicators())

@app.post("/api/extension/register")
@handle_validation
def register_extension():
    data = json_body()
    participant = {
        "name": required_text(data, "name", "nome", 120),
        "email": required_text(data, "email", "e-mail", 254).lower(),
        "organization": required_text(data, "organization", "instituição/comunidade", 200),
        "role": required_text(data, "role", "perfil", 80),
    }
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", participant["email"]):
        raise ValidationError("Informe um endereço de e-mail válido.")
    if participant["role"] not in ROLES:
        raise ValidationError("Perfil de agente inválido.")
    try:
        participant_id = database.register_participant(participant)
    except Exception as exc:
        # A mensagem externa não revela detalhes internos do banco.
        if "UNIQUE constraint failed" in str(exc):
            return jsonify({"error": "Este e-mail já está cadastrado."}), 409
        app.logger.exception("Falha ao registrar participante")
        return jsonify({"error": "Não foi possível registrar a inscrição."}), 500
    return jsonify({"message": "Inscrição registrada.", "id": participant_id}), 201

@app.post("/api/extension/feedback")
@handle_validation
def extension_feedback():
    data = json_body()
    feedback = {
        "participant_name": required_text(data, "participant_name", "nome", 120),
        "usability_rating": data.get("usability_rating"),
        "clarity_rating": data.get("clarity_rating"),
        "comments": data.get("comments", ""),
    }
    for key in ("usability_rating", "clarity_rating"):
        value = feedback[key]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValidationError(f"'{key}' deve ser um número inteiro entre 1 e 5.")
    if not isinstance(feedback["comments"], str):
        raise ValidationError("O campo 'comments' deve ser texto.")
    feedback["comments"] = feedback["comments"].strip()[:2000]
    feedback_id = database.insert_feedback(feedback)
    return jsonify({"message": "Feedback registrado.", "id": feedback_id}), 201

@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Rota não encontrada."}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error("Erro interno: %s", error)
    return jsonify({"error": "Erro interno do servidor."}), 500

if __name__ == "__main__":
    database.init_db()
    # Protótipo local: não exponha esta API à internet sem autenticação e HTTPS.
    app.run(host="127.0.0.1", port=5000, debug=False)
