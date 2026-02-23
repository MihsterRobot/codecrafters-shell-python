import sys


def main():
    # Map command names to their functionality
    commands = {"exit": "exit", "echo": echo}

    while True:
        sys.stdout.write("$ ")
        command = input()

        print(command.removeprefix("echo"))


if __name__ == "__main__":
    main()
