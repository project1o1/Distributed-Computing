import subprocess
import time

blender_path = '"C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"'
output_format = "PNG"
folder_name = '"cube_diorama"'
file_name = '"ripple_dreams_fields.blend"'
start_frame = 1
end_frame = 10

start = time.time()
subprocess.call(f'{blender_path} -b {folder_name}/{file_name} -o "C:/Users/visha/Desktop/Stuff/distributed_computing/blender/blender_output/" -F {output_format} -x 1 -s {start_frame} -e {end_frame} -a', shell=True)
end = time.time()
print(end - start)