import subprocess
import os
import cv2

# Blender rendering settings
start_frame = 1
end_frame = 6
num_machines = 2
frames_per_machine = (end_frame - start_frame + 1) // num_machines

# Blender rendering command
blender_command = '"C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"'
blend_file = '"C:/Users/visha/Downloads/jiggly_pudding.blend"'
output_directory = '"C:/Users/visha/Downloads/output/"'
output_format = 'JPEG'

# Render frames using Blender
for i in range(num_machines):
    start = start_frame + i * frames_per_machine
    end = start + frames_per_machine - 1

    command = f'{blender_command} -b {blend_file} -o {output_directory} -F {output_format} -x 1 -s {start} -e {end} -a'
    subprocess.run(command, shell=True)

# Read and sort the list of image files
image_files = [os.path.join(output_directory, f'frame_{i:04d}.{output_format}') for i in range(start_frame, end_frame + 1)]
image_files.sort()

# Create a video using OpenCV
video_output_path = '"C:/Users/visha/Downloads/output/video.mp4"'
frame = cv2.imread(image_files[0])
height, width, layers = frame.shape
video = cv2.VideoWriter(video_output_path, cv2.VideoWriter_fourcc(*'mp4v'), 24, (width, height))

for image_file in image_files:
    video.write(cv2.imread(image_file))

cv2.destroyAllWindows()
video.release()

# Optionally, clean up the individual image files
for image_file in image_files:
    os.remove(image_file)

# Clean up the empty output_directory
os.rmdir(output_directory)
