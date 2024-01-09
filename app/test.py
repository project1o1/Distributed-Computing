import time


def mul(values):
    result = []
    for value in values:
        for i in range(1, value):
            value *= i

        result.append(value)
    return "done"


user_input = [123456] * 100

start = time.time()
mul(user_input)
end = time.time()

print(end - start)