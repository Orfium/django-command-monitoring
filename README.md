# Django Command Monitoring

### Description
Django Command Monitoring is a tool that logs the progress of django commands. It writes the progress into FireBase
where you can then read and do whatever you want with the data. Currently it keeps the log of the last 100 iterations
for each command to avoid overuse of Firebase database.

Currently supports:

- Django>=1.11
- Python 2 & 3


## How to install

#### Package installation
Use 
 - `pip install django-command-monitor`
 - `pip install git+https://github.com/orfium/django-command-monitoring.git`

#### Set up environment
In your django settings file you have to include your FireBase credentials and the FireBase folder that identifies your 
project.

For your FireBase credentials: 
```python
FIREBASE_MONITORING = {
    'API_KEY': '<your FireBase API key>',
    'DOMAIN': '<your FireBase domain>',
    'NAME': '<your FireBase name>',
    'PROJECT_ID': '<your FireBase project id>',
    'SENDER_ID': '<your FireBase sender id>'
}
```

For your FireBase folder:
```python
FIREBASE_MONITORING_KEY = 'monitor-myapp-production'
```

#### How to run with django-command-monitoring
When you are done setting up the only thing you have to do is to include the tool and use `MonitoredCommand` class 
instead of Django's `BaseCommand`

```python
from django_command_monitor import monitor

class Command(monitor.MonitoredCommand):
...
```

#### Settings variables and command inputs
- To disable the command monitoring feature for one command for development runs you can include the input 
`--disable_monitor` as argument in your command

- If you want to disable the monitoring in the testing env, you can add a variable in your testing settings:
`TESTING=True`

- To set the time between each ping set the following variable in settings `FIREBASE_MONITORING_INTERVAL_PING=<secs>`, where `<secs>`
is integer, default is 30 seconds.

- To disable the monitoring for the entire project set the variable in settings `FIREBASE_MONITORING_RUN=False`

## After installation
Your data in FireBase will look like this:

```json
{"monitor-myapp-production":{
           "commands":{
                "<the name of your command with arguments>":{
                        "log":[{
                                      "finished": "<DATETIME>",
                                      "id": "<COMMAND ID>",
                                      "latest": "<DATETIME>",
                                      "message": "<MESSAGE>",
                                      "name": "<COMMAND NAME>",
                                      "params": "<PARAMETERS>",
                                      "started": "<DATETIME>",
                                      "status": "<STATUS>",
                                      "exception_type": "<EXCEPTION AS STRING>"
                                },
                                {...},
                                ...   
                        ]
                },
                "<another command>":{...}
           },
  },
}
```

First of all the name of the FireBase table is the same as the one in settings `FIREBASE_TABLE`.
Under the key `commands` all the commands that have ran under the `monitor.MonitoredCommand` are listed there.

Each command is identified by its name along side with its parameters i.e. when running 
`python manage.py test_command --verbosity=2` the command name is transformed to `test_command__verbosity_2`.

Under each command there is the key `log` that contains a list of all runs of this command with the respective details

For each log it keeps the following data:
- `id`: the identifier of the command(for now is the same as the key of the command mentioned above)
- `name` : The name of the command i.e. when running `python manage.py test_command --verbossity=2` the name is `test_command`
- `status`: the status of the command
    - `STARTED` : The command has just started
    - `RUNNING` : The command currently running
    - `FINISHED` : The command has naturally finished
    - `FAILED` : There was an error when running the command. `message` holds the error message and `exception_type`
    holds the type of the exception
    - `SYSTEM_KILL`: The command is killed by the system i.e. Heroku restarts the dyno based on the given interval. This 
    status is assigned when the same command starts a new cycle and the previous log has status `RUNNING`, meaning the 
    command is forced to stop before writing to FireBase
- `started` : The datetime of when the process started
- `finished`: The datetime of when the process finished. If the process is not yet finished the value is None
- `latest`: The datetime of the latest ping. The process is running under a thread where it pings to FireBase under a 
time interval
- `message`: The message of the failed command
- `exception_type` : The type of the exception when the command failed
- `params`: The parameters of the command i.e. `python manage.py test_command --verbosity=2` goes to `verbosity=2`. 
Multiple parameters are comma separated

Finally the `<DATETIME>` format is as follows: YYYY-MM-DDTHH:MM:SS.(float)Z

## TODO
- [X] Handle the timeouts on FireBase, with at least 3 times retry
- [ ] Add support for other command classes other than `BaseCommand`