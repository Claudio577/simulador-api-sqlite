from flask import Flask, jsonify, send_from_directory
import sqlite3, os

APP_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(APP_DIR, "higestor_mock.db")

app = Flask(__name__, static_folder="public")

def q(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(sql, params).fetchall()]
    con.close()
    return rows

@app.after_request
def no_cache(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    # Se for consumir a API de outro domínio, destrave CORS:
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

@app.get("/dump")
def dump():
    associates     = q("SELECT * FROM associates ORDER BY associate_id")
    events         = q("SELECT * FROM events ORDER BY event_id")
    invoices       = q("SELECT * FROM invoices ORDER BY invoice_id")
    payments       = q("SELECT * FROM payments ORDER BY payment_id")
    registrations  = q("SELECT * FROM registrations ORDER BY registration_id")
    monthly_rev    = q("SELECT * FROM monthly_revenue ORDER BY month")
    delinquency    = q("SELECT * FROM delinquency ORDER BY month")

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
    return {"ok": True}

if __name__ == "__main__":
    # Porta dinâmica para plataformas (Render/Heroku/etc.)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

