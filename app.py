from flask import Flask, jsonify, send_from_directory
import sqlite3, os, shutil

# --- Configuração do caminho do banco ----------------------------------------
APP_DIR = os.path.dirname(__file__)
BASE_DB = os.path.join(APP_DIR, "higestor_mock.db")           # .db no repositório (opcional)
DB_PATH = os.environ.get("DB_PATH", BASE_DB)                   # ex.: /tmp/higestor.db no Render

# Se estiver usando /tmp e ainda não existir um DB lá, copia o modelo do repo (se existir)
if DB_PATH.startswith("/tmp") and (not os.path.exists(DB_PATH)) and os.path.exists(BASE_DB):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    shutil.copyfile(BASE_DB, DB_PATH)

# --- App Flask ----------------------------------------------------------------
app = Flask(__name__, static_folder="public")

def q(sql, params=()):
    """Executa consulta e retorna lista de dicionários."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()
    return rows

@app.after_request
def no_cache(resp):
    # Evitar cache em endpoints de API e destravar CORS (para consumo de outros domínios)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "*"
    return resp

# --- Endpoints ----------------------------------------------------------------
@app.get("/dump")
def dump():
    # Se o DB não existir, retorna erro amigável
    if not os.path.exists(DB_PATH):
        return jsonify({
            "error": "database_not_found",
            "message": "O arquivo do banco não foi encontrado.",
            "db_path": DB_PATH
        }), 503

    try:
        associates     = q("SELECT * FROM associates ORDER BY associate_id")
        events         = q("SELECT * FROM events ORDER BY event_id")
        invoices       = q("SELECT * FROM invoices ORDER BY invoice_id")
        payments       = q("SELECT * FROM payments ORDER BY payment_id")
        registrations  = q("SELECT * FROM registrations ORDER BY registration_id")
        monthly_rev    = q("SELECT * FROM monthly_revenue ORDER BY month")
        delinquency    = q("SELECT * FROM delinquency ORDER BY month")
    except sqlite3.Error as e:
        return jsonify({
            "error": "query_failed",
            "message": str(e),
            "db_path": DB_PATH
        }), 500

    data = {
        "associates": associates,
        "events": events,
        "invoices": invoices,
        "payments": payments,
        "registrations": registrations,
        "reports": {
            "monthly_revenue": monthly_rev,
            "delinquency": delinquency
        }
    }
    meta = {
        "source": "sqlite-mock",
        "db_path": DB_PATH,
        "totals": {
            "associates": len(associates),
            "events": len(events),
            "invoices": len(invoices),
            "payments": len(payments),
            "registrations": len(registrations)
        }
    }
    return jsonify({"meta": meta, "data": data})

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "db_path": DB_PATH,
        "db_exists": os.path.exists(DB_PATH)
    }

# --- Main ---------------------------------------------------------------------
if __name__ == "__main__":
    # Porta dinâmica para plataformas (Render/Heroku/etc.)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
