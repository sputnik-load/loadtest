# -*- coding: utf-8 -*-

import slumber
import logging
import glob
import os
import sys
import fnmatch
import argparse
from ConfigParser import RawConfigParser, NoOptionError, NoSectionError

from requests.auth import AuthBase

MAX_FILE_SIZE = 75000000
LOG_LEVEL=logging.INFO
DEFAULT_LOG = 'import_files.log'
REMOTE_DBG = False
files = { 'metrics': 'salts_metrics_*.txt',  # base
    'jm_jtl': 'jmeter_*.jtl',  # base?
    'phout': 'phout_*.log',  # base
    'yt_log': 'tank.log',  # cwd
    'jm_log': 'jmeter_*.log',  # base?
    'yt_conf': 'lunapark_*.lock',  # lock_dir
    'ph_conf': 'phantom_*.conf',  # base
    'modified_jmx': 'modified_*.jmx',  # base?
    'console_log': 'tank-console.log',  # cwd
    'report_txt': 'salts_reports_*.txt',  # base
    'jm_log_2': 'testResults.txt',
}
DEFAULT_SALTS_API="http://<salts-server>/api2/"


class DRFApikeyAuth(AuthBase):
    def __init__(self, apikey):
        self.apikey = apikey

    def __call__(self, r):
        r.headers['Authorization'] = "Token {0}".format(self.apikey)
        return r

def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

def result_dir2session_id(dir):
    if os.path.isdir(dir):
        return os.path.basename(dir.strip('/'))
    elif os.path.isfile(dir):
        return result_dir2session_id(os.path.dirname(dir))
    return None

def salts_store_test_result(result_dir, api):
    log = logging.getLogger(__name__)
    log.info("Import files from {dir} to salts...".format(dir=result_dir))

    session_id = result_dir2session_id(result_dir)
    if not session_id:
        log.error('Wrong session_id = ' + session_id)
        return
    log.info("session_id = " + session_id)

    res = api.testresult.get(session_id=session_id)
    if not res:
        log.error("Test not found, session_id = " + session_id)
        return
    log.info("testresult id = {id}".format(id=res[0]['id']))

    for field, file_path_g in files.items():
        file_path_g = result_dir.rstrip('/') + '/' + file_path_g
        file_path = None
        try:
            file_path = glob.glob(file_path_g)[0]
        except Exception as exc:
            pass
        try:
            if file_path:
                if not res[0][field]:
                    size = os.stat(file_path).st_size
                    if size < MAX_FILE_SIZE:
                        log.info("Saving file '{field}': {path}".format(field=field, path=file_path))
                        with open(file_path) as fp:
                            api.testresult(res[0]['id']).put(files={field: fp})
                    else:
                        log.error("File '{field}' too big - {size} byte(s), MAX = {max}".format(field=field, size=size, max=MAX_FILE_SIZE))
                else:
                    log.warn("File '{field}' already exist: {value}".format(field=field, value=res[0][field]))
            else:
                log.info("File '{field}' not found: {path}".format(field=field, path=file_path_g))
        except Exception as exc:
            log.error("Error saving file to salts: " + str(exc))
            if hasattr(exc, 'content'):
                log.error("Exception content: " + str(exc.content))
            log.error("Exception : " + repr(exc))

def init_logger(logfile):
    log = logging.getLogger('')
    log.setLevel(LOG_LEVEL)

    if logfile:
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s %(message)s"))
        log.addHandler(file_handler)

    log.addHandler(logging.StreamHandler(sys.stdout))


def main():
    parser = argparse.ArgumentParser(description='Import loadtest artifacts (log files) to salts')
    parser.add_argument('-a', '--api', action='store', metavar='API URL',
                        help="Salts API URL (default={api})".format(api=DEFAULT_SALTS_API))
    parser.add_argument('-l', '--log', action='store', default=DEFAULT_LOG, metavar='log file',
                        help="Log file (default={file})".format(file=DEFAULT_LOG))
    parser.add_argument('-c', '--config', action='store', default=None, metavar='common.ini', required=True,
                        help="common.ini with api_key")
    parser.add_argument('-d', '--dir', action='store', default=None, metavar='<artifacts dir>', nargs='+', required=True,
                        help="Artifacts dir, must end with actual session_id (example: -d /data/qa/_results/2015-06-08_19-53-55.2WnRbI)")
    args = parser.parse_args()

    config = RawConfigParser()

    config.read(args.config)
    api_url = config.get('salts', 'api_url')

    cfg_list = find('*-influx_*.ini', '/etc/yandex-tank')
    if len(cfg_list) > 1:
        print "Warning! You have many *-influx_*.ini files in /etc/yandex-tank"
    if len(cfg_list) == 0:
        print "Error: There is no *-influx_*.ini config file in /etc/yandex-tank"
        exit(1)
    config_abspath = cfg_list[0]
    config.read(config_abspath)

    ya_config_path = os.path.expanduser('~/.yandex_tank')
    api_key = ''
    if os.path.exists(ya_config_path):
        ya_config = RawConfigParser()
        ya_config.read(ya_config_path)
        try:
            api_key = ya_config.get('salts', 'api_key')
        except (NoSectionError, NoOptionError):
            print "User config %s hasn't got api_key option." % ya_config_path
    if not api_key:
        try:
            api_key = config.get('salts_report',
                                 'console_default_api_key')
        except (NoSectionError, NoOptionError):
            print "common.ini hasn't got console_default_api_key option."

    if args.api:
        api_url = args.api

    if not hasattr(args, 'dir') or not args.dir:
        parser.print_help()
        exit(1)

    init_logger(args.log)
    log = logging.getLogger(__name__)

    try:
        api = slumber.API(api_url, auth=DRFApikeyAuth(api_key))
        for dir in args.dir:
            salts_store_test_result(dir, api)
        log.info("Import finished")
    except Exception as exc:
        log.error("Error: " + str(exc))
        if hasattr(exc, 'content'):
            log.error("Exception content: " + str(exc.content))
        log.error("Exception : " + repr(exc))


if __name__ == '__main__':
    # append pydev remote debugger
    if REMOTE_DBG:
        # Make pydev debugger works for auto reload.
        # Note pydevd module need to be copied in ...
        try:
            import pydevd as pydevd
            import sys
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
            pydevd.settrace('172.16.98.252', stdoutToServer=True, stderrToServer=True)
        except ImportError:
            sys.stderr.write("Error: " +
                "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
            sys.exit(1)
    main()

