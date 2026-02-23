import sys


def echo(cmd): 
    return cmd.removeprefix("echo ")


def main():
    exit = False

    while not exit:
        sys.stdout.write("$ ")
        command = input()

        exit = True if command == "exit" else False
        if exit: 
            break

        if "echo" not in command:
            print(f"{command}: command not found")
        else:
            print(echo(command))


if __name__ == "__main__":
    main()
