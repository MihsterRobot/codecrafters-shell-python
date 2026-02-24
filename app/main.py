import sys
import os

EXIT = object()


def run_echo(cmd): 
    return cmd, None


def run_type(cmd): 
    # Check if the command is a builtin 
    if cmd in ("echo", "type", "exit"): 
        return f"{cmd} is a shell builtin", None
    
    # Extract PATH
    path_value = os.environ["PATH"]

    # Isolate directories
    dirs = path_value.split(":")
    print(dirs)

    filename = cmd

    # Iterate through each directory in the path
    for dir in dirs: 
        # Join directory path with filename
        full_path = os.path.join(dir, filename)

        # If file exists
        if os.path.isfile(full_path):
            if os.access(full_path, os.X_OK):
                return f"{filename} is {full_path}", None
    
    return f"{filename}: not found", None
        

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
