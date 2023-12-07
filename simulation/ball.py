import matplotlib.pyplot as plt
import numpy as np
import timeit

def simulate_bouncing_balls_normal(num_balls, max_initial_height, num_steps, damping_factor, dt):
    time_steps = []
    heights_list = []

    for _ in range(num_balls):
        initial_height = np.random.uniform(0, max_initial_height)
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

    return time_steps, heights_list

def simulate_bouncing_balls_numpy(num_balls, max_initial_height, num_steps, damping_factor, dt):
    time_steps = np.arange(num_steps) * dt
    heights_list = np.zeros((num_balls, num_steps))

    initial_heights = np.random.uniform(0, max_initial_height, num_balls)
    heights = initial_heights
    velocities = np.zeros(num_balls)

    for step in range(num_steps):
        acceleration_due_to_gravity = 9.8
        acceleration = -damping_factor * velocities - acceleration_due_to_gravity
        velocities += acceleration * dt
        heights += velocities * dt

        heights = np.maximum(heights, 0)
        velocities[heights == 0] = -velocities[heights == 0] * damping_factor

        heights_list[:, step] = heights

    return time_steps, heights_list

num_balls = 1_000_0  
max_initial_height = 25.0
num_steps = 750
damping_factor = 0.8
dt = 0.01

start = timeit.default_timer()
time_steps, heights_list = simulate_bouncing_balls_normal(num_balls, max_initial_height, num_steps, damping_factor, dt)
stop = timeit.default_timer()
print('Normal Runtime:', stop - start, 'seconds')

start = timeit.default_timer()
time_steps, heights_list = simulate_bouncing_balls_numpy(num_balls, max_initial_height, num_steps, damping_factor, dt)
stop = timeit.default_timer()
print('Numpy Runtime:', stop - start, 'seconds')

# plt.figure(figsize=(10, 6))
# for i in range(10):
#     plt.plot(time_steps, heights_list[i], label=f'Ball {i+1}')

# plt.title('Bouncing Balls Simulation with Damped Oscillations and Gravity')
# plt.xlabel('Time (s)')
# plt.ylabel('Height (m)')
# plt.legend()
# plt.show()