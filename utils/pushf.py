# -*- coding: utf-8 -*-


import sys
from git import Repo
from argparse import ArgumentParser
from logging import getLogger, StreamHandler, Formatter, INFO


TEST_REPO_PATH = "/data/qa/test_files"


reload(sys)
sys.setdefaultencoding("utf-8")
log = getLogger(__file__)
log.setLevel(INFO)
console_handler = StreamHandler(sys.stdout)
console_handler.setLevel(INFO)
formatter = Formatter("%(asctime)s: [%(levelname)s]: %(message)s")
console_handler.setFormatter(formatter)
log.addHandler(console_handler)


def check_diff(diff):
    if not diff:
        return []
    changed_files = []
    change_types = ["A", "D", "R", "M"]
    for ct in change_types:
        for diff_item in diff.iter_change_type(ct):
            log.info("Diff (%s): %s" % (ct, diff_item.a_path))
            changed_files.append(diff_item.a_path)
    return changed_files

try:
    parser = ArgumentParser(description="Тестовый скрипт для коммита.")
    parser.add_argument("-c", action="store", dest="comment",
                        required=True,
                        help="Комментарий к коммиту")
    args = parser.parse_args()


    repo = Repo(path=TEST_REPO_PATH)
    index = repo.index

    changed_files = check_diff(index.diff(None))
    if changed_files:
        index.add(changed_files)
        log.info("Commit with comment: %s" % args.comment)
        index.commit(args.comment)


    origin = repo.remotes.origin
    log.info("Pull")
    fetch_info = origin.pull()[0]
    log.info("Fetch Info: %s" % fetch_info)
    log.info("Push")
    origin.push()

    log.info("Check Conflicts")

    index = repo.index
    changed_files = check_diff(index.diff(None))
    if changed_files:
        log.warning("Остались неразрешенные конфликты.")
except Exception as ex:
    log.warning("Ошибка: %s. Возможно неразрешенные конфликты." % ex)
