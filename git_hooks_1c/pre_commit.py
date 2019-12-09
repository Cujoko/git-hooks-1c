# -*- coding: utf-8 -*-
from pathlib import Path
import subprocess
import sys
from typing import List

import fleep
from loguru import logger
import re
import shutil

from parse_1c_build import Parser

indexed_pattern = re.compile(r'^\s*[AMD]\s+"?(?P<rel_name>[^"]*)"?')
bin_file_suffixes = ['.epf', '.erf', '.ert', '.md']
bin_file_to_check_suffixes = ['.md']

logger.disable(__name__)


def get_indexed_file_fullpaths() -> List[Path]:
    result = []
    try:
        args_au = ['git', 'diff-index',  '--ignore-submodules', '--name-status', '--cached', 'HEAD']
        output = subprocess.check_output(args_au, encoding='utf-8')
    except subprocess.CalledProcessError:
        args_au = ['git', 'status', '--ignore-submodules', '--porcelain']
        output = subprocess.check_output(args_au, encoding='utf-8')
    for line in output.split('\n'):
        if line != '':
            match = indexed_pattern.match(line)
            if match:
                indexed_file_fullpath = Path(match.group('rel_name')).absolute()
                result.append(indexed_file_fullpath)
    return result


def get_for_processing_file_fullpaths(file_fullpaths: List[Path]) -> List[Path]:
    result = []
    for file_fullpath in file_fullpaths:
        if file_fullpath.suffix.lower() in bin_file_suffixes:
            if file_fullpath.suffix.lower() in bin_file_to_check_suffixes:
                with file_fullpath.open('rb') as file:
                    info = fleep.get(file.read(128))
                if info.type == ['document']:
                    result.append(file_fullpath)
            else:
                result.append(file_fullpath)
    return result


def parse(file_fullpaths: List[Path]) -> List[Path]:
    result = []
    parser = Parser()
    for file_fullpath in file_fullpaths:
        source_dir_fullpath = Path(file_fullpath.parent, file_fullpath.stem + '_' + file_fullpath.suffix[1:] + '_src')
        if not source_dir_fullpath.exists():
            source_dir_fullpath.mkdir(parents=True)
        else:
            shutil.rmtree(source_dir_fullpath)
        parser.run(file_fullpath, source_dir_fullpath)
        result.append(source_dir_fullpath)
    return result


def add_to_index(dir_fullpaths: List[Path]) -> None:
    for dir_fullpath in dir_fullpaths:
        args_au = ['git', 'add', '--all', str(dir_fullpath)]
        exit_code = subprocess.check_call(args_au)
        if exit_code:
            raise Exception('some error occured while adding to index', exit_code)


def remove_from_index(file_fullpaths: List[Path]) -> None:
    for file_fullpath in file_fullpaths:
        args_au = ['git', 'rm', '--cached', str(file_fullpath)]
        exit_code = subprocess.check_call(args_au)
        if exit_code:
            raise Exception('some error occured while removing from index', exit_code)


# noinspection PyUnusedLocal
def run(args) -> None:
    logger.enable('cjk-commons')
    logger.enable('parse-1c-build')
    logger.enable(__name__)
    try:
        indexed_file_fullpaths = get_indexed_file_fullpaths()
        if len(indexed_file_fullpaths) == 0:
            logger.info('no added, modified or deleted files')
            sys.exit(1)

        for_processing_file_fullpaths = get_for_processing_file_fullpaths(indexed_file_fullpaths)
        if len(for_processing_file_fullpaths) == 0:
            logger.info('no for processing files')

        for_indexing_source_dir_fullpaths = parse(for_processing_file_fullpaths)
        if len(for_indexing_source_dir_fullpaths) == 0:
            logger.info('no for indexing source dirs')

        add_to_index(for_indexing_source_dir_fullpaths)

        if not args.not_remove_1c_files:
            remove_from_index(for_processing_file_fullpaths)

        indexed_file_fullpaths = get_indexed_file_fullpaths()
        if len(indexed_file_fullpaths) == 0:
            logger.info('no added, modified or deleted files')
            sys.exit(1)

    except Exception as e:
        logger.exception(e)
        sys.exit(1)


def add_subparser(subparsers) -> None:
    decs = 'Pre-commit for 1C:Enterprise files'
    subparser = subparsers.add_parser(
        Path(__file__).stem,
        help=decs,
        description=decs,
        add_help=False
    )
    subparser.set_defaults(func=run)
    subparser.add_argument(
        '-h', '--help',
        action='help',
        help='Show this help message and exit'
    )
    subparser.add_argument(
        '-a', '--not-remove-1c-files',
        action='store_true',
        help='Not remove 1C-files from index'
    )
