# README — Connect to a database, list tables, run queries

## Purpose
Quick reference to connect to common SQL databases, list tables and run simple queries. Includes CLI commands and short Python / Node.js snippets for PostgreSQL, MySQL and SQLite.

## Prerequisites
- DB reachable (host/port) or local file for SQLite.
- Appropriate client tools/drivers installed:
        - PostgreSQL: psql or psycopg2 (Python) / pg (Node.js)
        - MySQL: mysql client or mysql-connector-python / mysql2 (Node.js)
        - SQLite: sqlite3 CLI or builtin sqlite3 module (Python) / sqlite3 (Node.js)

## PostgreSQL (CLI)
Connect:
```bash
psql -h <host> -p <port> -U <user> -d <dbname>
```

List tables (psql interactive):
```psql
\dt
```

List tables (SQL):
```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
        AND table_schema NOT IN ('pg_catalog','information_schema');
```

Run a simple query:
```sql
SELECT * FROM public.my_table LIMIT 10;
```

## MySQL (CLI)
Connect:
```bash
mysql -h <host> -P <port> -u <user> -p <dbname>
```

List tables:
```sql
SHOW TABLES;
```

Or via information_schema:
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = '<dbname>';
```

Run a simple query:
```sql
SELECT * FROM my_table LIMIT 10;
```

## SQLite (CLI)
Open DB:
```bash
sqlite3 /path/to/database.sqlite
```

List tables (CLI):
```sql
.tables
```

Or via SQL:
```sql
SELECT name
FROM sqlite_master
WHERE type='table' AND name NOT LIKE 'sqlite_%';
```

Run a simple query:
```sql
SELECT * FROM my_table LIMIT 10;
```

## Python examples

PostgreSQL (psycopg2):
```python
import psycopg2

conn = psycopg2.connect(host="host", port=5432, dbname="db", user="user", password="pw")
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
print(cur.fetchall())
cur.execute("SELECT * FROM my_table LIMIT 5")
print(cur.fetchall())
cur.close()
conn.close()
```

SQLite (builtin):
```python
import sqlite3

conn = sqlite3.connect("path/to/database.sqlite")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cur.fetchall())
cur.close()
conn.close()
```

## Node.js examples

PostgreSQL (pg):
```js
const { Client } = require('pg');

const client = new Client({ host:'host', port:5432, user:'user', password:'pw', database:'db' });
await client.connect();
const res = await client.query("SELECT table_name FROM information_schema.tables WHERE table_schema='public'");
console.log(res.rows);
await client.end();
```

MySQL (mysql2):
```js
const mysql = require('mysql2/promise');

const conn = await mysql.createConnection({ host:'host', user:'user', database:'db', password:'pw' });
const [rows] = await conn.execute('SHOW TABLES');
console.log(rows);
await conn.end();
```

## Tips
- Secure credentials (environment variables, .env, secret stores).
- Use LIMIT when exploring large tables.
- Use information_schema or sqlite_master for metadata queries.
- Always use parameterized queries in production to avoid SQL injection.

If you need a specific DB version, connector/ORM example, or a short connection string for a particular environment, state the DB and language.