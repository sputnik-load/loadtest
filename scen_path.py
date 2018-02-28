#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from os.path import realpath, dirname
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description="Скрипт возвращает scenario path.")
    parser.add_argument("-r", "--run-sh", dest="run_sh")
    parser.add_argument("-c", "--config", dest="config")
    parser.add_argument("-s", "--search", dest="search",
                        action="store_true", default=False)
    args = parser.parse_args()

    run_sh_dir = dirname(realpath(args.run_sh))
    if args.search:
        run_sh_dir = run_sh_dir.replace("/search", "")
    config_path = realpath(args.config)
    scenario_path = config_path.replace("%s/" % run_sh_dir, "")

    print scenario_path


if __name__ == "__main__":
    main()



