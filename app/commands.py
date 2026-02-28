import os
import subprocess

EXIT = object()


def run_echo(args): 
    if args.startswith("'") and args.endswith("'"):
        # Preserve the whitspace
        if " " in args: 
            new_str = args[1:len(args)-1]
            return new_str, None
        
        # If two consecutive single quotes exist, remove all single quotes
        if "''" in args: 
            new_str = args.replace("'", "")
            return new_str, None

    if "''" in args:
        new_str = args.replace("'","")
        return new_str, None
    
    if not args.startswith("'") and not args.endswith("'"):
        if "'" not in args:
            spaces = 0
            for char in args: 
                if char == " ": 
                    spaces += 1

                if spaces > 1: 
                    new_str = " ".join(args.split())
                    return new_str, None
                
    return args, None

    
def run_type(args): 
    if args in ("echo", "type", "pwd", "exit"): 
        return f"{args} is a shell builtin", None
    
    path_env = os.environ["PATH"]
    dirs = path_env.split(":")
    filename = args

    for directory in dirs: 
        # Construct the path to the program within this directory
        full_path = os.path.join(directory, filename)
        
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return f"{filename} is {full_path}", None

    return f"{filename}: not found", None


def find_executable(program_name): 
    # Split PATH into the directories the shell uses to look for executables
    path_env = os.environ["PATH"]
    dirs = path_env.split(":")
   
    for directory in dirs:
        full_path = os.path.join(directory, program_name)
        
        # If the path points to an executable file, return the program name
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return program_name
        
    return None


def run_external_program(path, args): 
    result = subprocess.run([path] + args, capture_new_str=True, text=True)
    return result.stdout if result.returncode == 0 else result.stderr


def run_cd(args):
    destination_path = args

    home_dir = os.environ["HOME"]
    if destination_path == "~":
        os.chdir(home_dir)
        return None, None
   
    if os.path.isdir(destination_path):
        os.chdir(destination_path)
        return None, None
    else: 
        return f"{destination_path}: No such file or directory", None
    
        
def run_pwd(args): 
    return os.getcwd(), None


def run_exit(args):
    return None, EXIT


COMMANDS = {"echo": run_echo, "type": run_type, "pwd": run_pwd, "cd": run_cd, "exit": run_exit}
