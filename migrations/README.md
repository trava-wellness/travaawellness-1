Use Flask-Migrate for schema versioning.

Typical commands:

1. `flask db init` (first time only)
2. `flask db migrate -m "message"`
3. `flask db upgrade`

Set `FLASK_APP=app.py` before running migration commands.
