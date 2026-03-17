from app import create_app
from flask import render_template
from flask_talisman import Talisman  # Importa Flask-Talisman
from ldap3 import Server, Connection, ALL, SIMPLE
import socket

app = create_app()

# Configuración de modo de mantenimiento de forma centralizada
app.config['MAINTENANCE_MODE'] = False

# Configura Talisman para forzar HTTPS
Talisman(app, content_security_policy=None)

@app.before_request
def check_for_maintenance():
    if app.config.get('MAINTENANCE_MODE'):
        return render_template('maintenance.html')

if __name__ == '__main__':
    ssl_cert = 'C:\\Users\\amjimenez\\OneDrive - NEW STETIC S.A\\Documentos\\DESARROLLOS\\TRACKING17032025\\certificates\\server.crt'
    ssl_key = 'C:\\Users\\amjimenez\\OneDrive - NEW STETIC S.A\\Documentos\\DESARROLLOS\\TRACKING17032025\\certificates\\server.key'
    app.run(
        host='0.0.0.0',
        port=12443,
        ssl_context=(ssl_cert, ssl_key)  # <-- ESTA LÍNEA ES CLAVE
    )