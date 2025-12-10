nice -n 19 python3 app.py

# python -m gunicorn -b 0.0.0.0:8050 app:server --timeout 120
# nice -n 19 python -m gunicorn -b 0.0.0.0:8050 app:server --timeout 120