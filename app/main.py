import sys


def main():
    while True:
        sys.stdout.write("$ ")
        command = input()

        print(command.removeprefix("echo "))


if __name__ == "__main__":
    main()
