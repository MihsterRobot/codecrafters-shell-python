import os
import subprocess

EXIT = object()


def run_echo(cmd): 
    return cmd, None


def run_type(cmd): 
    if cmd in ("echo", "type", "exit"): 
        return f"{cmd} is a shell builtin", None
    
    path_value = os.environ["PATH"]
    dirs = path_value.split(":")
    filename = cmd

    for dir in dirs: 
        full_path = os.path.join(dir, filename)
        
        if os.path.isfile(full_path):
            if os.access(full_path, os.X_OK):
                return f"{filename} is {full_path}", None

    return f"{filename}: not found", None


def find_executable(program_name): 
    # Grab the PATH environment variable and then split it into a list of directories
    path_value = os.environ["PATH"]
    dirs = path_value.split(":")
   
    for dir in dirs:
        # Generate a full path by appending the program name to the end of the directory
        full_path = os.path.join(dir, program_name)
        
        # If the path points to an executable file, return the program name
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return program_name
        
    return None


def run_external_program(path, args): 
    result = subprocess.run(path + args, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else result.stderr

0
def run_exit(cmd):
    return None, EXIT


COMMANDS = {"echo": run_echo, "type": run_type, "exit": run_exit}
