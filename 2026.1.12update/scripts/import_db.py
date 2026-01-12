import os
import mysql.connector
from mysql.connector import errorcode

DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = int(os.environ.get('DB_PORT', '8000'))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'marker86')
SQL_PATH = os.path.join(os.path.dirname(__file__), '..', 'init_db.sql')

print(f"Connecting to MySQL {DB_USER}@{DB_HOST}:{DB_PORT} ...")

with open(SQL_PATH, 'r', encoding='utf-8') as f:
    sql = f.read()

# Remove any DEFINER/SQL comments that mysql-connector may not like? We'll pass directly using multi=True.
try:
    cnx = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        autocommit=True,
        connection_timeout=30,
    )
except mysql.connector.Error as err:
    print('Connection error:', err)
    raise SystemExit(1)

cursor = cnx.cursor()
print('Executing SQL script (this can take a while)...')
try:
    try:
        # Try multi execution (some connector versions support it)
        for result in cursor.execute(sql, multi=True):
            if getattr(result, 'with_rows', False):
                _ = result.fetchall()
            if getattr(result, 'statement', None):
                print('OK:', (result.statement or '')[:80].replace('\n',' '))
    except TypeError:
        # Fallback: split by semicolon and execute statements one-by-one
        print('multi=True not supported; falling back to single-statement execution')
        parts = [p.strip() for p in sql.split(';') if p.strip()]
        for i, stmt in enumerate(parts, 1):
            try:
                cursor.execute(stmt)
                print(f'OK ({i}/{len(parts)})')
            except mysql.connector.Error as e:
                print(f'Error at statement {i}:', e)
                raise
except mysql.connector.Error as err:
    print('Error executing SQL:', err)
    cursor.close()
    cnx.close()
    raise SystemExit(1)

print('SQL execution finished. Listing databases:')
try:
    cursor.execute('SHOW DATABASES')
    dbs = [row[0] for row in cursor.fetchall()]
    for d in dbs:
        print(' -', d)
except mysql.connector.Error as err:
    print('Error listing databases:', err)

cursor.close()
cnx.close()
print('Done.')
