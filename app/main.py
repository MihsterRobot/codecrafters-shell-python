import sys

from . import commands as c


def main():
    while True:
        line = input('$ ')
        tokens = c.tokenize(line)
        cmd_tokens, cmd_name, raw_args, stdout_file_path, stderr_file_path, stdout_mode, stderr_mode = c.parse_redirects(tokens)

        if cmd_name in c.COMMANDS: 
            handler = c.COMMANDS[cmd_name] 
            stdout, signal = handler(raw_args)

            if signal is c.EXIT:
                break

            # Redirect stdout to file if specified, otherwise print to terminal
            if stdout and stdout_file_path: 
                    with open(stdout_file_path, stdout_mode) as f:
                        f.write(stdout + '\n')
            elif stdout: 
                print(stdout)

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
                    f.write(stdout if stdout else '')
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
