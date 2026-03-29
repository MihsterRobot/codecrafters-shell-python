import readline

from . import commands as c


def completer(text, state):
    builtin_matches = c.get_builtin_completions(text)
    exe_matches = c.get_executable_completions(text)
    filename_matches = c.get_filename_completions(text)
    directory_matches = c.get_directory_completions(text)
    completions = builtin_matches + exe_matches + filename_matches + directory_matches

    # readline increments state on each call; use it to index into the completions list
    # Return None when state reaches or exceeds the number of matches, signaling no more completions
    if state >= len(completions):
        return None
    return completions[state] + ' '


def main():
    readline.set_completer(completer)
    readline.set_completer_delims(' ')
    readline.parse_and_bind('tab: complete')

    c.load_history_from_env()

    while True:
        line = input('$ ')
        c.add_to_history(line)
        tokens = c.tokenize(line)

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

            # Redirect stdout to file if specified, otherwise print to terminal
            if stdout and stdout_file_path:
                with open(stdout_file_path, stdout_mode) as f:
                    f.write(stdout)
            elif stdout:
                print(stdout, end='')

            # Builtins don't produce stderr, but the file must still be created when 2> is used
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
