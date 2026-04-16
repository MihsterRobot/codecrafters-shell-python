'''Shell command implementations, utilities, and state management.'''

import os
import subprocess
from typing import Literal
from typing import NamedTuple


class RedirectResult(NamedTuple):
    '''Represents the parsed result of a command line with redirect operators.

    Attributes:
        cmd_tokens: The list of tokens representing the command and its arguments,
                    excluding any redirect operators and file paths.
        cmd_name: The name of the command to execute.
        args: The arguments to pass to the command as a single string.
        stdout_file_path: The file path to redirect stdout to,
                          or None if stdout is not redirected.
        stdout_mode: The file mode for stdout redirection ('w' for overwrite,
                     'a' for append).
        stderr_file_path: The file path to redirect stderr to,
                          or None if stderr is not redirected.
        stderr_mode: The file mode for stderr redirection ('w' for overwrite,
                     'a' for append).
    '''
    cmd_tokens: list[str]
    cmd_name: str
    args: str
    stdout_file_path: str | None
    stdout_mode: str
    stderr_file_path: str | None
    stderr_mode: str


class HistoryState:
    '''Tracks the shell's command history and file write state.

    Attributes:
        entries: The list of commands entered by the user.
        last_written_idx: The index of the last entry written to a history file,
                          used to determine which entries are new when appending.
    '''
    def __init__(self):
        self.entries = []
        self.last_written_idx = 0


class JobState:
    '''Tracks the state of background jobs.

    Attributes:
        counter: The number of background jobs started, used to assign
                 sequential job numbers.
    '''
    def __init__(self):
        self.counter = 0


def tokenize(line: str) -> list[str]:
    '''Parse a raw input line into a list of tokens, respecting quoting and escaping rules.

    Handles single quotes (no escaping), double quotes (backslash escapes for
    \\, ", $, `, and newline), and unquoted backslash escaping.

    Args:
        line: The raw input line to tokenize.

    Returns:
        A list of parsed tokens with quotes stripped and escape sequences resolved.
    '''
    symbols = {"'": 'single', '"': 'double'}
    state = 'unquoted'
    current = []
    tokens = []

    i = 0
    while i < len(line):
        char = line[i]

        if state == 'unquoted' and char in symbols:  # Start a quoted segment.
            state = symbols[char]
            i += 1
        elif state != 'unquoted' and char in symbols:  # Complete the quoted segment.
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

    if current:  # The current list may retain characters after the loop finishes.
        tokens.append("".join(current))

    return tokens


def parse_redirects(tokens: list[str]) -> RedirectResult:
    '''Parse redirect operators from a token list and extract the command and file paths.

    Handles >, 1>, 2>, >>, 1>>, 2>>, and combinations of stdout and stderr redirection.

    Args:
        tokens: The list of tokens to parse for redirect operators.

    Returns:
        A RedirectResult containing the command tokens, command name, arguments,
        and redirect file paths and modes.
    '''
    stdout_file_path = None
    stdout_mode = 'w'
    stderr_file_path = None
    stderr_mode = 'w'
    redir_idx = None

    # FIXME: Combinations of append operators (e.g. >> and 2>>) are not handled correctly.
    # redir_idx may be overwritten when both are present, causing incorrect cmd_tokens slicing.

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

       # Slice up to the first redirect operator to exclude redirect syntax from cmd_tokens.
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

    # Derive command tokens from everything before the first redirect operator.
    if redir_idx is None:
        cmd_tokens = tokens
    else:
        cmd_tokens = tokens[0:redir_idx]

    cmd_name = cmd_tokens[0]
    args = ' '.join(cmd_tokens[1:])

    return RedirectResult(cmd_tokens, cmd_name, args, stdout_file_path, stdout_mode, stderr_file_path, stderr_mode)


def run_echo(args: str) -> tuple[str, None]:
    '''Return the provided string back to the terminal.

    Args:
        args: The string to echo.

    Returns:
        A tuple of the echoed string with a trailing newline, and None as the signal.
    '''
    return ''.join(args) + '\n', None


def run_pwd(args: str) -> tuple[str, None]:
    '''Print the current working directory.

    Args:
        args: Unused.

    Returns:
        A tuple of the current working directory path with a trailing newline,
        and None as the signal.
    '''
    return os.getcwd() + '\n', None


def load_history_from_env() -> None:
    '''Load command history from the file specified by the HISTFILE environment variable.

    If HISTFILE is not set or the file does not exist, this function does nothing.
    '''
    # os.environ.get('HISTFILE') is safer than os.environ['HISTFILE'] because it
    # returns None if the variable doesn't exist instead of raising a KeyError.
    hist_file = os.environ.get('HISTFILE')
    if hist_file:
        if os.path.isfile(hist_file):
            with open(hist_file, 'r') as f:
                for line in f:
                    history.entries.append(line.strip())


def save_history_to_env() -> None:
    '''Save the current command history to the file specified by the HISTFILE environment variable.

    If HISTFILE is not set, this function does nothing. Creates the file if it does not exist.
    '''
    hist_file = os.environ.get('HISTFILE')
    if hist_file:
        with open(hist_file, 'w') as f:
            for entry in history.entries:
                f.write(entry + '\n')


def add_to_history(line: str) -> None:
    '''Append a command line to the in-memory history.

    Args:
        line: The command line to append.
    '''
    history.entries.append(line)


def run_history(args: str) -> tuple[str | None, None]:
    '''Display or manage the command history.

    Supports the following usage:
        history         — display all entries
        history <n>     — display the last n entries
        history -r <file> — load entries from a file into history
        history -w <file> — write all entries to a file
        history -a <file> — append new entries since the last -a call to a file

    Args:
        args: The arguments string specifying the operation and optional file path.

    Returns:
        A tuple of the formatted history output and None as the signal,
        or (None, None) for file operations.
    '''
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

    # Generator expression produces formatted history entries one at a time.
    # join() consumes them directly without storing the full list in memory.
    output = '\n'.join(f'   {i}  {cmd}' for i, cmd in enumerate(entries, start))

    return output + '\n', None


def run_cd(args: str) -> tuple[str | None, None]:
    '''Change the current working directory.

    Args:
        args: The destination path. Use '~' to navigate to the home directory.

    Returns:
        A tuple of an error message and None if the directory does not exist,
        or (None, None) on success.
    '''
    dest_path = args
    home_dir = os.environ['HOME']

    if dest_path == '~':
        os.chdir(home_dir)
        return None, None

    if os.path.isdir(dest_path):
        os.chdir(dest_path)
        return None, None

    return f'{dest_path}: No such file or directory' + '\n', None


def run_type(args: str) -> tuple[str, None]:
    '''Identify whether a command is a shell builtin or an executable in PATH.

    Args:
        args: The command name to look up.

    Returns:
        A tuple of the type description string with a trailing newline,
        and None as the signal.
    '''
    if args in COMMANDS:
        return f'{args} is a shell builtin' + '\n', None

    # os.environ['PATH'] and os.environ['HOME'] are used directly because
    # these variables are always expected to be set on a Unix system.
    path_env = os.environ['PATH']
    dirs = path_env.split(':')
    filename = args

    for directory in dirs:
        # Construct the path to the program within this directory.
        full_path = os.path.join(directory, filename)

        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return f'{filename} is {full_path}' + '\n', None

    return f'{filename}: not found' + '\n', None


def start_background_job(args: list[str]) -> subprocess.Popen:
    '''Start a command as a background job without waiting for it to finish.

    Increments the job counter each time a new background job is started.

    Args:
        args: The command and its arguments as a list of tokens.

    Returns:
        The Popen object representing the background process.
    '''
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, text=True)
    job_state.counter += 1
    return proc


def run_jobs(args: str) -> tuple[None, None]:
    '''List active background jobs.

    Args:
        args: Unused.

    Returns:
        (None, None) — not yet implemented.
    '''
    return None, None
    

def run_exit(args: str) -> tuple[None, object]:
    '''Exit the shell.

    Args:
        args: Unused.

    Returns:
        A tuple of None and the EXIT sentinel value to signal the shell to exit.
    '''
    return None, EXIT


def find_executable(exe_name: str) -> str | None:
    '''Search PATH directories for an executable with the given name.

    Args:
        exe_name: The name of the executable to find.

    Returns:
        The executable name if found, or None if not found in any PATH directory.
    '''
    # Split PATH into the directories the shell uses to look for executables.
    path_env = os.environ['PATH']
    dirs = path_env.split(':')

    for directory in dirs:
        exe_path = os.path.join(directory, exe_name)

        # If the file exists and is executable, return the executable name.
        if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
            return exe_name

    return None


def run_external_program(exe_name: str, args: list[str]) -> tuple[str, str]:
    '''Run an external program and capture its stdout and stderr.

    Args:
        exe_name: The name of the executable to run.
        args: The list of arguments to pass to the executable.

    Returns:
        A tuple of the program's stdout and stderr output as strings.
    '''
    result = subprocess.run([exe_name] + args, capture_output=True, text=True)
    return result.stdout, result.stderr


# TODO: Review the pipeline process and structure.
def run_pipeline(tokens: list[str]) -> tuple[str | None, str | None]:
    '''Execute a pipeline of commands connected by | operators.

    Handles pipelines containing any number of commands, including builtin
    commands at any position in the pipeline.

    Args:
        tokens: The full token list including | operators.

    Returns:
        A tuple of the final stdout and stderr output as strings, or None
        if the output was sent directly to the terminal.
    '''
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

    # curr_proc = None is unnecessary because it's always assigned before being used within the loop.
    # prev_proc and builtin_stdout need to be initialized because they're referenced across iterations,
    # while curr_proc is only used within the same iteration it's assigned.

    prev_proc = None
    builtin_stdout = None

    # Iterate over pipeline_cmds and determine if the cmd is a builtin or external.
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
                   if prev_proc.stdout:
                    prev_proc.stdout.close()
                   _, stderr = curr_proc.communicate()
                   return None, stderr
                else: # Previous command was a builtin
                    result = subprocess.run(cmd_toks, input=builtin_stdout, capture_output=True, text=True)
                    return result.stdout, result.stderr

        # If a middle command is a builtin, the previous stdout isn't needed; capture the builtin's stdout.
        if cmd_name in COMMANDS:
            handler = COMMANDS[cmd_name]
            builtin_stdout, _ = handler(' '.join(cmd_toks[1:]))
            prev_proc = None
        else: # External
            # If the previous command was a builtin, pass its output to the current process via stdin.
            # Popen doesn't accept 'input=' directly like subprocess.run; stdin must be written to manually.
            # 'text=True' allows writing strings directly to stdin; otherwise, builtin_stdout would need to be encoded to bytes first.
            if builtin_stdout:
                curr_proc = subprocess.Popen(cmd_toks, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
                if curr_proc.stdin:
                    curr_proc.stdin.write(builtin_stdout)
                    curr_proc.stdin.close()
                prev_proc = curr_proc
                builtin_stdout = None
            elif prev_proc: # If the previous command was external
                curr_proc = subprocess.Popen(cmd_toks, stdin=prev_proc.stdout, stdout=subprocess.PIPE, text=True)
                if prev_proc.stdout: 
                    prev_proc.stdout.close()
                prev_proc = curr_proc

    return None, None


def get_builtin_completions(text: str) -> list[str]:
    '''Return builtin command names that start with the given text.

    Args:
        text: The prefix to match against builtin command names.

    Returns:
        A list of matching builtin command names.
    '''
    matches = [cmd for cmd in COMMANDS if cmd.startswith(text)]
    return matches


def get_executable_completions(text: str) -> list[str]:
    '''Return executable names from PATH directories that start with the given text.

    Args:
        text: The prefix to match against executable names.

    Returns:
        A list of matching executable names.
    '''
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


def get_path_completions(text: str, entry_type: Literal['file', 'dir']) -> list[str]:
    '''Return file or directory paths that match the given text prefix.

    Handles both simple filenames and paths containing directory separators.
    Directories are returned with a trailing '/'.

    Args:
        text: The prefix to match, optionally containing path separators.
        entry_type: Either 'file' to match files or 'dir' to match directories.

    Returns:
        A list of matching file or directory paths.
    '''
    is_match = os.path.isfile if entry_type == 'file' else os.path.isdir
    suffix = '' if entry_type == 'file' else '/'
    matches = []

    if '/' in text:
        directory, prefix = text.rsplit('/', maxsplit=1)
        if os.path.isdir(directory):
            full_path = os.path.join(os.getcwd(), directory)
            for name in os.listdir(full_path):
                if is_match(os.path.join(full_path, name)) and name.startswith(prefix):
                    matches.append(os.path.join(directory, name) + suffix)
    else:
        for name in os.listdir(os.getcwd()):
            if is_match(os.path.join(os.getcwd(), name)) and name.startswith(text):
                matches.append(name + suffix)

    return matches


history = HistoryState()
job_state = JobState()

EXIT = object() # Sentinel value

COMMANDS = {
    'echo': run_echo,
    'pwd': run_pwd,
    'history': run_history,
    'cd': run_cd,
    'type': run_type,
    'jobs': run_jobs,
    'exit': run_exit
}
