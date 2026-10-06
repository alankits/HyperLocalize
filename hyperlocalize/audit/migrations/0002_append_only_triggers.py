"""PostgreSQL triggers that make audit_record append-only (ADR 0007).

Row-level triggers reject UPDATE and DELETE; a statement-level trigger rejects
TRUNCATE. A table owner can still disable triggers; the hash chain is what makes
such tampering detectable (tamper-evident, not tamper-proof).
"""
from django.db import migrations

SQL = """
CREATE OR REPLACE FUNCTION audit_record_reject_change() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_record is append-only (%)', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_record_no_update_delete
    BEFORE UPDATE OR DELETE ON audit_record
    FOR EACH ROW EXECUTE FUNCTION audit_record_reject_change();

CREATE TRIGGER audit_record_no_truncate
    BEFORE TRUNCATE ON audit_record
    FOR EACH STATEMENT EXECUTE FUNCTION audit_record_reject_change();
"""

REVERSE = """
DROP TRIGGER IF EXISTS audit_record_no_truncate ON audit_record;
DROP TRIGGER IF EXISTS audit_record_no_update_delete ON audit_record;
DROP FUNCTION IF EXISTS audit_record_reject_change();
"""


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
