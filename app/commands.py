import os
import re
import subprocess

EXIT = object()
TOKEN_RE_1 = re.compile(r'"[^"]*"|\'[^\']*\'|[^ \t\'"]+')
# TOKEN_RE_2 = re.compile(r'[\S]+\\[\S]+|[\S]+\\.|\\.|[^ \t]+')


def run_echo(raw_args): 
    args = parse_echo_args(raw_args)
    return " ".join(args), None
    

def preprocess_backslashes(raw):
    # if raw.startswith("'") and raw.endswith("'") or raw.startswith('"') and raw.endswith('"'): 
    #     return raw
    
    # tokens = TOKEN_RE_2.findall(raw)

    result = raw
    prev = ""

    for char in raw: 
        if char == "\\" and prev != "\\": 
            # Handle nonliteral backslashes
            prev = char
            result = result.replace("\\", "")
        else: 
            prev = char

    # Whitespace inside quotes needs to be preserved
    if result.startswith("'") and result.endswith("'") or result.startswith('"') and result.endswith('"'): 
        result = [space.replace(" ", "{{SPACE}}") for space in result]
    
    return "".join(result)
    
 
def parse_echo_args(raw):
    raw = preprocess_backslashes(raw)
    # print("RAW:", raw) # Debugging
    tokens = TOKEN_RE_1.findall(raw)
    # print("TOKENS:", tokens) # Debugging
    args = []
    current = []

    # Track where each token came from
    positions = []
    idx = 0
    for tok in tokens: 
        start = raw.find(tok, idx) 
        positions.append(start)
        idx = start + len(tok)

    # Iterate over tokens with their index so we can look at the next token when needed
    for i, tok in enumerate(tokens):
        # Strip quotes
        if tok.startswith("'") and tok.endswith("'"):
            piece = tok[1:-1]
        elif tok.startswith('"') and tok.endswith('"'):
            piece = tok[1:-1]
        else:
            piece = tok

        current.append(piece)

        # Determine if the next token is separated by whitespace
        if i + 1 < len(tokens):
            end_of_tok = positions[i] + len(tok)
            start_of_next = positions[i+1]

            # Nonadjacent tokens belong to different arguments 
            if any(char.isspace() for char in raw[end_of_tok:start_of_next]):
                args.append("".join(current))
                current = []
    
    if current: 
        args.append("".join(current))

    args = [arg.replace("{{SPACE}}", " ") for arg in args]

    return args


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
    result = subprocess.run([path] + args, capture_output=True, text=True)
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
