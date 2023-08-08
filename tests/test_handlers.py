import logging
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from log_to.redis import RedisLogHandler, RedisBufferedLogHandler




def get_handler():
    handler = RedisLogHandler(
        # key='logging:test_logger',
        host='localhost',
        port=6379,
        password='',
        cap=100_000,
        attach_date_to_key=True,
        expire_after=timedelta(days=61),
    )
    return handler




class TestRedisLogHandler(unittest.TestCase):

    def test_emit(self):
        logger = logging.getLogger('RedisLogHandler')
        logger.setLevel(logging.INFO)
        handler = get_handler()
        logger.addHandler(handler)
        logger.info('Allo')




class TestRedisBufferedLogHandler(unittest.TestCase):

    def test_flush(self):
        logger = logging.getLogger('RedisBufferedLogHandler')
        logger.setLevel(logging.INFO)
        handler = RedisBufferedLogHandler(
            capacity=100,
            key='test_buffered_logger',
            redis_namespace='logging',
            host='localhost',
            port=6379,
            password='',
            cap=100_000,
            attach_date_to_key=True,
            expire_after=timedelta(days=61),
        )
        logger.addHandler(handler)

        import time
        for i in range(500):
            print(f'Running {i}')
            time.sleep(0.005)
            logger.info('Allo')




if __name__ == '__main__':
    unittest.main()
