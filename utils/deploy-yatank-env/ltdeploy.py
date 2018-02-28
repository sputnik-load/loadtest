#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import argparse
import subprocess
import logging
import logging.handlers
from time import sleep
import requests
import simplejson as json
from signal import SIGTERM
import ConfigParser
import git
import glob


POLL_INTERVAL = 3
LOG_FILENAME = "ltdeploy.out"
LOG_MAX_BYTES = pow(2, 20)  # 1 MB
LOG_BACKUP_COUNT = 5
YANDEX_TANK = "yandex-tank "  # Пробел тут важен, чтобы отличать yandex-tank и yandex-tank-api-server в списке процессов
YANDEX_TANK_API = "yandex-tank-api-server"
LOCK_DIR = "/data/qa/ltbot/loadtest"
UPDATE_LOCK = "update.lock"
CFG_FILE_NAME = "ltdeploy.cfg"


def init_logger(verbose):
    logger = logging.getLogger("lt_deploy_logger")
    logger.setLevel(logging.DEBUG)
    rfh = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                               maxBytes=LOG_MAX_BYTES,
                                               backupCount=LOG_BACKUP_COUNT)
    templ_str = "%(asctime)s: [%(levelname)s]: %(message)s"
    rfh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(templ_str)
    rfh.setFormatter(formatter)

    sh_out = logging.StreamHandler(sys.stdout)
    sh_err = logging.StreamHandler(sys.stderr)
    sh_out.setFormatter(formatter)
    sh_err.setFormatter(formatter)

    if verbose == 2:
        sh_out.setLevel(logging.DEBUG)
        sh_err.setLevel(logging.ERROR)
    elif verbose == 0:
        sh_out.setLevel(logging.WARNING)
        sh_err.setLevel(logging.ERROR)
    else:
        sh_out.setLevel(logging.INFO)
        sh_err.setLevel(logging.ERROR)

    logger.addHandler(sh_out)
    logger.addHandler(sh_err)
    logger.addHandler(rfh)

    return logger


class YaTankTracker:

    def __init__(self, log):
        self.log = log
        self.yatank_pids = []
        self.yatankapi_pids = []
        self.lock = False
        self.set_lock(False)

    def set_lock(self, enable):
        lock_path = os.path.join(LOCK_DIR, UPDATE_LOCK)
        if enable:
            open(lock_path, "w").close()
            self.log.info("Update lock was created.")
        else:
            if os.path.exists(lock_path):
                os.unlink(lock_path)
                self.log.info("Update lock was removed.")
        self.lock = enable

    def get_plugin_pathes(self, config_name, plugin_names=None):
        config = ConfigParser.ConfigParser()
        config.read(config_name)
        pathes = []
        for sec in config.sections():
            if plugin_names and (not sec in plugin_names):
                continue
            try:
                plugin_path = config.get(sec, "path")
                self.log.info("Plugin path %s was read from %s" % (plugin_path, config_name))
                pathes.append(plugin_path)
            except ConfigParser.NoOptionError:
                self.log.warning("No 'path' option in the config file %s" % config_name)
        return pathes

    def install_plugins(self, path=None, names=None, config=CFG_FILE_NAME,
                        external_script=None):
        def log_working_pids(pidname, pids):
            for pid in pids:
                self.log.info("%s is working now: pid = %s" % (pidname, pid))

        self.set_lock(True)
        while True:
            self.log.info("*******")
            yt = self.is_yatank_working()
            yt_api = self.is_yatank_api_working() and self.is_yatank_api_test()
            log_working_pids(YANDEX_TANK, self.yatank_pids)
            log_working_pids(YANDEX_TANK_API, self.yatankapi_pids)
            if yt or yt_api:
                sleep(POLL_INTERVAL)
            else:
                break

        if self.is_yatank_api_working():
            for pid in self.yatankapi_pids:
                self.log.info("Yandex Tank Api Server will be restarted.")
                os.kill(int(pid), SIGTERM)

        if external_script:
            subprocess.check_call(external_script)
        else:
            plugin_pathes = []
            if path:
                plugin_pathes.append(path)
            else:
                plugin_pathes = self.get_plugin_pathes(config, names)
            for path in plugin_pathes:
                cwdir = os.getcwd()
                os.chdir(path)

                try:
                    self.log.info("Git Pull: %s" % path)
                    repo = git.Repo(path=path)
                    o = repo.remotes.origin
                    fi = o.pull()[0]
                    if fi.old_commit:
                        self.log.info(repo.git.diff(fi.old_commit, fi.commit))
                except Exception, exc:
                    self.log.warning("Git Pull Error: %s" % exc)

                deploy_cmdline = os.path.join(path, "deploy.sh")
                self.log.info("Deploy Command: %s" % deploy_cmdline)
                subprocess.check_call(deploy_cmdline)
                os.chdir(cwdir)

        self.set_lock(False)

    def _check_pids(self, pidname, pids):
        if not pids:
            pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
        result = []
        for pid in pids:
            try:
                cmdline = open(os.path.join("/proc", pid, "cmdline"), "rb").read()
                if re.search("/%s\W" % pidname, cmdline):
                    result.append(pid)
            except IOError: # proc has already terminated
                continue
        return result

    def is_yatank_working(self):
        self.yatank_pids = self._check_pids(YANDEX_TANK,
                                            self.yatank_pids)
        return bool(self.yatank_pids)

    def is_yatank_api_working(self):
        self.yatankapi_pids = self._check_pids(YANDEX_TANK_API,
                                               self.yatankapi_pids)
        return bool(self.yatankapi_pids)

    def is_yatank_api_test(self):
        req = "http://localhost:8888/status"
        resp = requests.get(req)
        if resp.status_code == 200:
            data = json.loads(resp.text)
            for sess_id in data:
                if data[sess_id]["status"] == "running":
                    self.log.info("Test with id=%s is running now." % sess_id)
                    return True
                else:
                    self.log.info("Test with id=%s isn't running now according to the status." % sess_id)
        if glob.glob(os.path.join(LOCK_DIR, "lunapark*.lock")):
            self.log.info("Test hasn't stopped on Yandex Tank API Server yet.")
            return True
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--external",
                        default="",
                        help="Путь к скрипту, который устанавливает плагины.")
    parser.add_argument("-p", "--plugin-path",
                        help="Путь к каталогу с исходниками плагина. При наличии устанавливается плагин только из этого каталога, параметр --config игнорируется.")
    parser.add_argument("-n", "--plugin-names",
                        help="Имена плагинов (перечисляются через запятую) из конфигурационного файла. При наличии устанавливаются только эти плагины.")
    parser.add_argument("-c", "--config", default=CFG_FILE_NAME,
                        help="Имя файла с настройками, лежащего в одном каталоге со скриптом.")
    parser.add_argument("-v", "--verbose", type=int,
                        help="Параметр регулирует уровень подробности логгирования. Варианты: 0, 1, 2. Самый подробный режим - 2.")
    args = parser.parse_args()
    log = init_logger(args.verbose)
    tracker = YaTankTracker(log)
    if args.external:
        tracker.install_plugins(external_script=args.external)
    elif args.plugin_path:
        tracker.install_plugins(path=args.plugin_path)
    elif args.plugin_names:
        tracker.install_plugins(config=args.config,
                                names=args.plugin_names.split(","))
    else:
        tracker.install_plugins(config=args.config)


main()
