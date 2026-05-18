from allowedflare.gunicorn import configure

configure(globals())
bind = 'localhost:8001'  # Should match docker-compose.yaml and manage.py
wsgi_app = 'demodj.wsgi'
