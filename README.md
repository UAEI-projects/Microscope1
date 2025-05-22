%Run camera_server.py
[0:29:25.465100249] [6762]  INFO Camera camera_manager.cpp:326 libcamera v0.5.0+59-d83ff0a4
Traceback (most recent call last):
  File "/home/pi/Downloads/camera_server.py", line 19, in <module>
    camera = Picamera2()
  File "/usr/lib/python3/dist-packages/picamera2/picamera2.py", line 281, in __init__
    camera_num = self.global_camera_info()[camera_num]['Num']
IndexError: list index out of range
