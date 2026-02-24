import sys


def echo(cmd): 
    return cmd.removeprefix("echo ")


def type(cmd): 
    cmd = cmd.removeprefix("type ")

    if cmd in ("echo", "type", "exit"): 
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

        # Get the command by splitting user input into a list of words and grabbing the first one
        first_word = command.split()[0]
        # If the command is invalid, it won't be in COMMMANDS, so None is returned when attempting to print command below
        cmd = COMMANDS.get(first_word) if first_word in COMMANDS else command

        if cmd not in COMMANDS: 
            print(f"{cmd}: not found")
            break

        print(cmd(command))


if __name__ == "__main__":
    main()
