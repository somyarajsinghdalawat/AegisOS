import time


def cpu_stress():

    print("CPU stress started.")

    while True:

        value = 0

        for number in range(1, 1000000):

            value += number ** 2

        if value < 0:
            print(value)

        time.sleep(0.01)


if __name__ == "__main__":
    cpu_stress()