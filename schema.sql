PRAGMA foreign_keys = ON;

-- ============ TABELAS BASE ============
CREATE TABLE IF NOT EXISTS associates (
  associate_id TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  cpf_mask    TEXT NOT NULL,
  join_date   TEXT NOT NULL,                 -- YYYY-MM-DD
  status      TEXT NOT NULL CHECK(status IN ('ativo','inadimplente','suspenso')),
  plan        TEXT NOT NULL CHECK(plan IN ('Básico','Padrão','Premium')),
  monthly_fee REAL NOT NULL CHECK(monthly_fee >= 0)
);

CREATE TABLE IF NOT EXISTS events (
  event_id   TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  start_date TEXT NOT NULL,                  -- YYYY-MM-DD
  end_date   TEXT NOT NULL,                  -- YYYY-MM-DD
  price      REAL NOT NULL CHECK(price >= 0),
  seats      INTEGER NOT NULL CHECK(seats > 0)
);

CREATE TABLE IF NOT EXISTS invoices (
  invoice_id    TEXT PRIMARY KEY,
  associate_id  TEXT NOT NULL REFERENCES associates(associate_id),
  issue_date    TEXT NOT NULL,               -- YYYY-MM-DD
  due_date      TEXT NOT NULL,               -- YYYY-MM-DD
  amount        REAL NOT NULL CHECK(amount >= 0),
  status        TEXT NOT NULL CHECK(status IN ('aberto','pago','vencido','cancelado')),
  payment_date  TEXT,                        -- YYYY-MM-DD
  boleto_number TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS payments (
  payment_id   TEXT PRIMARY KEY,
  invoice_id   TEXT NOT NULL REFERENCES invoices(invoice_id),
  date         TEXT NOT NULL,                -- YYYY-MM-DD
  method       TEXT NOT NULL CHECK(method IN ('boleto','pix','cartao')),
  amount       REAL NOT NULL CHECK(amount >= 0),
  conciliated  INTEGER NOT NULL CHECK(conciliated IN (0,1)),
  gateway_txid TEXT
);

CREATE TABLE IF NOT EXISTS registrations (
  registration_id TEXT PRIMARY KEY,
  event_id        TEXT NOT NULL REFERENCES events(event_id),
  associate_id    TEXT NOT NULL REFERENCES associates(associate_id),
  date            TEXT NOT NULL,             -- YYYY-MM-DD
  paid            INTEGER NOT NULL CHECK(paid IN (0,1)),
  UNIQUE(event_id, associate_id)
);

-- ============ RELATÓRIOS ============
CREATE TABLE IF NOT EXISTS monthly_revenue (
  month   TEXT PRIMARY KEY,                  -- YYYY-MM
  revenue REAL NOT NULL CHECK(revenue >= 0)
);

CREATE TABLE IF NOT EXISTS delinquency (
  month            TEXT PRIMARY KEY,         -- YYYY-MM
  delinquency_rate REAL NOT NULL CHECK(delinquency_rate >= 0 AND delinquency_rate <= 1)
);

-- ============ ÍNDICES ============
CREATE INDEX IF NOT EXISTS idx_invoices_due        ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_invoices_associate  ON invoices(associate_id);
CREATE INDEX IF NOT EXISTS idx_payments_invoice    ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payments_date       ON payments(date);
CREATE INDEX IF NOT EXISTS idx_reg_event           ON registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_reg_associate       ON registrations(associate_id);

Adiciona schema inicial do banco
