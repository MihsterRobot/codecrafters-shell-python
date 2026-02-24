import sys

EXIT = object()


def run_echo(cmd): 
    return cmd, None


def run_type(cmd): 
    if cmd in ("echo", "type", "exit"): 
        return f"{cmd} is a shell builtin", None
    else: 
        return f"{cmd}: not found", None


def run_exit(cmd):
    return None, EXIT


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

        # Grab the command's handler and arguments
        handler = COMMANDS[cmd] 
        command_args = command.removeprefix(cmd + " ")

        output, signal = handler(command_args)

        if signal is EXIT:
            break

        if output is not None: 
            print(output)


if __name__ == "__main__":
    main()
