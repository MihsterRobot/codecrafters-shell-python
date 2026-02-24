import sys
import os

EXIT = object()
path_value = os.environ["PATH"]


def run_echo(cmd): 
    return cmd, None


def run_type(cmd): 
    if cmd in ("echo", "type", "exit"): 
        return f"{cmd} is a shell builtin", None
    
    dirs = path_value.split(":")
    filename = cmd
    
    for dir in dirs: 
        # Join directory path with filename
        full_path = os.path.join(dir, filename)

        # If file exists
        if os.path.isfile(full_path):
            if os.access(filename, os.X_OK):
                return f"{filename} is {dir}", None
    
    return f"{cmd}: not found", None
        


def run_exit(cmd):
    return None, EXIT


COMMANDS = {"echo": run_echo, "type": run_type, "exit": run_exit}


def main():
    while True:
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
