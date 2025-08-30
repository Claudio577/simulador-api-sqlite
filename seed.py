# seed.py — popula o banco SQLite (higestor_mock.db) com dados fictícios
# Requisitos: Python 3.10+ (bibliotecas padrão)

import os
import sqlite3
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Configurações (via env vars ou defaults)
#   - DB_PATH: caminho do arquivo .db (ex.: /tmp/higestor.db no Render)
#   - SCHEMA_FILE: caminho do schema.sql
# ---------------------------------------------------------------------------
HERE = Path(__file__).parent
DB_PATH = Path(os.environ.get("DB_PATH", HERE / "higestor_mock.db"))
SCHEMA_FILE = Path(os.environ.get("SCHEMA_FILE", HERE / "schema.sql"))

random.seed(7)

# ------------------ helpers ------------------
def rand_date(start="2023-01-01", end="2025-08-01"):
    sd = datetime.fromisoformat(start)
    ed = datetime.fromisoformat(end)
    delta_days = (ed - sd).days
    return sd + timedelta(days=random.randrange(delta_days + 1))

def cpf_fake():
    nums = [random.randint(0, 9) for _ in range(9)]
    return f"{nums[0]}{nums[1]}{nums[2]}.{nums[3]}{nums[4]}{nums[5]}.{nums[6]}{nums[7]}{nums[8]}-**"

def boleto_number():
    return "".join(random.choices(string.digits, k=47))

def pix_txid():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=25))

# ------------------ main ------------------
def main():
    if not SCHEMA_FILE.exists():
        raise SystemExit(f"ERRO: schema.sql não encontrado em: {SCHEMA_FILE}")

    # Garante que a pasta do DB existe (útil quando DB_PATH está em /tmp/ ou subpastas)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON;")
    # PRAGMAs úteis para velocidade durante o seed (opcionais)
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")

    # Aplica/reaplica o schema
    con.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    cur = con.cursor()

    # limpa se já existir algo (ordem respeita FKs)
    for t in ["payments", "invoices", "registrations", "events", "associates", "monthly_revenue", "delinquency"]:
        cur.execute(f"DELETE FROM {t}")

    # -------- associates --------
    n_assoc = 50
    assoc_ids = [f"A{i:04d}" for i in range(1, n_assoc + 1)]
    plans = ["Básico", "Padrão", "Premium"]
    status_opts = ["ativo", "inadimplente", "suspenso"]

    for i, aid in enumerate(assoc_ids, 1):
        cur.execute(
            """
            INSERT INTO associates(associate_id, name, cpf_mask, join_date, status, plan, monthly_fee)
            VALUES (?,?,?,?,?,?,?)
            """,
            (
                aid,
                f"Associado {i}",
                cpf_fake(),
                rand_date("2022-01-01", "2025-06-01").date().isoformat(),
                random.choices(status_opts, weights=[75, 18, 7])[0],
                random.choices(plans, weights=[40, 40, 20])[0],
                float(random.choice([35.0, 49.9, 59.9, 79.9, 99.9])),
            ),
        )

    # -------- events --------
    n_events = 6
    event_ids = [f"E{i:03d}" for i in range(1, n_events + 1)]
    events_buf = []
    for i, eid in enumerate(event_ids, 1):
        start = rand_date("2024-01-01", "2025-11-01")
        end = start + timedelta(days=random.randint(1, 2))
        name = f"Evento {i} - Gestão e Arrecadação"
        price = float(random.choice([0, 20, 35, 49.9, 79.9, 120.0]))
        seats = int(random.choice([50, 100, 150, 200]))
        row = (eid, name, start.date().isoformat(), end.date().isoformat(), price, seats)
        events_buf.append(row)
        cur.execute(
            "INSERT INTO events(event_id, name, start_date, end_date, price, seats) VALUES (?,?,?,?,?,?)",
            row,
        )

    # -------- invoices & payments --------
    n_invoices = 220
    invoice_ids = [f"I{i:05d}" for i in range(1, n_invoices + 1)]
    status_invoice = ["aberto", "pago", "vencido", "cancelado"]
    payments_buf = []

    for iid in invoice_ids:
        assoc = random.choice(assoc_ids)
        issue = rand_date("2024-01-01", "2025-08-01")
        due = issue + timedelta(days=10 + random.randint(0, 9))
        amount = float(random.choice([39.9, 49.9, 59.9, 69.9, 79.9, 99.9, 149.9]))
        status = random.choices(status_invoice, weights=[22, 60, 12, 6])[0]

        pay_date = None
        if status == "pago":
            pay_date = issue + timedelta(days=random.randint(1, 34))
            method = random.choices(["boleto", "pix", "cartao"], weights=[55, 35, 10])[0]
            conciliated = 1 if random.random() < 0.92 else 0
            gateway_txid = pix_txid() if method == "pix" else None
            payments_buf.append(
                (
                    f"P{iid[1:]}",  # casa com o número da fatura
                    iid,
                    pay_date.date().isoformat(),
                    method,
                    amount,
                    conciliated,
                    gateway_txid,
                )
            )

        cur.execute(
            """
            INSERT INTO invoices(invoice_id, associate_id, issue_date, due_date, amount, status, payment_date, boleto_number)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                iid,
                assoc,
                issue.date().isoformat(),
                due.date().isoformat(),
                amount,
                status,
                pay_date.date().isoformat() if pay_date else None,
                boleto_number(),
            ),
        )

    if payments_buf:
        cur.executemany(
            "INSERT INTO payments(payment_id, invoice_id, date, method, amount, conciliated, gateway_txid) "
            "VALUES (?,?,?,?,?,?,?)",
            payments_buf,
        )

    # -------- registrations --------
    regs_buf = []
    for (eid, _name, sdate, _edate, price, seats) in events_buf:
        k = random.randint(int(seats * 0.2), int(seats * 0.7))
        chosen = random.sample(assoc_ids, k=min(k, len(assoc_ids)))
        for a in chosen:
            paid = 1 if (price == 0 or random.random() < 0.85) else 0
            regs_buf.append((f"R{len(regs_buf)+1:05d}", eid, a, sdate, paid))
    if regs_buf:
        cur.executemany(
            "INSERT INTO registrations(registration_id, event_id, associate_id, date, paid) VALUES (?,?,?,?,?)",
            regs_buf,
        )

    # -------- reports (precompute) --------
    # receita mensal (pagamentos)
    cur.execute(
        """
        WITH m AS (
          SELECT substr(date,1,7) AS month, SUM(amount) AS revenue
          FROM payments
          GROUP BY 1
        )
        INSERT OR REPLACE INTO monthly_revenue(month, revenue)
        SELECT month, revenue FROM m
        """
    )

    # inadimplência por mês (vencido / (aberto+vencido)) pela due_date
    cur.execute(
        """
        WITH base AS (
          SELECT substr(due_date,1,7) AS month,
                 SUM(CASE WHEN status='vencido' THEN 1 ELSE 0 END) AS overdue,
                 SUM(CASE WHEN status='aberto'  THEN 1 ELSE 0 END) AS open
          FROM invoices
          GROUP BY 1
        )
        INSERT OR REPLACE INTO delinquency(month, delinquency_rate)
        SELECT month,
               CASE WHEN (open+overdue)>0
                    THEN CAST(overdue AS REAL)/(open+overdue)
                    ELSE 0 END
        FROM base
        """
    )

    # Índices úteis (idempotentes)
    cur.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_invoices_associate ON invoices(associate_id);
        CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);
        CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);
        CREATE INDEX IF NOT EXISTS idx_registrations_event ON registrations(event_id);
        CREATE INDEX IF NOT EXISTS idx_registrations_assoc ON registrations(associate_id);
        CREATE INDEX IF NOT EXISTS idx_monthly_revenue_month ON monthly_revenue(month);
        CREATE INDEX IF NOT EXISTS idx_delinquency_month ON delinquency(month);
        """
    )

    con.commit()
    con.close()
    print(f"✔ Banco gerado/populado em: {DB_PATH.resolve()}")

if __name__ == "__main__":
    main()
