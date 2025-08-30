PRAGMA foreign_keys = ON;

-- =========================
-- Tabela de associados
-- =========================
CREATE TABLE IF NOT EXISTS associates (
  associate_id   TEXT PRIMARY KEY,
  name           TEXT NOT NULL,
  cpf_mask       TEXT,
  join_date      TEXT,               -- YYYY-MM-DD
  status         TEXT,               -- ativo | inadimplente | suspenso
  plan           TEXT,               -- Básico | Padrão | Premium
  monthly_fee    REAL
);

-- =========================
-- Eventos
-- =========================
CREATE TABLE IF NOT EXISTS events (
  event_id   TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  start_date TEXT NOT NULL,          -- YYYY-MM-DD
  end_date   TEXT NOT NULL,          -- YYYY-MM-DD
  price      REAL NOT NULL DEFAULT 0,
  seats      INTEGER NOT NULL
);

-- =========================
-- Faturas
-- =========================
CREATE TABLE IF NOT EXISTS invoices (
  invoice_id    TEXT PRIMARY KEY,
  associate_id  TEXT REFERENCES associates(associate_id) ON DELETE SET NULL,
  issue_date    TEXT NOT NULL,       -- YYYY-MM-DD
  due_date      TEXT NOT NULL,       -- YYYY-MM-DD
  amount        REAL NOT NULL,
  status        TEXT NOT NULL,       -- aberto | pago | vencido | cancelado
  payment_date  TEXT,                -- YYYY-MM-DD (se pago)
  boleto_number TEXT
);

-- =========================
-- Pagamentos
-- =========================
CREATE TABLE IF NOT EXISTS payments (
  payment_id   TEXT PRIMARY KEY,
  invoice_id   TEXT NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
  date         TEXT NOT NULL,        -- YYYY-MM-DD
  method       TEXT NOT NULL,        -- boleto | pix | cartao
  amount       REAL NOT NULL,
  conciliated  INTEGER NOT NULL DEFAULT 0,  -- 0/1
  gateway_txid TEXT                   -- quando PIX
);

-- =========================
-- Inscrições em eventos
-- =========================
CREATE TABLE IF NOT EXISTS registrations (
  registration_id TEXT PRIMARY KEY,
  event_id        TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  associate_id    TEXT NOT NULL REFERENCES associates(associate_id) ON DELETE CASCADE,
  date            TEXT NOT NULL,     -- YYYY-MM-DD (usa start_date do evento)
  paid            INTEGER NOT NULL DEFAULT 0  -- 0/1
);

-- =========================
-- Relatórios agregados
-- =========================
CREATE TABLE IF NOT EXISTS monthly_revenue (
  month    TEXT PRIMARY KEY,         -- YYYY-MM
  revenue  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS delinquency (
  month             TEXT PRIMARY KEY,  -- YYYY-MM
  delinquency_rate  REAL NOT NULL      -- 0..1
);

-- Índices úteis
CREATE INDEX IF NOT EXISTS idx_invoices_associate    ON invoices(associate_id);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date     ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_payments_invoice      ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_registrations_event   ON registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_registrations_assoc   ON registrations(associate_id);
CREATE INDEX IF NOT EXISTS idx_monthly_revenue_month ON monthly_revenue(month);
CREATE INDEX IF NOT EXISTS idx_delinquency_month     ON delinquency(month);
