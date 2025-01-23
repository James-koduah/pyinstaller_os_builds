from datetime import datetime
import os
import time
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
from image_exif import sort_all_filenames_in_folder_numerically, make_sure_all_images_are_present, add_exif, filter_broken_brackets
import webbrowser
import threading
import socket
from engineio.async_drivers import gevent

app = Flask(__name__)

app.config['SECRET_KEY'] = 'verysecretlol'
socketio = SocketIO(app)

keep_running = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/begin_processing', methods=['post'])
def begin_processing():
    data = request.get_json()
    try:
        filenames = sort_all_filenames_in_folder_numerically(data.get('folder_path'))
        if len(filenames) == 0:
            return jsonify({'status': False, 'problem': 'empty_folder'})
    except:
        return jsonify({'status': False, 'problem': 'bad_path'})
    
    check = make_sure_all_images_are_present(filenames)
    if check:
        return jsonify({'status': False, 'problem': 'missing_files', 'data': check})
    
    process_files(data, filenames)
    return jsonify(filenames)

@app.route('/continue_processing', methods=['post'])
def continue_processing():
    data = request.get_json()
    filenames = sort_all_filenames_in_folder_numerically(data.get('folder_path'))
    process_files(data, filenames)
    return jsonify({})

@app.route('/skip_broken', methods=['post'])
def skip_broken():
    data = request.get_json()
    filenames = sort_all_filenames_in_folder_numerically(data.get('folder_path'))
    filtered_brackets = filter_broken_brackets(filenames, len(data.get('frame_sequence')))
    process_files(data, filtered_brackets)
    return jsonify({})


def process_files(data, filenames):

    frame_number = 0
    bracket_date = None
    folder_path = data.get('folder_path')
    output_path = data.get('output_path')
    frame_sequence = data.get('frame_sequence')
    metadata = {
        'camera_make': data.get('camera_make'),
        'camera_model': data.get('camera_model'),
        'white_balance': int(data.get('white_balance')),
        'focal_length': int(data.get('focal_length')),
        'iso_speed': int(data.get('iso_speed')),
        'aperture': int(data.get('aperture'))
    }
    frame_data = {
        'under': {
            'exposure_time': int(data.get('under_exposure_time')),
            'exposure_bias': int(data.get('under_exposure_bias')),
        },
        'mild-under': {
            'exposure_time': int(data.get('mild_under_exposure_time')) if data.get('mild_under_exposure_time') else None,
            'exposure_bias': int(data.get('mild_under_exposure_bias')) if data.get('mild_under_exposure_bias') else None,
        },
        'normal': {
            'exposure_time': int(data.get('normal_exposure_time')),
            'exposure_bias': int(data.get('normal_exposure_bias')),
        },
        'mild-over': {
            'exposure_time': int(data.get('mild_over_exposure_time')) if data.get('mild_over_exposure_bias') else None,
            'exposure_bias': int(data.get('mild_over_exposure_bias')) if data.get('mild_over_exposure_bias') else None,
        },
        'over': {
            'exposure_time': int(data.get('over_exposure_time')),
            'exposure_bias': int(data.get('over_exposure_bias'),)
        }
    }
    global keep_running
    keep_running = True
    for i in range(0, len(filenames)):
        if not keep_running:
            break
        filename = filenames[i]
        if frame_number == 0:
            socketio.emit('processing', [filenames[i+j] for j in range(0, len(frame_sequence))])
            time.sleep(2)
            bracket_date = datetime.now()
            bracket_date = bracket_date.strftime("%Y:%m:%d %H:%M:%S")
        current_frame_type = frame_sequence[frame_number]
        add_exif(folder_path, filename, metadata, frame_data.get(current_frame_type), bracket_date, output_path)
        frame_number += 1
        if frame_number >= len(frame_sequence):
            frame_number = 0

def shutdown_server():
    """Gracefully shuts down the Flask server."""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        os._exit(0)
    func()

@socketio.on('stop_processing')
def stop_process():
    """Stops the long-running process."""
    global keep_running
    keep_running = False
    print('stopping')
    emit('stopped_process')

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
    socketio.run(app, host='0.0.0.0', port=port, debug=True)