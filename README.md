from flask import Flask, Response
import cv2
from picamera2 import Picamera2
import numpy as np
import time

app = Flask(__name__)

# --- IMPORTANT NOTE ON LIBCAMERA ---
# The original code uses `cv2.VideoCapture(0)`, which relies on the V4L2 interface.
# On modern Raspberry Pi OS, the camera stack uses `libcamera`.
# To interact with `libcamera` in Python, you need to use the `picamera2` library.
# This library works differently from `cv2.VideoCapture`.
# There is no direct "drop-in" replacement for `cv2.VideoCapture`'s methods like `set()`
# for resolutions. Instead, you configure the camera with `picamera2`'s own methods.

# Initialize Picamera2
# This creates an object to control the Raspberry Pi camera via libcamera.
camera = Picamera2()

# Define desired resolutions to try, from highest to lowest.
# Picamera2 will attempt to use the highest resolution it supports that is
# close to the one specified in `create_video_configuration`.
# For streaming, a balance between resolution and frame rate is crucial.
# 1920x1080 (Full HD) is a common and good starting point for web streams.
resolutions_to_try = [
    (3840, 2160),  # 4K UHD
    (2560, 1440),  # 2K QHD
    (1920, 1080),  # Full HD
    (1280, 720),   # HD
    (1024, 768),
    (800, 600),
    (640, 480)
]

# Attempt to configure the camera with the highest possible resolution from the list.
# Note: Picamera2 might not support all resolutions listed, it will pick the closest.
configured_resolution = None
for res_width, res_height in resolutions_to_try:
    try:
        # Create a video configuration. The 'main' stream is typically used for capture.
        # The 'size' parameter specifies the desired resolution.
        config = camera.create_video_configuration(main={"size": (res_width, res_height)})
        camera.configure(config)
        configured_resolution = (res_width, res_height)
        print(f"Attempting to set resolution to: {res_width}x{res_height}")
        # Break after the first successful configuration attempt
        break
    except Exception as e:
        print(f"Could not configure camera for {res_width}x{res_height}: {e}")

if configured_resolution:
    print(f"Camera configured with resolution: {camera.stream_configuration('main')['size']}")
else:
    print("Could not configure camera with any preferred resolution. Using default.")
    # Fallback to default configuration if none of the preferred ones worked
    camera.configure(camera.create_video_configuration())

# Start the camera capture process.
camera.start()
# Give the camera a moment to warm up and stabilize.
time.sleep(1)


def generate_frames():
    """
    Generator function to continuously capture frames from the camera,
    encode them as JPEG, and yield them for the Flask response.
    """
    while True:
        try:
            # Capture a frame directly from picamera2 as a NumPy array.
            # `capture_array()` is efficient for getting raw frame data.
            frame = camera.capture_array()

            # Picamera2 typically provides frames in RGB format.
            # OpenCV's `imencode` (and many other OpenCV functions) expect BGR format.
            # Convert the frame from RGB to BGR for OpenCV compatibility.
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Encode the frame as a JPEG image.
            # `cv2.imencode` returns a tuple: (success_flag, buffer_of_encoded_image).
            ret, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not ret:
                print("Failed to encode frame to JPEG!")
                continue # Skip this frame and try the next one

            # Convert the buffer to bytes.
            frame_bytes = buffer.tobytes()

            # Yield the frame in the multipart/x-mixed-replace format required for MJPEG streaming.
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        except Exception as e:
            # Catch any exceptions during frame capture or processing
            print(f"Error during frame generation: {e}")
            # In a real application, you might want to log this error,
            # attempt to restart the camera, or gracefully shut down.
            break # Exit the loop if an unrecoverable error occurs

@app.route('/video_feed')
def video_feed():
    """
    Flask route that serves the video stream.
    It returns a Response object with the generator and the appropriate MIME type
    for MJPEG streaming.
    """
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """
    Simple HTML page to display the video feed.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Raspberry Pi Camera Stream</title>
        <style>
            body {
                font-family: 'Inter', sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                background-color: #f0f2f5;
                margin: 0;
                padding: 20px;
                box-sizing: border-box;
            }
            .container {
                background-color: #ffffff;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
                text-align: center;
                width: 90%;
                max-width: 800px;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.8em;
            }
            img {
                width: 100%;
                height: auto;
                border: 2px solid #ddd;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
                max-width: 760px; /* Max width to prevent overly large images */
            }
            .footer {
                margin-top: 30px;
                color: #777;
                font-size: 0.9em;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Live Raspberry Pi Camera Feed</h1>
            <img src="/video_feed" alt="Raspberry Pi Camera Stream">
            <p class="footer">Powered by Flask and Picamera2</p>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Run the Flask application.
    # host='0.0.0.0' makes the server accessible from any IP address on the network.
    # port=5000 is the default Flask port.
    app.run(host='0.0.0.0', port=5000)
