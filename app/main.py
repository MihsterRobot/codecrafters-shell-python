import sys


def echo(cmd): 
    return cmd.removeprefix("echo ")


def type(cmd): 
    cmd = cmd.removeprefix("type ")

    if ("echo", "type", "exit") in cmd: 
        return f"{cmd} is a shell builtin"
    else: 
        return f"{cmd}: not found"


COMMANDS = {"echo": echo, "type": type}


def main():
    exit = False

    # Continue looping until user inputs "exit"
    while not exit:
        # Display command prompt and read user input
        sys.stdout.write("$ ")
        command = input()
        
        exit = True if command == "exit" else False
        if exit: 
            break
        
        cmd = COMMANDS.get(command)
        print(cmd(command))
        
        # if "echo" not in command:
        #     print(f"{command}: command not found")
        # else:
        #     print(echo(command))


if __name__ == "__main__":
    main()
