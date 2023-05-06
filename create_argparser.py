import argparse
import os


def create_parser():
    parser = argparse.ArgumentParser(
        description='Arguments for logging',
    )
    parser.add_argument(
        '-d',
        '--dest_folder',
        type=str,
        metavar='',
        default=os.getenv('LOGS_FOLDER'),
        help='destination folder for bot logs',
    )
    parser.add_argument(
        '-m',
        '--max_bytes',
        type=int,
        metavar='',
        default=os.getenv('LOGS_MAX_SIZE'),
        help='maximum size bot.log file',
    )
    parser.add_argument(
        '-bc',
        '--backup_count',
        type=int,
        metavar='',
        default=os.getenv('LOGS_BACKUP_COUNT'),
        help='bot logs backup counts',
    )
    return parser
