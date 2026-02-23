import sys


def echo(cmd): 
    return cmd.removeprefix("echo ")


def type(cmd): 
    if "echo" or "type type" or "exit" in cmd: 
        return f"{cmd.removeprefix("type ")} is a shell builtin"


def main():
    exit = False

    while not exit:
        sys.stdout.write("$ ")
        command = input()

        exit = True if command == "exit" else False
        if exit: 
            break
        
        if "invalid_command" in command: 
            print(f"{command}: not found")
        else:
            print(type(command))


        # if "echo" not in command:
        #     print(f"{command}: command not found")
        # else:
        #     print(echo(command))


if __name__ == "__main__":
    main()
