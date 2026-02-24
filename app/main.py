import sys


def run_echo(cmd): 
    print(cmd)


def run_type(cmd): 
    if cmd in ("echo", "type", "exit"): 
        print(f"{cmd} is a shell builtin")
    else: 
        print(f"{cmd}: not found")


def exit():
    sys.exit(0)


COMMANDS = {"echo": run_echo, "type": run_type, "exit": exit}


def main():
    # Continue looping until user inputs "exit"
    while True:
        # Display command prompt and read user input
        sys.stdout.write("$ ")
        command = input()
        
        # Get the command by grabbing the first word
        cmd = command.split()[0]

        # No command entered, only invalid input
        if cmd not in COMMANDS: 
            print(f"{cmd}: not found")
            continue

        # Grab the command's handler
        handler = COMMANDS.get(cmd) 

        if cmd == "exit":
            handler()

        # Grab the command's arguments 
        command_args = command.removeprefix(cmd + " ")

        # Execute the command
        handler(command_args)


if __name__ == "__main__":
    main()
