import time


memory_storage = []


def memory_leak():

    print("Memory leak simulation started.")

    while True:

        memory_storage.append(
            bytearray(10 * 1024 * 1024)
        )

        print(
            "Allocated:",
            len(memory_storage) * 10,
            "MB"
        )

        time.sleep(2)


if __name__ == "__main__":
    memory_leak()