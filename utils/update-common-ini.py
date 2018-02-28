#!/usr/bin/env python

import sys
import git
import os
import re
import glob
import subprocess
import logging.handlers
import ConfigParser
import argparse
from termcolor import colored


LOG_FILENAME = "/tmp/update-common-ini.out"
LOG_MAX_BYTES = pow(2, 20)  # 1 MB
LOG_BACKUP_COUNT = 5


fnull = open(os.devnull, "w")
log = None


def init_logger(verbose):
    level = logging.INFO
    if verbose:
        level = logging.DEBUG
    logger = logging.getLogger("update_common_ini")
    logger.setLevel(level)
    rfh = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                               maxBytes=LOG_MAX_BYTES,
                                               backupCount=LOG_BACKUP_COUNT)
    templ_str = "%(asctime)s: [%(levelname)s]: %(message)s"
    rfh.setLevel(level)
    formatter = logging.Formatter(templ_str)
    rfh.setFormatter(formatter)

    sh_out = logging.StreamHandler(sys.stdout)
    sh_err = logging.StreamHandler(sys.stderr)
    sh_out.setFormatter(formatter)
    sh_err.setFormatter(formatter)

    sh_out.setLevel(level)
    sh_err.setLevel(logging.ERROR)

    logger.addHandler(sh_out)
    logger.addHandler(sh_err)
    logger.addHandler(rfh)

    return logger


def colored_ex(msg, color, kv):
    chunks = re.split("{.*?}", msg)
    templs = re.findall("{(.*?)}", msg)
    i = 0
    message = ""
    for t in templs:
        message += colored(chunks[i], color)
        message += colored(kv[t],
                           color, attrs=["bold"])
        i += 1
    message += colored(chunks[i], color)
    return message


def log_title(hname):
    log.info(colored_ex("*** The {hname} host ***", "yellow",
                        {"hname": hname}))


def log_warning_message(message, param={}):
    log.info(colored_ex(message, "red", param))


def log_info_message(message, param={}):
    log.info(colored_ex(message, "cyan", param))


def log_list(lines):
    for line in lines:
        log.info(str(line))


class RemoteHelper:

    def __init__(self):
        self._host = None
        self._output = None

    def _exec(self, param, save_output=False):
        if save_output:
            try:
                self._output = subprocess.check_output(param)
                return True
            except subprocess.CalledProcessError:
                self._output = None
                return False
        else:
            return not subprocess.call(param)

    def _exists(self, respath):
        if not self._host:
            log.warning("Invalid calling of method RemoteHelper._exists. "
                        "Method is private.")
        log.debug("Checking for the %s exists on %s host."
                  % (respath, self._host))
        param = ["ssh", self._host, "ls", "-l", respath]
        if subprocess.call(param, stdout=fnull):
            log.debug("The %s path is not existed on the %s host."
                      % (respath, self._host))
            return False
        else:
            log.debug("The %s path is existed on the %s host."
                      % (respath, self._host))
            return True

    def create_dir(self, hname, dirpath, sudo=False):
        self._host = hname
        sudo_str = ""
        if sudo:
            sudo_str = "sudo"
        log.debug("The %s directory will be created on the %s host."
                  % (dirpath, hname))
        ok = self._exists(dirpath)
        if not ok:
            param = ["ssh", hname, "%s mkdir -p %s" % (sudo_str, dirpath)]
            ok = self._exec(param)
        if not ok:
            log.debug("The %s directory has not been created on the %s host."
                      % (dirpath, hname))
        self._host = None
        return ok

    def get_file(self, local_destpath, hname, srcpath):
        self._host = hname
        log_param = (srcpath, hname, local_destpath)
        log.debug("The %s file from the %s host will be put "
                  "into the %s file on the localhost."
                  % log_param)
        ok = self._exists(srcpath)
        if ok:
            param = ["scp", "%s:%s" % (hname, srcpath), local_destpath]
            ok = self._exec(param)
        if ok:
            log.debug("The %s file from the %s host was put "
                      "into the %s file on the localhost successfully."
                      % log_param)
        else:
            log.debug("The %s file from the %s host cannot be put "
                      "into the %s file on the localhost."
                      % log_param)
        return ok

    def put_file(self, local_srcpath, hname, destpath, sudo=False):
        self._host = hname
        log.debug("The %s file will be put into the %s file on the %s host."
                  % (local_srcpath, destpath, hname))
        if sudo:
            tmp_path = "/tmp/%s" % os.path.basename(destpath)
            param = ["scp", local_srcpath, "%s:%s" % (hname, tmp_path)]
            ok = self._exec(param)
            if ok:
                ok = self.mv_file(hname, tmp_path, destpath, True)
                self._host = hname
        else:
            param = ["scp", local_srcpath,
                     "%s:%s" % (hname, destpath)]
            ok = self._exec(param)
        if ok:
            log.debug("The %s file was put into the %s file "
                      "on the %s host successfully."
                      % (local_srcpath, destpath, hname))
        else:
            log.debug("The %s file cannot be put "
                      "into the %s file on the %s host."
                      % (local_srcpath, destpath, hname))
        self._host = None
        return ok

    def mv_file(self, hname, srcpath, destpath, sudo=False):
        self._host = hname
        sudo_str = ""
        if sudo:
            sudo_str = "sudo"
        log.debug("The %s file will be move into the %s on the %s host."
                  % (srcpath, destpath, hname))
        ok = self._exists(srcpath)
        if ok:
            param = ["ssh", hname, "%s mv" % sudo_str,
                     srcpath, destpath]
            ok = self._exec(param)
        if ok:
            log.debug("The %s file was moved into "
                      "the %s on the %s host successfully."
                      % (srcpath, destpath, hname))
        else:
            log.debug("The %s file cannot be move into "
                      "the %s on the %s host."
                      % (srcpath, destpath, hname))
        self._host = None
        return ok

    def delete_file(self, hname, filepath, sudo=False):
        self._host = hname
        sudo_str = ""
        if sudo:
            sudo_str = "sudo"
        log.debug("The %s file will be deleted on the %s host."
                  % (filepath, hname))
        ok = self._exists(filepath)
        if ok:
            param = ["ssh", hname, "%s rm -f %s" % (sudo_str, filepath)]
            ok = self._exec(param)
            if ok:
                log.debug("The %s file was deleted on the %s host."
                          % (filepath, hname))
            else:
                log.debug("The %s file cannot be deleted on the %s host."
                          % (filepath, hname))
        self._host = None
        return ok

    def create_link(self, filepath, hname, linkpath, sudo=False):
        self._host = hname
        sudo_str = ""
        if sudo:
            sudo_str = "sudo"
        log.debug("The %s file will be deleted on the %s host."
                  % (filepath, hname))
        ok = self._exists(os.path.basename(filepath))
        if ok:
            param = ["ssh", hname, "%s ln -s %s %s"
                     % (sudo_str, filepath, linkpath)]
            ok = self._exec(param)
            if not ok:
                log.debug("The %s link has not been created on the %s host."
                          % (filepath, hname))
        self._host = None
        return ok

    def list_dir(self, hname, dirpath):
        self._host = hname
        log.debug("Files from the %s directory on the %s host will be listed."
                  % (dirpath, hname))
        ok = self._exists(dirpath)
        if not ok:
            return ok
        param = ["ssh", hname, "find %s -maxdepth 1 -type f" % dirpath]
        output = []
        ok = self._exec(param, True)
        if ok:
            output = self._output.split("\n")[:-1]
        param = ["ssh", hname, "find %s -maxdepth 1 -type l" % dirpath]
        ok = self._exec(param, True)
        if ok:
            output += self._output.split("\n")[:-1]
        self._host = None
        self._output = None
        return output


class IniManager:

    DEFAULTS_INI_FNAME = ".defaultsini"
    CONFIG_COMMON_INI_FNAME = "common-levels.ini"
    ETC_DIRS = {"yandex-tank": "/etc/yandex-tank",
                "yandex-tank-api": "/etc/yandex-tank-api/defaults"}

    def __init__(self, dry_run):
        self._dry_run = dry_run
        self._repo = git.Repo(search_parent_directories=True)
        common_config_path = "%s/%s" \
            % (os.getcwd(), IniManager.CONFIG_COMMON_INI_FNAME)
        self._common_config = ConfigParser.ConfigParser()
        self._common_config.read(common_config_path)
        self._last_commits = self._get_last_commit_numbers()
        self._defaults_path = "%s/%s" \
            % (self._repo.working_dir, IniManager.DEFAULTS_INI_FNAME)
        self._current_commits = self._read_defaults_ini()
        self._rh = RemoteHelper()
        self._common_info = {}

    def update_commits_info(self):
        log_param = {"defname": self._defaults_path}
        if not os.path.exists(self._defaults_path):
            log_warning_message("The script saves commit numbers of "
                                "common ini-files in the {defname} file. "
                                "It should be created.", log_param)
        self._common_info = self._changed_commons()
        if self._common_info["extra"]:
            log_info_message("Following records should be removed "
                             "in the {defname} file:", log_param)
            log_list(self._common_info["extra"])
        if self._common_info["old"]:
            log_info_message("Following records should be updated "
                             "in the {defname} file:", log_param)
            log_list(self._common_info["old"])
        if self._common_info["absent"]:
            log_info_message("Following records should be created "
                             "in the {defname} file:", log_param)
            log_list(self._common_info["absent"])
        if self._dry_run:
            return
        for name in self._common_info["extra"]:
            del(self._current_commits[name])
        for name in self._common_info["old"]:
            self._current_commits[name] = self._last_commits[name]
        for name in self._common_info["absent"]:
            self._current_commits[name] = self._last_commits[name]
        self._write_defaults_ini()

    def update_all(self, hname, yt):
        etc_dirpath = IniManager.ETC_DIRS[yt]
        log_title(hname)
        etc_inifiles = self._rh.list_dir(hname, etc_dirpath)
        log_param = {"hname": hname, "yt_path": etc_dirpath}
        log_info_message("*** Ini-files (and links) in the {yt_path} "
                         "directory on the {hname} host: ***", log_param)
        log_list(etc_inifiles)
        etc_info = self._changed_etc(etc_inifiles, hname)
        if etc_info["extra"]:
            log_info_message("The extra files in the {yt_path} "
                             "on the {hname} host (should be removed):",
                             log_param)
            log_list(etc_info["extra"])
        if etc_info["rename"]:
            log_info_message("Need to rename the following files "
                             "on the {hname} host:", log_param)
            for p in etc_info["rename"]:
                log.info("%s -> %s" % p)
        if etc_info["update"]:
            log_info_message("Need to update (or add) the following files "
                             "on the {hname} host:", log_param)
            for src, dest in etc_info["update"]:
                log.info("%s -> %s:%s/%s"
                         % (src, hname, etc_dirpath, dest))
        if self._dry_run:
            return
        for path in etc_info["extra"]:
            self._rh.delete_file(hname, path, True)
        for srcpath, destpath in etc_info["rename"]:
            self._rh.mv_file(hname, srcpath, destpath, True)
        for srcpath, destpath in etc_info["update"]:
            self._rh.put_file(srcpath, hname,
                              "%s/%s" % (etc_dirpath, destpath), True)
        log.info(colored("All Done.", "green", attrs=["bold"]))

    def clear_etc_dir(self, hname, yt):
        etc_dirpath = IniManager.ETC_DIRS[yt]
        log_title(hname)
        etc_inifiles = self._rh.list_dir(hname, etc_dirpath)
        log_info_message("*** Ini-files (and links) in the {yt_path} "
                         "directory on the {hname} host will be removed: ***",
                         {"hname": hname, "yt_path": etc_dirpath})
        log_list(etc_inifiles)
        if self._dry_run:
            return
        for remote_path in etc_inifiles:
            self._rh.delete_file(hname, remote_path, True)
        log.info(colored("All Done.", "green", attrs=["bold"]))

    def update_hipchat(self, hname, yt, option, value):
        etc_dirpath = IniManager.ETC_DIRS[yt]
        log_title(hname)
        etc_inifiles = self._rh.list_dir(hname, etc_dirpath)
        log_info_message("*** Ini-files (and links) in the {yt_path} "
                         "directory on the {hname} host: ***",
                         {"hname": hname, "yt_path": etc_dirpath})
        log_list(etc_inifiles)
        remote_hc_inipath = ""
        ini_name = ""
        ini_level = ""
        for fpath in etc_inifiles:
            path = os.path.basename(fpath)
            m = re.search("(\d+)-(hipchat.ini)$", path)
            if m:
                remote_hc_inipath = fpath
                (ini_level, ini_name) = m.groups()
                break
        tmp_ini_path = "/tmp/hc.ini"
        if remote_hc_inipath:
            log_info_message("The {hcfile} file found on the {hname} host.",
                             {"hcfile": remote_hc_inipath, "hname": hname})
            ok = self._rh.get_file(tmp_ini_path, hname, remote_hc_inipath)
            if not ok:
                log_warning_message("Error retrieving the {remote_hc_inipath} "
                                    "file copies from the {host} host:",
                                    {"remote_hc_inipath": remote_hc_inipath,
                                     "hname": hname})
                return
        else:
            if not option == "token" or not value:
                log_warning_message("The hipchat.ini file absent "
                                    "in the {etc_dirpath} directory "
                                    "on the {hname} host. "
                                    "The non-empty {option} option is "
                                    "required.",
                                    {"etc_dirpath": etc_dirpath,
                                     "hname": hname, "option": option})
                return
            from shutil import copy
            hipchat_path = self._repo.working_dir
            path = self._common_config.get("hipchat", "path")
            if path:
                hipchat_path += "/%s" % path
            hipchat_path += "/hipchat.ini"
            copy(hipchat_path, tmp_ini_path)
        hc = ConfigParser.ConfigParser()
        hc.read(tmp_ini_path)
        if value:
            hc.set("hipchat", option, value)
            log.info("The hipchat file update: option: %s, value: %s"
                     % (option, value))
        with open(tmp_ini_path, "wb") as configfile:
            hc.write(configfile)
        rep_level = self._common_config.get("hipchat", "level")
        if ini_level and rep_level != ini_level:
            log_info_message("The {remote_path} file from the {hname} "
                             "host should be removed.",
                             {"remote_path": remote_hc_inipath,
                              "hname": hname})
        etc_hc_inipath = "%s/%s-hipchat.ini" % (etc_dirpath, rep_level)
        log_info_message("The {tmp_path} file should be put "
                         "into the {remote_path} on the {hname} host.",
                         {"tmp_path": tmp_ini_path,
                          "remote_path": etc_hc_inipath,
                          "hname": hname})
        if not self._dry_run:
            if remote_hc_inipath and rep_level != ini_level:
                self._rh.delete_file(hname, remote_hc_inipath, True)
            self._rh.put_file(tmp_ini_path, hname, etc_hc_inipath, True)
            log.info(colored("All Done.", "green", attrs=["bold"]))
        os.unlink(tmp_ini_path)

    def _changed_commons(self):
        info = {}
        info["extra"] = []
        info["old"] = []
        info["absent"] = self._last_commits.keys()
        for name in self._current_commits:
            if name in self._last_commits:
                if self._last_commits[name] != self._current_commits[name]:
                    info["old"].append(name)
                info["absent"].remove(name)
            else:
                info["extra"].append(name)
        return info

    def _suffix_valid(self, ini_fname, suffix, hname=None):
        if not suffix:
            return True
        sfx = ["tank-1", "service-3"]
        if suffix in sfx:
            if hname:
                return suffix == hname
            return True
        if not self._common_config.has_option(ini_fname, suffix):
            return False
        return hname in self._common_config.get(ini_fname, suffix).split(",")

    def _changed_etc(self, remote_pathes, hname):
        info = {}
        info["extra"] = []
        info["rename"] = []
        info["update"] = []
        update_names = self._last_commits.keys()
        for path in remote_pathes:
            fname = os.path.basename(path)
            pat = re.compile("(\d+)-([a-zA-Z]+)_?(.*).ini")
            m = pat.search(fname)
            if not m:
                info["extra"].append(path)
                continue
            (level, ini_fname, suffix) = m.groups()
            if not self._suffix_valid(ini_fname, suffix, hname):
                info["extra"].append(path)
                continue
            fullname_ini = ini_fname
            if suffix:
                fullname_ini += "_%s" % suffix
            fullname_ini += ".ini"
            if fullname_ini not in self._last_commits:
                info["extra"].append(path)
                continue
            if self._common_config.has_option(ini_fname, "level"):
                config_level = self._common_config.get(ini_fname, "level")
            else:
                info["extra"].append(path)
                update_names.remove(fullname_ini)
                continue
            if fullname_ini not in self._common_info["old"]:
                if level != config_level:
                    remote_path = "%s/%s" % (os.path.dirname(path),
                                             re.sub("^\d+", config_level,
                                                    fname))
                    info["rename"].append((path, remote_path))
                update_names.remove(fullname_ini)
        for name in update_names:
            if name == "hipchat.ini":
                log_warning_message("The hipchat.ini file should be "
                                    "added with -c update-hipchat.")
                continue
            pat = re.compile("([a-zA-Z]+)_?(.*).ini")
            m = pat.search(name)
            (ini_fname, suffix) = m.groups()
            if not self._suffix_valid(ini_fname, suffix, hname):
                continue
            config_level = self._common_config.get(ini_fname, "level")
            fullname_ini = "%s-%s" % (config_level, ini_fname)
            if suffix:
                fullname_ini += "_%s" % suffix
            fullname_ini += ".ini"
            local_fullname = self._repo.working_dir
            path = self._common_config.get(ini_fname, "path")
            if path:
                local_fullname += "/%s" % path
            local_fullname += "/%s" % name
            info["update"].append((local_fullname, fullname_ini))
        return info

    def _get_last_commit_numbers(self):
        commits = {}
        for section in self._common_config.sections():
            common_dir = "%s/%s" \
                % (self._repo.working_dir,
                   self._common_config.get(section, "path"))
            pathes = glob.glob("%s/%s*.ini"
                               % (common_dir, section))
            for path in pathes:
                lines = self._repo.git.log(path).split("\n")
                if lines and lines[0] and ' ' in lines[0]:
                    commits[os.path.basename(path)] = lines[0].split()[1]
        return commits

    def _write_defaults_ini(self):
        if self._current_commits:
            with open(self._defaults_path, "w") as f:
                f.writelines(
                    "\n".join(["%s %s" % (name, self._current_commits[name])
                               for name in self._current_commits]))

    def _read_defaults_ini(self):
        commits = {}
        lines = []
        if os.path.exists(self._defaults_path):
            with open(self._defaults_path, "r") as f:
                lines = f.read().split("\n")
                for line in lines:
                    items = line.split()
                    commits[items[0]] = items[1]
        return commits


def main():
    cwd = os.getcwd()
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    parser = argparse.ArgumentParser()
    hlp = "Select command. Possible values ('status' is default): " \
          "1. update: updates all common ini files except 'hipchat' " \
          "on the hosts specified in the 't' option; " \
          "2. update-hipchat: updates the option's value in the " \
          "'hipchat' file, the option's name is specified in the 'o' " \
          "option, the new value is specified in the 'v' option; " \
          "3. clear: removes files and links from the /etc/<yt> directory " \
          "on the hosts specified in the 't' option."
    parser.add_argument("-c", "--command",
                        dest="command",
                        choices=["update", "update-hipchat", "clear"],
                        default="update",
                        help=hlp)
    hlp = "Comma-separated names of hosts where " \
          "yandex-tank and yandex-tank-api are worked. " \
          "By default is 'salt-dev,service-3,tank-1,ltt-1'."
    parser.add_argument("-t", "--tanks",
                        dest="tanks",
                        default="salt-dev,service-3,tank-1,ltt-1",
                        help=hlp)
    hlp = "Comma-separated folders to update. " \
          "By default is 'yandex-tank,yandex-tank-api'."
    parser.add_argument("-y", "--yt",
                        dest="yt",
                        choices=["all", "yandex-tank", "yandex-tank-api"],
                        default="yandex-tank,yandex-tank-api",
                        help=hlp)
    hlp = "The option name in the 'hipchat' ini file to update. " \
          "By default the option's name is 'token'."
    parser.add_argument("-o", "--option",
                        dest="option",
                        default="token",
                        help=hlp)
    hlp = "The new value to update in the 'hipchat' ini file " \
          "the option specified in the 'o' option."
    parser.add_argument("-l", "--value",
                        dest="value",
                        help=hlp)
    hlp = "Shows changes in the .defaultsini file and on the " \
          "hosts specified in the 't' option."
    parser.add_argument("-r", "--dry-run",
                        dest="dry_run", action="store_true",
                        default=False,
                        help=hlp)
    parser.add_argument("-v", "--verbose",
                        dest="verbose",
                        action="store_true", default=False,
                        help="Shows debug messages or not.")
    args = parser.parse_args()

    global log
    log = init_logger(args.verbose)
    ini_manager = IniManager(args.dry_run)
    if args.command == "update":
        ini_manager.update_commits_info()
    for t in args.tanks.split(","):
        for y in args.yt.split(","):
            if args.command == "update":
                ini_manager.update_all(t, y)
            elif args.command == "update-hipchat":
                ini_manager.update_hipchat(t, y, args.option, args.value)
            elif args.command == "clear":
                ini_manager.clear_etc_dir(t, y)
    os.chdir(cwd)

if __name__ == "__main__":
    main()
