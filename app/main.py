'''Entry point and main loop for the shell, including tab completion and input handling.'''

import readline

from . import commands as c


def completer(text: str, state: int) -> str | None:
    '''Return a tab completion match for the given text prefix.

    Called repeatedly by readline with incrementing state values until None
    is returned. Completes builtin commands, executables in PATH, filenames,
    and directory names. Builtin and executable completions are skipped when
    text is empty to avoid overwhelming readline with all possible matches.

    Args:
        text: The prefix typed by the user to complete.
        state: The index of the match to return, incremented by readline on each call.

    Returns:
        The matching completion string with a trailing space for files or '/'
        for directories, or None when no more matches are available.
    '''
    # Skip builtin and executable completions when text is empty; returning all matches
    # would overwhelm readline and prevent file/directory completions from taking effect.
    builtin_matches: list[str] = []
    exe_matches: list[str] = []
    if text:
        builtin_matches = c.get_builtin_completions(text)
        exe_matches = c.get_executable_completions(text)

    filename_matches: list[str] = c.get_path_completions(text, 'file')
    directory_matches: list[str] = c.get_path_completions(text, 'dir')
    
    completions: list[str] = builtin_matches + exe_matches + filename_matches + directory_matches

    # readline increments state on each call; use it to index into the completions list.
    # Return None when state reaches or exceeds the number of matches, signaling no more completions.
    if state >= len(completions):
        return None

    # TODO: Check if this can be removed and added to get_path_completions.
    # Directories get a trailing '/' with no space; files get a trailing space.
    suffix: str = '' if completions[state].endswith('/') else ' '

    return completions[state] + suffix


def main() -> None:
    '''Run the main shell loop.

    Initialises readline with tab completion and history, then repeatedly
    reads input, parses it, and dispatches to the appropriate handler.
    Supports background jobs (&), pipelines (|), I/O redirection, builtin
    commands, and external executables. Saves history to HISTFILE on exit.
    '''
    readline.set_completer(completer)
    readline.set_completer_delims(' ')
    readline.parse_and_bind('tab: complete')

    c.load_history_from_env()

    while True:
        c.reap_jobs()

        line = input('$ ')
        c.add_to_history(line)
        tokens = c.tokenize(line)

        if '&' in tokens: 
            proc = c.start_background_job(tokens[:-1])
            print(f'[{c.job_state.jobs[-1].num}] {proc.pid}')
            continue

        if '|' in tokens:
            stdout, stderr = c.run_pipeline(tokens)
            if stdout:
                print(stdout, end='')
            if stderr:
                print(stderr, end='')
            continue

        cmd_tokens, cmd_name, args, stdout_file_path, stdout_mode, stderr_file_path, stderr_mode = c.parse_redirects(tokens)

        if cmd_name in c.COMMANDS:
            handler = c.COMMANDS[cmd_name]
            stdout, signal = handler(args)

            if signal is c.EXIT:
                c.save_history_to_env()
                break

            # Redirect stdout to file if specified, otherwise print to terminal.
            if stdout and stdout_file_path:
                with open(stdout_file_path, stdout_mode) as f:
                    f.write(stdout)
            elif stdout:
                print(stdout, end='')

            # Builtins don't produce stderr, but the file must still be created when 2> is used.
            if stderr_file_path:
                with open(stderr_file_path, stderr_mode) as f:
                    f.write('')

            continue

        exe_name = c.find_executable(cmd_name)
        
        if exe_name is not None:
            stdout, stderr = c.run_external_program(exe_name, cmd_tokens[1:])

            if stdout_file_path:
                with open(stdout_file_path, stdout_mode) as f:
                    f.write(stdout or '')
            elif stdout:
                print(stdout, end='')

            if stderr_file_path:
                with open(stderr_file_path, stderr_mode) as f:
                    f.write(stderr)
            elif stderr:
                print(stderr, end='')

            continue
        else:
            print(f'{cmd_name}: not found')


if __name__ == '__main__':
    main()
