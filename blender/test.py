import socket
import subprocess
import os

def distribute_rendering(blender_file, num_workers, start_frame, end_frame):
    # Set up a socket for communication
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12345))  # Adjust the port as needed
    server_socket.listen(num_workers)

    # Launch Blender instances on worker clients
    for _ in range(num_workers):
        worker_socket, addr = server_socket.accept()
        cmd = [
            "blender",
            "--background",
            blender_file,
            "--python",
            os.path.realpath(__file__),  # This script file
            "--",
            "--start_frame",
            str(start_frame),
            "--end_frame",
            str(end_frame),
        ]
        worker_socket.send((" ".join(cmd)).encode())
        worker_socket.close()

    server_socket.close()

if __name__ == "__main__":
    blend_file_path = "/path/to/your/blender/file.blend"
    num_workers = 3
    start_frame = 1
    end_frame = 250
    distribute_rendering(blend_file_path, num_workers, start_frame, end_frame)
