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
        

def run_exit(cmd):
    return None, EXIT


COMMANDS = {"echo": run_echo, "type": run_type, "exit": run_exit}
