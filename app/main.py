import sys


def run_echo(cmd): 
    return cmd


def run_type(cmd): 
    if cmd in ("echo", "type", "exit"): 
        return f"{cmd} is a shell builtin"
    else: 
        return f"{cmd}: not found"


def run_exit(cmd):
    return "EXIT"


COMMANDS = {"echo": run_echo, "type": run_type, "exit": run_exit}


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

        # Grab the command's arguments 
        command_args = command.removeprefix(cmd + " ")

        # Execute the command and store the return value
        result = handler(command_args)

        if result == "EXIT":
            break
        else: 
            print(result)


if __name__ == "__main__":
    main()
