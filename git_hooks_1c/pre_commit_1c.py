# -*- coding: utf-8 -*-
import re
import shutil
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List

from parse_1c_build import Parser

from git_hooks_1c import __version__

added_or_modified = re.compile(r'^\s*(?:A|M)\s+"?(?P<rel_name>[^"]*)"?')


def get_added_or_modified_file_paths() -> List[Path]:
    result = []

    try:
        output = subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8')
    except subprocess.CalledProcessError:
        return result

    for line in output.split('\n'):
        if line != '':
            match = added_or_modified.match(line)
            if match:
                added_or_modified_file_path = Path.cwd() / match.group('rel_name')
                if added_or_modified_file_path.name.lower() != 'readme.md':
                    result.append(added_or_modified_file_path)

    return result


def get_for_processing_file_paths(file_paths: List[Path]) -> List[Path]:
    result = []

    for file_path in file_paths:
        if file_path.suffix.lower() in ['.epf', '.erf', '.ert', '.md']:
            result.append(file_path)

    return result


def parse(file_paths: List[Path]) -> List[Path]:
    result = []

    parser = Parser()

    for file_path in file_paths:
        source_dir_path = file_path.parent / (file_path.stem + '_' + file_path.suffix[1:] + '_src')

        if not source_dir_path.exists():
            source_dir_path.mkdir(parents=True)
        else:
            shutil.rmtree(str(source_dir_path), ignore_errors=True)

        parser.parse(file_path, source_dir_path)

        result.append(source_dir_path)

    return result


def add_to_index(dir_paths: List[Path]) -> None:
    for dir_path in dir_paths:
        exit_code = subprocess.check_call(['git', 'add', '--all', str(dir_path)])
        if exit_code != 0:
            exit(exit_code)


def main() -> None:
    argparser = ArgumentParser()
    argparser.add_argument('-v', '--version', action='version', version='%(prog)s, ver. {}'.format(__version__))
    argparser.parse_args()

    added_or_modified_file_paths = get_added_or_modified_file_paths()
    for_processing_file_paths = get_for_processing_file_paths(added_or_modified_file_paths)
    if len(for_processing_file_paths) == 0:
        exit(0)

    for_indexing_source_dir_paths = parse(for_processing_file_paths)
    add_to_index(for_indexing_source_dir_paths)


if __name__ == '__main__':
    sys.exit(main())
