import setuptools
import codecs
import os.path




def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, rel_path)) as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")




with open('README.md', 'r') as fh:
    long_description = fh.read()

description = (
    'A Python logging handler that sends logs to Redis; later to be a '
    'collection of logging handlers.'
)

setuptools.setup(
    name='python-send-logs-to',
    version=get_version('log_to/__init__.py'),
    author='Armandt van Zyl',
    author_email='armandtvz@gmail.com',
    description=description,
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/armandtvz/python-send-logs-to',
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
    ],
    python_requires=">=3.8, <4",
    install_requires=[
        'redis',
    ],
)
