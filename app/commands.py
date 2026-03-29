import os
import subprocess


class HistoryState:
    def __init__(self):
        self.entries = []
        self.last_written_idx = 0


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

    if current:  # The current list may retain characters after the loop finishes
        tokens.append("".join(current))

    return tokens


def parse_redirects(tokens):
    stdout_file_path = None
    stdout_mode = 'w'
    stderr_file_path = None
    stderr_mode = 'w'
    redir_idx = None

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
    return ''.join(args) + '\n', None


def run_pwd(args):
    return os.getcwd() + '\n', None


def load_history_from_env():
    # os.environ.get('HISTFILE') is safer than os.environ['HISTFILE'] because it
    # returns None if the variable doesn't exist instead of raising a KeyError
    hist_file = os.environ.get('HISTFILE')
    if hist_file:
        if os.path.isfile(hist_file):
            with open(hist_file, 'r') as f:
                for line in f:
                    history.entries.append(line.strip())


def save_history_to_env():
    hist_file = os.environ.get('HISTFILE')
    if hist_file:
        with open(hist_file, 'w') as f:
            for entry in history.entries:
                f.write(entry + '\n')


def add_to_history(line):
    history.entries.append(line)


def run_history(args):
    entries = history.entries
    num_entries = len(history.entries)
    start = 0

    if args:
        if args.isdigit():
            n = int(args)
            entries = entries[-n:]
            start = num_entries - n + 1
        else:
            file_path = args.split()[1]
            if args.startswith('-r'):
                with open(file_path, 'r') as f:
                    for line in f:
                        history.entries.append(line.strip())
                return None, None
            elif args.startswith('-w'):
                with open(file_path, 'w') as f:
                    for entry in entries:
                        f.write(entry + '\n')
                return None, None
            elif args.startswith('-a'):
                with open(file_path, 'a') as f:
                    for entry in entries[history.last_written_idx:]:
                        f.write(entry + '\n')
                    history.last_written_idx = num_entries
                return None, None
    else:
        start = 1

    # Generator expression produces formatted history entries one at a time
    # join() consumes them directly without storing the full list in memory
    output = '\n'.join(f'   {i}  {cmd}' for i, cmd in enumerate(entries, start))

    return output + '\n', None


def run_cd(args):
    dest_path = args
    home_dir = os.environ['HOME']

    if dest_path == '~':
        os.chdir(home_dir)
        return None, None

    if os.path.isdir(dest_path):
        os.chdir(dest_path)
        return None, None

    return f'{dest_path}: No such file or directory' + '\n', None


def run_type(args):
    if args in COMMANDS:
        return f'{args} is a shell builtin' + '\n', None

    # os.environ['PATH'] and os.environ['HOME'] are used directly because
    # these variables are always expected to be set on a Unix system
    path_env = os.environ['PATH']
    dirs = path_env.split(':')
    filename = args

    for directory in dirs:
        # Construct the path to the program within this directory
        full_path = os.path.join(directory, filename)

        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return f'{filename} is {full_path}' + '\n', None

    return f'{filename}: not found' + '\n', None


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


# TODO: Review the pipeline process and structure
def run_pipeline(tokens):
    pipeline_cmds = []
    cmd_tokens = []

    for tok in tokens:
        if tok == '|':
            pipeline_cmds.append(cmd_tokens)
            cmd_tokens = []
            continue
        cmd_tokens.append(tok)

    if cmd_tokens:
        pipeline_cmds.append(cmd_tokens)

    prev_proc = None
    builtin_stdout = None
    # curr_proc = None is unnecessary because it's always assigned before being used within the loop
    # prev_proc and builtin_stdout  need to be initialized because they're referenced across iterations,
    # while curr_proc is only used within the same iteration it's assigned

    # Iterate over pipeline_cmds and determine if the cmd is a builtin or external
    for i, cmd_toks in enumerate(pipeline_cmds):
        cmd_name = cmd_toks[0]

        if i == 0: # First command
            if cmd_name in COMMANDS: # Builtin
                handler = COMMANDS[cmd_name]
                builtin_stdout, _ = handler(' '.join(cmd_toks[1:]))
            else: # External
                prev_proc = subprocess.Popen(cmd_toks, stdout=subprocess.PIPE)
            continue
        elif i == len(pipeline_cmds) - 1: # Last command
            if cmd_name in COMMANDS: # Builtin
                handler = COMMANDS[cmd_name]
                stdout, _ = handler(' '.join(cmd_toks[1:]))
                return stdout, None
            else: # External
                if prev_proc: # Previous command was external
                   curr_proc = subprocess.Popen(cmd_toks, stdin=prev_proc.stdout, stderr=subprocess.PIPE, text=True)
                   prev_proc.stdout.close()
                   _, stderr = curr_proc.communicate()
                   return None, stderr
                    # result = subprocess.run(cmd_toks, stdin=prev_proc.stdout, capture_output=True, text=True)
                    # prev_proc.stdout.close()
                else: # Previous command was a builtin
                    result = subprocess.run(cmd_toks, input=builtin_stdout, capture_output=True, text=True)
                    return result.stdout, result.stderr

        # Command is somewhere in the middle

        # If a middle command is a builtin, the previous stdout isn't needed; capture the builtin's stdout
        if cmd_name in COMMANDS:
            handler = COMMANDS[cmd_name]
            builtin_stdout, _ = handler(' '.join(cmd_toks[1:]))
            prev_proc = None
        else: # External
            # If the previous command was a builtin, pass its output to the current process via stdin
            # Popen doesn't accept input= directly like subprocess.run; stdin must be written to manually
            # text=True allows writing strings directly to stdin; otherwise, builtin_stdout would need to be encoded to bytes first
            if builtin_stdout:
                curr_proc = subprocess.Popen(cmd_toks, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
                curr_proc.stdin.write(builtin_stdout)
                curr_proc.stdin.close()
                prev_proc = curr_proc
                builtin_stdout = None
            elif prev_proc: # If the previous command was external
                curr_proc = subprocess.Popen(cmd_toks, stdin=prev_proc.stdout, stdout=subprocess.PIPE, text=True)
                prev_proc.stdout.close()
                prev_proc = curr_proc


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


def get_filename_completions(text):
    matches = []
    if '/' in text:  # Return file path
        directory, prefix = text.rsplit('/', maxsplit=1)
        if os.path.isdir(directory):
            full_path = os.path.join(os.getcwd(), directory)
            for name in os.listdir(full_path):
                if os.path.isfile(os.path.join(directory, name)) and name.startswith(prefix):
                    matches.append(os.path.join(directory, name))
    else:  # Return filename
        for name in os.listdir(os.getcwd()):
            if os.path.isfile(name) and name.startswith(text):
                matches.append(name)
    return matches


def get_directory_completions(text): 
    matches = []
    prefix = text.split()[1]
    # List the contents of the cwd
    for name in os.path.listdir(os.getcwd()):
        # Check if the current name is a directory
        if os.path.isdir(name) and name.startswith(prefix): 
            matches.append(name)
    return matches
    

history = HistoryState()

EXIT = object() # Sentinel value

COMMANDS = {
    'echo': run_echo,
    'pwd': run_pwd,
    'history': run_history,
    'cd': run_cd,
    'type': run_type,
    'exit': run_exit
}
