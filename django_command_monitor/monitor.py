from django.core.management.base import BaseCommand
from datetime import datetime
import threading
import firebase
from django.conf import settings


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

        self.command_index = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")

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

        self.command_name = subcommand

        return parser

    def execute(self, *args, **options):

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
                self._read_write_log(progress_doc, method='patch')

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
            'exeption_type': None,
            'params': ', '.join([x.replace('-', '').replace('=', '_') for x in self.arguments_passed])
        }

        # Initiate the command log in firebase
        self.initialize_firebase(progress_doc)

        # self._read_write_log(progress_doc, method='post')

        if options['verbosity'] > 1:
            print('Monitoring command: %s' % self.command_id)

        # Run the command
        t1 = threading.Thread(target=_handle_execute, args=(self, progress_doc, results))
        t1.start()

        while t1.isAlive():
            t1.join(10.0)
            if not results[-1][1]:
                progress_doc['status'] = 'RUNNING'
                progress_doc['latest'] = self.get_utc_time
                progress_doc['message'] = 'Command running'
                self._read_write_log(progress_doc, method='patch')
                # time.sleep(10.0)

        if not results[-1][1]:
            progress_doc['status'] = 'FINISHED'
            progress_doc['finished'] = self.get_utc_time
            progress_doc['message'] = 'Command finished'
            self._read_write_log(progress_doc, method='patch')

        return results[-1][0]

    def _read_write_log(self, progress_doc={}, method='get'):
        """
        Write the log of the command to firebase
        :param progress_doc: dictionary
        :param method: string, one of post, patch, delete, etc
        """
        # auth = firebase.FirebaseAuthentication(settings.FIREBASE['API_KEY'], 'kostas@orfium.com')
        app = firebase.FirebaseApplication(settings.FIREBASE_MONITORING['NAME'])

        results = app.get('%s/commands/%s/log' % (settings.FIREBASE_TABLE, str(self.command_id)), None)

        if method == 'get':
            return results
        else:
            if len(results) > 1:
                new_progress = results[:-1]
                new_progress.append(progress_doc)
            else:
                new_progress = [progress_doc]

            app.patch('%s/commands/%s' % (settings.FIREBASE_TABLE, str(self.command_id)),
                      {'log': new_progress})

    def initialize_firebase(self, progress_doc):

        app = firebase.FirebaseApplication(settings.FIREBASE_MONITORING['NAME'])

        results = self._read_write_log(method='get')
        if not results:
            new_results = [progress_doc]
        else:
            new_results = results[::]
            if new_results[-1].get('status', '') == 'RUNNING':
                new_results[-1]['status'] = 'SYSTEM_KILL'
                new_results[-1]['finished'] = self.get_utc_time
            new_results.append(progress_doc)

        app.patch('%s/commands/%s' % (settings.FIREBASE_TABLE, str(self.command_id)),
                  {'log': new_results})
