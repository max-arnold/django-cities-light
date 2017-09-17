from __future__ import division, unicode_literals

import collections
import itertools
import os
import datetime
import logging
from argparse import RawTextHelpFormatter
import sys
if sys.platform != 'win32':
    import resource

try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.conf import settings
from django.db import transaction, connection
from django.db import reset_queries, IntegrityError
from django.core.management.base import BaseCommand

import progressbar

from ...exceptions import *
from ...signals import *
from ...settings import *
from ...geonames import Geonames
from ...loading import get_cities_models

Country, Region, City = get_cities_models()


class MemoryUsageWidget(progressbar.widgets.WidgetBase):
    def __call__(self, progress, data):
        if sys.platform != 'win32':
            return '%s kB' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return '?? kB'


def without(d, key):
    new_d = d.copy()
    new_d.pop(key)
    return new_d


class Command(BaseCommand):
    help = """
Download all files in if they were updated or if --force
option was used. Import country data if they were downloaded or if
--force-import was used.
    """.strip()

    logger = logging.getLogger('cities_light')

    def create_parser(self, *args, **kwargs):
        parser = super(Command, self).create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
            default=False, help='Download and import if files are up-to-date.'
        ),
        parser.add_argument('--force-import', action='store_true',
            default=False, help='Import even if files are up-to-date.'
        ),
        parser.add_argument('--no-insert', action='store_true',
            default=False,
            help='Update existing records only'
        ),
        parser.add_argument('--no-update', action='store_true',
            default=False,
            help='Do not update existing records'
        ),
        parser.add_argument('--no-delete', action='store_true',
            default=False,
            help='Do not delete stale records'
        ),
        parser.add_argument('--keep-slugs', action='store_true',
            default=False,
            help='Do not update slugs'
        ),
        parser.add_argument('--progress', action='store_true',
            default=False,
            help='Show progress bar'
        ),

    def progress_init(self):
        """Initialize progress bar."""
        if self.progress_enabled:
            self.progress_widgets = [
                'RAM used: ',
                MemoryUsageWidget(),
                ' ',
                progressbar.ETA(),
                ' Done: ',
                progressbar.Percentage(),
                progressbar.Bar(),
            ]

    def progress_start(self, max_value):
        """Start progress bar."""
        if self.progress_enabled:
            self.progress = progressbar.ProgressBar(
                max_value=max_value,
                widgets=self.progress_widgets
            ).start()

    def progress_update(self, value):
        """Update progress bar."""
        if self.progress_enabled:
            self.progress.update(value)

    def progress_finish(self):
        """Finalize progress bar."""
        if self.progress_enabled:
            self.progress.finish()

    def handle(self, *args, **options):
        """Command handler."""

        if not os.path.exists(DATA_DIR):
            self.logger.info('Creating %s' % DATA_DIR)
            os.mkdir(DATA_DIR)

        install_file_path = os.path.join(DATA_DIR, 'install_datetime')

        self.no_insert = options.get('no_insert', False)
        self.no_purge = options.get('no_purge', False)
        self.keep_slugs = options.get('keep_slugs', False)
        self.progress_enabled = options.get('progress')

        self.progress_init()
        self.progress_start(1)

        dst_countries = {
            c['geoname_id']: without(c, 'geoname_id')
            for c in Country.objects.values()
        }
        dst_regions = {
            r['geoname_id']: without(r, 'geoname_id')
            for r in Region.objects.values()
        }
        dst_cities = {
            c['geoname_id']: without(c, 'geoname_id')
            for c in City.objects.values()
        }

        self.progress_finish()
