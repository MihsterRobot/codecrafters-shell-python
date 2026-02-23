import sys


def echo(cmd): 
    return cmd.removeprefix("echo ")


def main():
    while True:
        sys.stdout.write("$ ")
        command = input()

        if "echo" not in command:
            print(f"{command}: command not found")
        else:
            print(echo(command))


if __name__ == "__main__":
    main()
