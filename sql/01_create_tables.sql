-- Base tables are loaded from CSV by src/build_database.py.
-- This file creates indexes and can be rerun safely.
CREATE INDEX IF NOT EXISTS idx_snapshot_acct_month ON monthly_card_snapshot(account_id, month);
CREATE INDEX IF NOT EXISTS idx_bureau_acct_month ON bureau_tradeline_proxy(account_id, month);
CREATE INDEX IF NOT EXISTS idx_accounts_acct ON accounts(account_id);
CREATE INDEX IF NOT EXISTS idx_macro_month ON macro_scenario_panel(month);
