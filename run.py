from app import create_app
from livereload import Server
import socket
import webbrowser
import os

def find_free_port(start=5500, end=5600):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found.")

app = create_app()
app.debug = True
server = Server(app.wsgi_app)

# Watch for changes
server.watch('app/templates/**/*.html')
server.watch('app/static/**/*.css')
server.watch('app/**/*.py')

# Trouver un port libre
free_port = find_free_port()

# Lancer le navigateur (Chrome de préférence)
url = f"http://localhost:{free_port}"
try:
    webbrowser.get("macosx").open_new(url)
except:
    pass

os.system(f"open -a 'Google Chrome' {url}")

# Lancer le serveur
server.serve(open_url=False, debug=True, port=free_port)