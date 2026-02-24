import sys


def run_echo(cmd): 
    print(cmd)


def run_type(cmd): 
    if cmd in ("echo", "type", "exit"): 
        print(f"{cmd} is a shell builtin")
    else: 
        print(f"{cmd}: not found")


COMMANDS = {"echo": run_echo, "type": run_type}


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

        # Get the command by grabbing the first word
        cmd = command.split()[0]

        # No command entered, only invalid input
        if cmd not in COMMANDS: 
            print(f"{cmd}: not found")
            continue

        # Grab the command's handler
        handler = COMMANDS.get(cmd) 

        # Grab the command's arguments
        command_args = command.split(cmd + " ")

        # Execute the command
        handler(command_args)


if __name__ == "__main__":
    main()
