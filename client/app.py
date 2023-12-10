from client import Commander, Soldier
import hashlib
import time
import numpy as np
import pickle
import json
import base64
# IP = '192.168.0.107'
IP = '127.0.0.1'
PORT = 5000
ID = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()


# num_balls, max_initial_height, num_steps, damping_factor, dt
def simulate_bouncing_balls_normal(**kwargs):
    print("kwargs: ", kwargs)
    num_balls = kwargs["num_balls"]
    max_initial_height = kwargs["max_initial_height"]
    num_steps = kwargs["num_steps"]
    damping_factor = kwargs["damping_factor"]
    dt = kwargs["dt"]
    initial_heights = kwargs["initial_heights"]

    time_steps = []
    heights_list = []

    for i in range(len(initial_heights)):
        # initial_height = np.random.uniform(0, max_initial_height)
        initial_height = initial_heights[i]
        height = initial_height
        velocity = 0.0
        heights = []

        for step in range(num_steps):
            acceleration_due_to_gravity = 9.8
            acceleration = -damping_factor * velocity - acceleration_due_to_gravity
            velocity += acceleration * dt
            height += velocity * dt

            heights.append(height)
            if height <= 0:
                height = 0
                velocity = -velocity * damping_factor

        time_steps.append(np.arange(num_steps) * dt)
        heights_list.append(heights)

    heights_list = [heights.tolist() for heights in heights_list]
    time_steps = [time_step.tolist() for time_step in time_steps]

    return [time_steps, heights_list]



def main():
    type = input("Enter type (commander C/soldier S): ").lower()
    if type == "c":
        client = Commander(IP, PORT, ID)
        while True:
            # command = input("Enter command: ")
            input("Press Enter to send a message to the server... \n")
            num_steps = 750
            max_initial_height = 25.0
            num_balls = 1_000
            damping_factor = 0.5
            dt = 0.01
            initial_heights = np.random.uniform(0, max_initial_height, num_balls).tolist()
            serialized_function = base64.b64encode(pickle.dumps(simulate_bouncing_balls_normal)).decode('utf-8')
            command = {
                # "function" : simulate_bouncing_balls_normal,
                'function': serialized_function,
                "num_steps": num_steps,
                "num_balls": num_balls,
                "damping_factor":damping_factor,
                "max_initial_height":max_initial_height,
                "dt":dt,
                "initial_heights":initial_heights
            }

            start = time.time()
            result = client.command(command)
            end = time.time()
            # print(f'Result: {result}')
            print(f'Time taken: {end - start}')
    elif type == "s":
        client = Soldier(IP, PORT, ID)
        while True:
            print("Waiting for orders...")
            task_id = client.receive_orders()
            print(f'Obeyed order: {task_id}')


if __name__ == "__main__":
    main()

