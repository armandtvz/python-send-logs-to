python-send-logs-to
===================
A Python logging handler that sends logs to Redis; later to be a collection
of logging handlers. 




Quickstart
----------

1. Install the package:
   ```
   pip install python-send-logs-to
   ```

1. A code snippet showing an example logging config:

   ```python
   import logging
   from datetime import timedelta

   from log_to.redis import RedisLogHandler


   def configure_logging():
       logger = logging.getLogger('mylogger')
       logger.setLevel(logging.INFO)
       formatter = logging.Formatter(
           fmt='[{asctime}] {name} | {levelname} | {message}',
           style='{',
       )
       # All arguments shown here are default; except for `key`
       handler = RedisLogHandler(
           key='logging:mylogger',
           host='localhost',
           port=6379,
           password='',
           db=0,
           cap=100_000,
           attach_date_to_key=True,
           expire_after=timedelta(days=61), # Only supported for Redis 7 or higher
       )
       handler.setFormatter(formatter)
       logger.addHandler(handler)
       return logger
   ```



Compatiblity
------------
- Compatible with Python 3.8 and above.


Versioning
----------
This project follows [semantic versioning][1] (SemVer).


License and requirements
------------------------
Check the root of the repo for these files.




[//]: # (Links)

[1]: https://semver.org/
