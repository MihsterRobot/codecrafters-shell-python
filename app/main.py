import sys


def echo(cmd):
    return cmd.strip("echo")


def main():
    commands = {"exit": "exit", "echo": echo}

    while True:
        sys.stdout.write("$ ")
        command = input()

        result = commands.get(command)
        if result == "exit": 
            break
        
        print(result)

        # print(f"{command}: command not found")


if __name__ == "__main__":
    main()
