import os
import subprocess


def tokenize(line): 
    symbols = {"'": 'single', '"': 'double'}
    state = 'unquoted'
    current = []
    tokens = []
    
    i = 0
    while i < len(line):  
        char = line[i]

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
                if i + 1 < len(line):
                    if state == 'unquoted':
                        current.append(line[i+1])
                        i += 2
                    elif state == 'single': 
                        current.append(char)
                        i += 1
                    elif state == 'double': 
                        if line[i+1] in ['\\', '"', '`', '$', '\n']: 
                            current.append(line[i+1])
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
                        tokens.append(''.join(current))
                        current = []
                else: 
                    current.append(char)
                i += 1
            else: 
                current.append(char)
                i += 1
    
    if current: # The current list may retain characters after the loop finishes
        tokens.append("".join(current))
    
    return tokens
            

def parse_redirects(tokens): 
    redir_idx = None
    stdout_file_path = None
    stderr_file_path = None
    stdout_mode = 'w'
    stderr_mode = 'w'
    
    # FIXME: Combinations of append operators (e.g. >> and 2>>) are not handled correctly
    # redir_idx may be overwritten when both are present, causing incorrect cmd_tokens slicing

    # Append stdout
    if '>>' in tokens or '1>>' in tokens: 
        redir_symb = '>>' if '>>' in tokens else '1>>'
        redir_idx = tokens.index(redir_symb)
        stdout_file_path = tokens[redir_idx+1]
        stdout_mode = 'a'

    # Append stderr
    if '2>>' in tokens: 
        redir_idx = tokens.index('2>>')
        stderr_file_path = tokens[redir_idx+1]
        stderr_mode = 'a'

    # Both stdout and stderr redirection present
    if '2>' in tokens and ('>' in tokens or '1>' in tokens):  
       redir_symb = '>' if '>' in tokens else '1>'
       stdout_redir_idx = tokens.index(redir_symb)
       stderr_redir_idx = tokens.index('2>')

       stdout_file_path = tokens[stdout_redir_idx+1]
       stderr_file_path = tokens[stderr_redir_idx+1]

       # Slice up to the first redirect operator to exclude redirect syntax from cmd_tokens
       redir_idx = min(stdout_redir_idx, stderr_redir_idx)

    # Redirect stdout only
    if ('>' in tokens or '1>' in tokens) and '2>' not in tokens:   
        redir_symb = '>' if '>' in tokens else '1>'
        redir_idx = tokens.index(redir_symb)
        stdout_file_path = tokens[redir_idx+1]
    
    # Redirect stderr only
    if '2>' in tokens and '>' not in tokens and '1>' not in tokens: 
        redir_idx = tokens.index('2>')
        stderr_file_path = tokens[redir_idx+1]

    # Derive command tokens from everything before the first redirect operator
    if redir_idx is None: 
        cmd_tokens = tokens
    else: 
        cmd_tokens = tokens[0:redir_idx]

    cmd_name = cmd_tokens[0]
    args = ' '.join(cmd_tokens[1:])

    return cmd_tokens, cmd_name, args, stdout_file_path, stdout_mode, stderr_file_path, stderr_mode


def run_echo(args): 
    return ''.join(args), None


def run_pwd(args): 
    return os.getcwd(), None


def run_cd(args):
    dest_path = args
    home_dir = os.environ['HOME']

    if dest_path == '~':
        os.chdir(home_dir)
        return None, None
   
    if os.path.isdir(dest_path):
        os.chdir(dest_path)
        return None, None
    else: 
        return f'{dest_path}: No such file or directory', None
    

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


def run_exit(args):
    return None, EXIT
    

def find_executable(exe_name): 
    # Split PATH into the directories the shell uses to look for executables
    path_env = os.environ['PATH']
    dirs = path_env.split(':')

    for directory in dirs:
        exe_path = os.path.join(directory, exe_name)
        
        # If the file exists and is executable, return the executable name
        if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
            return exe_name
        
    return None


def run_external_program(exe_name, args): 
    result = subprocess.run([exe_name] + args, capture_output=True, text=True)
    return result.stdout, result.stderr


def run_pipeline(tokens): 
    pipe_idx = tokens.index('|')

    cmd1_tokens = tokens[0:pipe_idx]
    cmd2_tokens = tokens[pipe_idx+1:]

    # If the first command is a builtin and the second is not
    if cmd1_tokens[0] in COMMANDS and cmd2_tokens[0] not in COMMANDS: 
        handler = COMMANDS[cmd1_tokens[0]]
        stdout, signal = handler(' '.join(cmd1_tokens[1:]))

        stdout = stdout or ''
        result = subprocess.run(cmd2_tokens, capture_output=True, input=stdout + '\n', text=True) 

        return result.stdout, result.stderr 
    # If the second command is a builtin and the first is not
    elif cmd2_tokens[0] in COMMANDS and cmd1_tokens[0] not in COMMANDS:
           handler = COMMANDS[cmd2_tokens[0]]
           result, signal = handler(' '.join(cmd2_tokens[1:]))

           return result, None
   
    proc1 = subprocess.Popen(cmd1_tokens, stdout=subprocess.PIPE)
    proc2 = subprocess.Popen(cmd2_tokens, stdin=proc1.stdout)

    proc1.stdout.close()
    stdout, stderr = proc2.communicate()

    return stdout, stderr


def get_builtin_completions(text):
    matches = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    return matches


def get_executable_completions(text): 
    path_env = os.environ['PATH']
    dirs = path_env.split(':')
    matches = []

    for directory in dirs: 
        if os.path.isdir(directory):
            for filename in os.listdir(directory): 
                if filename.startswith(text):
                    exe_path = os.path.join(directory, filename)
                    if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
                        matches.append(filename)

    return matches


EXIT = object() # Sentinel value

COMMANDS = {
    'echo': run_echo,
    'pwd': run_pwd,
    'cd': run_cd,
    'type': run_type,
    'exit': run_exit
}
