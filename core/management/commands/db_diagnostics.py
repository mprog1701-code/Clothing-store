from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

class Command(BaseCommand):
    help = "Print DB diagnostics and run phone uniqueness checks"

    def add_arguments(self, parser):
        parser.add_argument("--phone", dest="phone", default="", help="Phone to search across tables")

    def handle(self, *args, **options):
        db = settings.DATABASES.get("default", {})
        engine = db.get("ENGINE") or ""
        name = db.get("NAME") or ""
        host = db.get("HOST") or ""
        port = str(db.get("PORT") or "")
        user = db.get("USER") or ""
        url = (settings.DATABASE_URL or "").strip()
        safe_host = host
        user_prefix = (user or "")[:3]
        if not safe_host and url:
            try:
                from urllib.parse import urlparse
                p = urlparse(url)
                h = p.netloc.split("@")[-1]
                safe_host = h.split(":")[0]
                name = (p.path or "").lstrip("/") or name
                try:
                    cred = p.netloc.split("@")[0]
                    u = cred.split(":")[0]
                    user_prefix = (u or "")[:3]
                except Exception:
                    pass
            except Exception:
                pass
        print(f"[db] engine={engine}")
        print(f"[db] name={name}")
        print(f"[db] host={safe_host}")
        print(f"[db] port={port}")
        print(f"[db] has_DATABASE_URL={bool(url)}")
        print(f"[db] user_prefix={user_prefix}")

        with connection.cursor() as cur:
            try:
                cur.execute("SELECT COUNT(*) FROM core_user")
                c_users = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM core_store")
                c_stores = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM core_storeownerinvite")
                c_invites = cur.fetchone()[0]
                print(f"[count] core_user={c_users}")
                print(f"[count] core_store={c_stores}")
                print(f"[count] core_storeownerinvite={c_invites}")
            except Exception as e:
                print(f"[count] failed: {e}")

            try:
                print("[invites] last 10:")
                cur.execute("SELECT phone, status, created_at, expires_at, claimed_at FROM core_storeownerinvite ORDER BY id DESC LIMIT 10")
                rows = cur.fetchall()
                for r in rows:
                    print(r)
            except Exception as e:
                print(f"[invites] query failed: {e}")

            try:
                print("[db] last 50 users:")
                cur.execute("SELECT id, phone, username, email, date_joined FROM core_user ORDER BY id DESC LIMIT 50")
                rows = cur.fetchall()
                for r in rows:
                    print(r)
            except Exception as e:
                print(f"[db] users query failed: {e}")

            phone = (options.get("phone") or "").strip()
            if phone:
                print(f"[db] search phone={phone}")
                try:
                    cur.execute("SELECT 'core_user' AS table, CAST(id AS TEXT), phone FROM core_user WHERE phone = %s", [phone])
                    rows = cur.fetchall()
                    for r in rows:
                        print(r)
                except Exception as e:
                    print(f"[db] core_user phone search failed: {e}")
                try:
                    cur.execute("SELECT 'core_store' AS table, CAST(id AS TEXT), owner_phone FROM core_store WHERE owner_phone = %s", [phone])
                    rows = cur.fetchall()
                    for r in rows:
                        print(r)
                except Exception:
                    pass
                try:
                    cur.execute("SELECT 'core_phonereservation' AS table, CAST(id AS TEXT), phone FROM core_phonereservation WHERE phone = %s", [phone])
                    rows = cur.fetchall()
                    for r in rows:
                        print(r)
                except Exception:
                    pass

            vendor = connection.vendor
            print(f"[db] vendor={vendor}")
            if vendor == "postgres":
                try:
                    sql = (
                        "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'core_user'"
                    )
                    cur.execute(sql)
                    idx = cur.fetchall()
                    for name, defn in idx:
                        print(f"[db] index: {name} {defn}")
                except Exception as e:
                    print(f"[db] index inspection failed: {e}")
            else:
                try:
                    cur.execute("PRAGMA index_list('core_user')")
                    idx = cur.fetchall()
                    for it in idx:
                        print(f"[db] index_list: {it}")
                except Exception as e:
                    print(f"[db] sqlite index inspection failed: {e}")
