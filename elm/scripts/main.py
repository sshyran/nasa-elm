
from argparse import ArgumentParser
import datetime
import logging
import os

from dask.diagnostics import ProgressBar

from elm.config.cli import add_config_file_argument
from elm.config import DEFAULTS, ConfigParser, executor_context, delayed
from elm.pipeline import pipeline

logger = logging.getLogger(__name__)


def cli(args=None, sys_argv=None):
    if args:
        return args
    parser = ArgumentParser(description="Pipeline classifier / predictor using ensemble and partial_fit methods")
    parser = add_config_file_argument(parser)
    parser.add_argument('--echo-config', action='store_true',
                        help='Output running config as it is parsed')
    if sys_argv:
        return parser.parse_args(sys_argv)
    return parser.parse_args()


def main(args=None, sys_argv=None):
    started = datetime.datetime.now()
    args = cli(args=args, sys_argv=sys_argv)
    err = None
    try:
        config = ConfigParser(args.config)
        if args.echo_config:
            logger.info(str(config))
        dask_executor = getattr(config, 'DASK_EXECUTOR', 'SERIAL')
        dask_scheduler = getattr(config, 'DASK_SCHEDULER', None)
        with executor_context(dask_executor, dask_scheduler) as executor:
            return_values = pipeline(config, executor)
    except Exception as e:
        err = e
        raise
    finally:
        ended = datetime.datetime.now()
        logger.info('Ran from {} to {} ({} '
                    'seconds)'.format(started, ended,
                                      (ended - started).total_seconds()))
        logger.info('There were errors {}'.format(repr(err)) if err else 'ok')
    return 0

if __name__ == "__main__":
    models = main()
