import time

from django.core.management.base import BaseCommand
from datetime import datetime
import threading
import firebase
from django.conf import settings
import sys


class MonitoredCommand(BaseCommand):
    """
    Monitoring the running command.
    """

    def __init__(self):

        super(MonitoredCommand, self).__init__()

        self.command_name = ''
        self.arguments_passed = []
        self.command_id = ''

        # Logging
        self.started = self.get_utc_time
        self.finished = None
        self.alive = True

        # Settings
        self.ping_interval = 10.0  # secs

    @property
    def get_utc_time(self):

        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def run_from_argv(self, argv):

        self.arguments_passed = argv[2:]

        super(MonitoredCommand, self).run_from_argv(argv)

    def create_parser(self, prog_name, subcommand):

        parser = super(MonitoredCommand, self).create_parser(prog_name, subcommand)

        parser.add_argument(
            '--env',
            help='Define the type of the environment: dev, staging, prod.',
            type=str,
            choices=['dev', 'staging', 'prod'],
            dest='environment',
            default='dev'
        )

        parser.add_argument(
            "--disable_monitor",
            action='store_true',
            dest="disable_monitor",
            help="Disable monitoring in this command",
        )

        self.command_name = subcommand

        return parser

    def execute(self, *args, **options):

        if options['disable_monitor']:
            output = super(MonitoredCommand, self).execute(*args, **options)

            return output

        # If in TESTING environment, do not log
        try:
            if settings.TESTING:
                output = super(MonitoredCommand, self).execute(*args, **options)

                return output
        except NameError:
            pass

        # Disable monitoring for the entire project
        try:
            if not settings.FIREBASE_MONITORING_RUN:
                output = super(MonitoredCommand, self).execute(*args, **options)

                return output
        except NameError:
            pass

        # Check to see if the interval ping is set
        interval_ping = 30
        try:
            if settings.FIREBASE_MONITORING_INTERVAL_PING:
               interval_ping = settings.FIREBASE_MONITORING_INTERVAL_PING
        except NameError:
            pass

        results = [['', False], ]

        def _handle_execute(self, progress_doc, results):

            failed = False
            output = None

            try:

                output = super(MonitoredCommand, self).execute(*args, **options)

            except Exception as e:
                print(e)
                failed = True
                progress_doc['status'] = 'FAILED'
                progress_doc['finished'] = self.get_utc_time
                progress_doc['message'] = str(e)
                progress_doc['exeption_type'] = str(sys.exc_info())
                self._write_log(progress_doc)

            results.append([output, failed])

        self.command_id = self.command_name + '__' + '__'.join(
            [x.replace('-', '').replace('=', '_') for x in self.arguments_passed]
        )

        progress_doc = {
            'id': self.command_id,
            'name': self.command_name,
            'status': 'STARTED',
            'started': self.started,
            'latest': self.started,
            'finished': self.finished,
            'message': 'Command started',
            'exception_type': None,
            'params': ', '.join([x.replace('-', '') for x in self.arguments_passed])
        }

        # Initiate the command log in firebase
        self.initialize_firebase(progress_doc)

        if options['verbosity'] > 1:
            print('Monitoring command: %s' % self.command_id)

        # Run the command
        t1 = threading.Thread(target=_handle_execute, args=(self, progress_doc, results))
        t1.start()

        while t1.isAlive():
            t1.join(self.ping_interval)
            if not results[-1][1]:
                progress_doc['status'] = 'RUNNING'
                progress_doc['latest'] = self.get_utc_time
                progress_doc['message'] = 'Command running'
                self._write_log(progress_doc)
                time.sleep(interval_ping)

        if not results[-1][1]:
            progress_doc['status'] = 'FINISHED'
            progress_doc['finished'] = self.get_utc_time
            progress_doc['message'] = 'Command finished'
            self._write_log(progress_doc)

        return results[-1][0]

    def _write_log(self, progress_doc=None):
        """
        Write the log of the command to firebase
        :param progress_doc: dictionary
        """
        results = self._read_write_firebase(method='get',
                                            data=None,
                                            action='%s/commands/%s/log' % (settings.FIREBASE_MONITORING_KEY,
                                                                           str(self.command_id)))
        # Make sure to keep the last 100 logs of the command
        if len(results) >= 100:
            results = results[len(results) - 100:len(results)]

        try:
            if len(results) > 1:
                new_progress = results[:-1]
                new_progress.append(progress_doc)
            else:
                new_progress = [progress_doc, ]

            self._read_write_firebase(method='patch',
                                      data=new_progress,
                                      action='%s/commands/%s' % (settings.FIREBASE_MONITORING_KEY,
                                                                 str(self.command_id)))
        except TypeError:
            self.initialize_firebase(progress_doc)

    def _read_write_firebase(self, method, data, action):
        app = firebase.FirebaseApplication(settings.FIREBASE_MONITORING['NAME'])

        # Make sure the folder we are writing to is monitoring
        action = 'monitoring/' + action

        tries = 3
        results = []

        while tries > 0:
            try:

                if method == 'get':
                    results = app.get(action, None)
                elif method == 'patch':
                    app.patch(action, {'log': data})
                else:
                    raise NotImplementedError('Pssst! You went too deep.')

                break
            except Exception as e:
                print('Firebase had an error. Tries left %d' % tries)
                print(e)
            finally:
                tries -= 1

        return results

    def initialize_firebase(self, progress_doc):

        results = self._read_write_firebase(method='get',
                                            data=None,
                                            action='%s/commands/%s/log' % (settings.FIREBASE_MONITORING_KEY,
                                                                           str(self.command_id)))
        if not results:
            new_results = [progress_doc, ]
        else:
            # Make sure to keep the last 100 logs of the command
            new_results = list(results)
            if len(new_results) >= 100:
                new_results = results[len(results) - 99:len(results)]  # Get the last 99 items

            if (new_results[-1].get('status', '') == 'RUNNING') or (new_results[-1].get('status', '') == 'STARTED'):
                new_results[-1]['status'] = 'SYSTEM_KILL'
                new_results[-1]['finished'] = self.get_utc_time
            new_results.append(progress_doc)

        self._read_write_firebase(method='patch',
                                  data=new_results,
                                  action='%s/commands/%s' % (settings.FIREBASE_MONITORING_KEY, str(self.command_id)))
