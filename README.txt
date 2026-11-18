GROUP 7 - NEON POSTGRESQL EXPERIMENT PACKAGE

CONTENTS
- setup.sql: optional SQL setup script (the Python script also creates/populates the table automatically)
- benchmark_neon.py: runs the warm, idle/resume, and concurrent query measurements

BEFORE YOU START
1. Create a free Neon project at https://console.neon.tech/.
2. In the Neon dashboard, choose Connect and copy the PostgreSQL connection string. Keep it private; it contains your database password.
3. Install Python 3 from https://www.python.org/downloads/windows/. During installation, enable "Add Python to PATH".
4. Extract this ZIP to a folder, e.g. Desktop\Group7_Neon_Experiment_Package.

RUN ON WINDOWS (PowerShell)
1. Open the extracted folder in File Explorer.
2. Click the address bar, type powershell, and press Enter.
3. Check Python: python --version
4. Install dependency: python -m pip install psycopg2-binary
5. Set the connection string for this PowerShell window only:
   $env:DATABASE_URL="postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"
   Replace the example with the exact connection string copied from Neon. Do not share it or upload it to GitHub.
6. Run: python benchmark_neon.py
7. Keep PowerShell open. The script waits 370 seconds between warm queries and the first-after-idle measurement. Avoid using the database during that idle period.

OUTPUT FILES
- neon_results.csv: individual measurements (timestamp, condition, trial, elapsed_ms, status, row_count, error)
- neon_summary.txt: mean, median, minimum, maximum, sample count, and error count for each test condition

TEST CONDITIONS
- warm: 10 individual requests while the database is active
- first_after_idle: first request after a 370-second idle interval
- after_resume: 5 subsequent requests after the first post-idle request
- concurrent_burst: 10 requests submitted concurrently

IMPORTANT NOTES
- The script creates a table and inserts up to 5,000 sample rows automatically.
- Actual timings depend on region, network, plan, load, and whether Neon suspends compute as expected. Do not copy example numbers or invent results.
- A 370-second wait is intended to exceed the commonly documented 5-minute inactivity period on eligible Neon compute, but suspension behaviour can depend on project settings and plan. If the first-after-idle result does not show a clear resume delay, report the observed value honestly and mention the limitation.
- If a row has status=error, inspect its error field. Do not treat failed trials as valid latency measurements.
- Before sharing neon_results.csv, check that it does not contain credentials. It should not contain the connection string.
- Do not paste your database connection string into the assignment PDF, chat, screenshots, or GitHub.
