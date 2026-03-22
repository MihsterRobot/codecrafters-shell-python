import os
import subprocess

EXIT = object() # Sentinel value (flag)


def run_echo(raw_args): 
    return ''.join(raw_args), None
    

def tokenize(raw): 
    current = [] # Accumulate characters for the current argument
    args = [] # Collect completed arguments 
    symbols = {"'": 'single', '"': 'double'}
    state = 'unquoted'
    
    i = 0
    while i < len(raw):  
        char = raw[i]

        if state == 'unquoted' and char in symbols:  # Start a quoted segment
            state = symbols[char]
            i += 1
        elif state != 'unquoted' and char in symbols:  # Complete the quoted segment
            if symbols[char] == state: 
                state = 'unquoted'
                i += 1
            else: 
                current.append(char)
                i += 1
        else: 
            if char == '\\': 
                if i + 1 < len(raw):
                    if state == 'unquoted':
                        current.append(raw[i+1])
                        i += 2
                    elif state == 'single': 
                        current.append(char)
                        i += 1
                    elif state == 'double': 
                        if raw[i+1] in ['\\', '"', '`', '$', '\n']: 
                            current.append(raw[i+1])
                            i += 2
                        else: 
                            current.append(char)
                            i += 1
                else:
                    current.append(char)
                    i += 1
            elif char == ' ': 
                if state == 'unquoted':
                    if current: 
                        args.append(''.join(current))
                        current = []
                else: 
                    current.append(char)
                i += 1
            else: 
                current.append(char)
                i += 1
    
    if current: # The current list may retain characters after the loop finishes
        args.append("".join(current))
    
    return args
            

def parse_redirects(tokens): 
    cmd_tokens = None
    stdout_file_path = None
    stderr_file_path = None
    stdout_mode = 'w'
    stderr_mode = 'w'

    if '2>>' in tokens: 
        redir_idx = tokens.index('2>>')

        cmd_tokens = tokens[0:redir_idx]
        cmd_name = cmd_tokens[0]
        raw_args = ' '.join(cmd_tokens[1:])

        stderr_file_path = tokens[redir_idx+1]
        stderr_mode = 'a'

        return cmd_tokens, cmd_name, raw_args, stdout_file_path, stderr_file_path, stdout_mode, stderr_mode

    if '>>' in tokens or '1>>' in tokens: 
        redir_symb = '>>' if '>>' in tokens else '1>>'
        redir_idx = tokens.index(redir_symb)

        cmd_tokens = tokens[0:redir_idx]
        cmd_name = cmd_tokens[0]
        raw_args = ' '.join(cmd_tokens[1:])

        stdout_file_path = tokens[redir_idx+1]
        stdout_mode = 'a'

        return cmd_tokens, cmd_name, raw_args, stdout_file_path, stderr_file_path, stdout_mode, stderr_mode
    
    if ('>' in tokens or '1>' in tokens) and '2>' not in tokens:   
        redir_symb = '>' if '>' in tokens else '1>'
        redir_idx = tokens.index(redir_symb)

        cmd_tokens = tokens[0:redir_idx]
        cmd_name = cmd_tokens[0]
        raw_args = ' '.join(cmd_tokens[1:])

        stdout_file_path = tokens[redir_idx+1]

        return cmd_tokens, cmd_name, raw_args, stdout_file_path, stderr_file_path, stdout_mode, stderr_mode
    
    # Both stdout and stderr redirection present
    if '2>' in tokens and ('>' in tokens or '1>' in tokens):  
        redir_symb = '>' if '>' in tokens else '1>'
        stdout_redir_idx = tokens.index(redir_symb)
        stderr_redir_idx = tokens.index('2>')

        # Slice up to the first redirect operator to exclude redirect syntax from cmd_tokens
        earliest_idx = min(stdout_redir_idx, stderr_redir_idx)
        cmd_tokens = tokens[0:earliest_idx]
        cmd_name = cmd_tokens[0]
        raw_args = ' '.join(cmd_tokens[1:])

        stdout_file_path = tokens[stdout_redir_idx+1]
        stderr_file_path = tokens[stderr_redir_idx+1]

        return cmd_tokens, cmd_name, raw_args, stdout_file_path, stderr_file_path, stdout_mode, stderr_mode
    
    if '2>' in tokens and '>' not in tokens and '1>' not in tokens: 
        redir_idx = tokens.index('2>')

        cmd_tokens = tokens[0:redir_idx]
        cmd_name = cmd_tokens[0]
        raw_args = ' '.join(cmd_tokens[1:])

        stderr_file_path = tokens[redir_idx+1]

        return cmd_tokens, cmd_name, raw_args, stdout_file_path, stderr_file_path, stdout_mode, stderr_mode

    # No redirect found
    if cmd_tokens is None: 
        cmd_tokens = tokens
        cmd_name = tokens[0]
        raw_args = ' '.join(tokens[1:])
        return cmd_tokens, cmd_name, raw_args, stdout_file_path, stderr_file_path, stdout_mode, stderr_mode


def run_type(args): 
    if args in ('echo', 'type', 'pwd', 'exit'): 
        return f'{args} is a shell builtin', None
    
    path_env = os.environ['PATH']
    dirs = path_env.split(':')
    filename = args

    for directory in dirs: 
        # Construct the path to the program within this directory
        full_path = os.path.join(directory, filename)
        
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return f'{filename} is {full_path}', None
        
    return f'{filename}: not found', None


def find_executable(exe_name): 
    # Split PATH into the directories the shell uses to look for executables
    path_env = os.environ['PATH']
    dirs = path_env.split(':')

    for directory in dirs:
        exe_path = os.path.join(directory, exe_name)
        
        # If the path points to an executable file, return the program name
        if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
            return exe_name
        
    return None


def run_external_program(exe_name, args): 
    result = subprocess.run([exe_name] + args, capture_output=True, text=True)
    return result.stdout, result.stderr


def run_cd(args):
    destination_path = args
    home_dir = os.environ['HOME']

    if destination_path == '~':
        os.chdir(home_dir)
        return None, None
   
    if os.path.isdir(destination_path):
        os.chdir(destination_path)
        return None, None
    else: 
        return f'{destination_path}: No such file or directory', None
    
        
def run_pwd(args): 
    return os.getcwd(), None


def run_exit(args):
    return None, EXIT


COMMANDS = {'echo': run_echo, 'type': run_type, 'pwd': run_pwd, 'cd': run_cd, 'exit': run_exit}    
