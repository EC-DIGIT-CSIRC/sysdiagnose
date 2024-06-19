import glob
import os
'''

# FIXME Have a look at the interesting evidence first, see which files are there that are not on other devices
- crashes_and_spins folder
  - ExcUserFault file
- crashes_and_spins/Panics subfolder
- summaries/crashes_and_spins.log

Though one as there is not necessary a fixed structure
- first line is json
- rest depends ...

Or perhaps include that in a normal log-parser.
And do the secret magic in the hunting rule
'''

parser_description = "Parsing crashes folder"


def get_log_files(log_root_path: str) -> list:
    log_files_globs = [
        'crashes_and_spins/*.ips'
    ]
    log_files = []
    for log_files_glob in log_files_globs:
        log_files.extend(glob.glob(os.path.join(log_root_path, log_files_glob)))

    return log_files


def parse_path(path: str) -> list | dict:
    files = get_log_files(path)
    print(f"Files: {files}")
    raise NotImplementedError("not implemented yet")
