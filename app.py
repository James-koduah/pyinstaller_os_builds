from flask import Flask, jsonify, render_template, request
import webbrowser
import threading
import socket

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test', methods=['POST'])
def test():
    data = request.get_json()
    print(data)
    return jsonify({'data': 'It is working!!!'})

def open_browser(port):
    # Open the browser to the specified port
    webbrowser.open(f"http://127.0.0.1:{port}")

def find_free_port(default_port=5000):
    # Try to bind to the default port; if unavailable, find another free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", default_port))
        port = sock.getsockname()[1]
    except OSError:
        # If binding fails, find an available port
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    finally:
        sock.close()
    return port

if __name__ == '__main__':
    port = find_free_port()  # Get an available port
    threading.Thread(target=open_browser, args=(port,)).start()
    app.run('0.0.0.0', port)
