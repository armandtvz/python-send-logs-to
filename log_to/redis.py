import logging
from logging.handlers import MemoryHandler, BufferingHandler
from datetime import datetime, timezone, timedelta

from redis import StrictRedis




class RedisLogMixin:

    def __init__(
        self,
        key=None,
        redis_namespace=None,
        namespace_separator=':',
        host='localhost',
        port=6379,
        password='',
        db=0,
        charset='utf-8',
        cap=100_000,
        attach_date_to_key=True,
        expire_after=timedelta(days=61),
    ):
        """
        :param key:           The Redis key to log to.
        :param host:          Redis instance host. Default is ``localhost``
        :param port:          Redis instance port. Default is ``6379``.
        :param password:      Redis instance password. Default is a blank string.
        :param db:            Redis instance logical database to use
                              Defaults to ``0``.
        :param charset:       Charset to use for Redis connection. Defaults to
                              ``utf-8``.
        :param cap:           The maximum number of elements to retain in the
                              Redis key. Default is 100 000.
        :param attach_date_to_key:  Append the current date to the Redis
                                    key. For example:
                                    ``logging:mykey:2022-12-01+0000``
        :param expire_after:  Must be an integer representing seconds or a
                              Python ``timedelta`` object with a delta equal to
                              or larger than 10 seconds. Set this to ``None``
                              if the logs should never expire. The default is
                              to keep the Redis key for 61 days after creation.
                              If the Redis key for a log already exists and has
                              no expire time; the expiry will be set. If the
                              expiry has already been set; the expire time
                              will not be changed. Redis 7 is required for this
                              because the ``NX`` option is used. If Redis 7 or
                              higher is not used no expiry will be set.
        """
        self.key = key
        self.namespace_separator = namespace_separator
        if isinstance(redis_namespace, str):
            if redis_namespace.endswith(self.namespace_separator):
                redis_namespace = redis_namespace[:-1]

        if not self.key and not redis_namespace:
            redis_namespace = 'logging'

        self.redis_namespace = redis_namespace
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.charset = charset
        self.cap = cap
        self.attach_date_to_key = attach_date_to_key
        self.redis = self.get_connection()
        self.expire_after = expire_after
        self.formatter = logging.Formatter(
            fmt='[{asctime}] {name} | {levelname} | {message}',
            style='{',
        )

        # Do checks for expire_after value
        if self.expire_after:
            if isinstance(self.expire_after, timedelta):
                if self.expire_after.total_seconds() <= 10:
                    raise ValueError(
                        'expire_after timedelta object must have a delta '
                        'equal to or larger than 10 seconds'
                    )

            if not (
                isinstance(self.expire_after, timedelta)
                or isinstance(self.expire_after, int)
            ):
                raise TypeError(
                    'expire_after argument must be of type int '
                    'or a timedelta instance'
                )


    def get_connection(self):
        redis = StrictRedis(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            encoding=self.charset,
            decode_responses=True,
        )
        return redis


    def get_key(self, record):
        key = self.key
        if not key:
            key = record.name

        if self.redis_namespace:
            # For example: "namespace:mykey"
            key = f'{self.redis_namespace}{self.namespace_separator}{key}'

        if self.attach_date_to_key:
            # For example: "namespace:mykey:2023-08-08+0000"
            now = datetime.now(tz=timezone.utc)
            today = now.strftime('%Y-%m-%d%z')
            key = f'{key}{self.namespace_separator}{today}'
        return key


    @property
    def redis_version(self):
        """
        Returns the major version of the Redis instance
        the log handler is connected to.

        :rtype: int
        """
        version = self.redis.info()['redis_version']
        version = version[0]
        try:
            version = int(version)
        except ValueError:
            # If first character of version
            # cannot be cast to an integer;
            # rather play it safe and set
            # the version to 0
            version = 0
        return version


    def _emit(self, record, **kwargs):
        pipe = kwargs.get('pipe', None)
        trim_list = True
        if not pipe:
            pipe = self.redis.pipeline()
        else:
            trim_list = False

        key = self.get_key(record)
        record = self.format(record)
        pipe.lpush(key, record)
        if self.cap and trim_list:
            pipe.ltrim(key, 0, self.cap)

        if (
            self.redis_version >= 7
            and self.expire_after
            and trim_list
        ):
            pipe.expire(key, self.expire_after, nx=True)
        # If expire_after set and Redis version lower than 7
        # redis.exceptions.ResponseError will be thrown when
        # calling pipe.execute(). Therefore, it's important
        # to check the Redis version before running execute()
        if trim_list:
            pipe.execute()




class RedisLogHandler(RedisLogMixin, logging.Handler):
    """
    A logging handler that sends logs to Redis. Uses the Redis list type.
    Other Redis types may be considered in future.

    An example of a log stored in Redis at a key named
    "logging:app:2023-01-01+0000":

    .. code-block::

        [2023-01-01 21:12:54,774] app | ERROR | <detail>
        [2023-01-01 17:12:52,774] app | ERROR | <detail>
        [2023-01-01 11:12:50,774] app | ERROR | <detail>
    """

    def __init__(self, *args, **kwargs):
        logging.Handler.__init__(self)
        super().__init__(*args, **kwargs)


    def emit(self, record, **kwargs):
        """
        Insert the log record at the head of a Redis list by doing an ``LPUSH``.
        """
        try:
            self._emit(record, **kwargs)
        except Exception:
            self.handleError(record)




class RedisBufferedLogHandler(RedisLogMixin, BufferingHandler):

    def __init__(
        self,
        capacity,
        *args,
        **kwargs,
    ):
        self.flushLevel = None
        try:
            self.flushLevel = kwargs.pop('flushLevel')
        except KeyError:
            self.flushLevel = logging.ERROR
        BufferingHandler.__init__(self, capacity)
        super().__init__(*args, **kwargs)


    def shouldFlush(self, record):
        """
        Check for buffer full or a record at the flushLevel or higher.
        """
        return (len(self.buffer) >= self.capacity) or \
                (record.levelno >= self.flushLevel)


    def flush(self):
        try:
            if not self.buffer:
                return
            pipe = self.redis.pipeline()

            for record in self.buffer:
                self._emit(record, pipe=pipe)
            pipe.execute()
            self.buffer.clear()

        except Exception:
            self.handleError(record)
