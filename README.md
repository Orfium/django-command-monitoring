# Django Command Monitoring

### Description
Django Command Monitoring is a tool that logs the progress of django commands. It writes the progress into FireBase
where you can then read and do whatever you want with the data.

Currently supports:

- Django>=1.11
- Python 2 & 3


## How to install

#### Package installation
Use 
 - `pip install git+https://github.com/siakon89/django-command-monitoring.git`

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
FIREBASE_TABLE = 'monitor-myapp-production'
```

#### How to run with django-command-monitoring
When you are done setting up the only thing you have to do is to include the tool and use `MonitoredCommand` class 
instead of Django's `BaseCommand`

```python
from django_command_monitor import monitor

class Command(monitor.MonitoredCommand):
...
```

## TODO
- [X] Handle the timeouts on FireBase, with at least 3 times retry
- [ ] Create tests
- [ ] Add support for other command classes other than `BaseCommand`