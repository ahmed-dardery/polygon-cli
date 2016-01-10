#!/usr/bin/env python3
import json
import os
import sys
from getpass import getpass
from sys import argv

import config
import global_vars
import utils
from problem import problemSession
from exceptions import PolygonNotLoginnedError


def load_session():
    try:
        sessionDataJson = open(config.get_session_file_path(), 'r').read()
        sessionData = json.loads(sessionDataJson)
        global_vars.problem = problemSession(config.polygon_url, sessionData["problemId"])
        global_vars.problem.use_ready_session(sessionData)
        return True
    except Exception:
        return False


def save_session():
    sessionData = global_vars.problem.dump_session()
    sessionDataJson = json.dumps(sessionData, sort_keys=True, indent='  ')
    utils.safe_rewrite_file(config.get_session_file_path(), sessionDataJson)


def process_init(argv):
    problem_id = None
    try:
        problem_id = int(argv[0])
    except:
        print_help()
    if config.login:
        print('Using login %s from config' % config.login)
    else:
        print('Enter login:', end=' ')
        sys.stdout.flush()
        config.login = sys.stdin.readline().strip()
    if config.password:
        print('Using password from config')
    else:
        config.password = getpass('Enter password: ')
    global_vars.problem = problemSession(config.polygon_url, problem_id)
    global_vars.problem.create_new_session(config.login, config.password)
    save_session()
    exit(0)


def process_relogin(argv):
    if len(argv) != 0:
        print_help()
    load_session()
    if global_vars.problem.problem_id is None:
        print('No problemId known. Use init instead.')
        exit(0)
    process_init([global_vars.problem.problem_id])


def download_solution(url):
    solutionText = global_vars.problem.send_request('GET', url).text
    return solutionText.replace(' \r\n', '\r\n')


def process_update(argv):
    load_session()
    if global_vars.problem.sessionId is None:
        print('No session known. Use relogin or init first.')
        exit(0)
    solutions = global_vars.problem.get_solutions_list()
    try:
        localSolutions = utils.get_local_solutions()
    except FileNotFoundError:
        localSolutions = []

    localSolutions = set(localSolutions)

    for solution in solutions:
        if len(argv) and solution.name not in argv:
            print('ignoring solution ' + solution.name)
            continue
        solution_text = download_solution(solution.download_link)
        if solution.name not in localSolutions:
            print('New solution found: %s' % solution.name)
            utils.safe_rewrite_file(config.get_solution_path(solution.name), solution)
        else:
            print('Updating solution %s' % solution.name)
            old_path = config.get_download_solution_path(solution.name)
            if not os.path.exists(old_path):
                utils.safe_rewrite_file(old_path, '')
            utils.safe_update_file(old_path, config.get_solution_path(solution.name), solution_text)
    save_session()


def process_send(argv):
    load_session()
    if global_vars.problem.sessionId is None:
        print('No session known. Use relogin or init first.')
        exit(0)
    solutions = global_vars.problem.get_solutions_list()
    solutions_dict = {i.name: i for i in solutions}
    for name in argv:
        if name.startswith(config.solutions_path + '/'):
            name = name[len(config.solutions_path + '/'):]
        if not os.path.exists(config.get_solution_path(name)):
            print('solution %s not found' % name)
            continue
        if name in solutions_dict:
            solution = solutions_dict[name]
            old_path = config.get_download_solution_path(name)
            if not os.path.exists(old_path):
                print('solution %s is outdated: update first' % name)
                continue
            solutionText = download_solution(solution.download_link).splitlines()  # TODO: check some fingerprint
            oldSolutionText = open(old_path, 'r').read().splitlines()
            if solutionText != oldSolutionText:
                print('solution %s is outdated: update first' % name)
                continue
            print('uploading solution %s' % name)
            content = open(config.get_solution_path(name), 'r').read()
            sucsess = global_vars.problem.edit_solution(name, content)
        else:
            content = open(config.get_solution_path(name), 'r').read()
            sucsess = global_vars.problem.updload_solution(name, content)
        if sucsess:
            utils.safe_rewrite_file(config.get_download_solution_path(name), content)


def print_help():
    print("""
polygon-cli Tool for using polygon from commandline
Supported commands:
    init <problemId>\tinitialize tool for problem <problemId>
    relogin\tCreate new polygon http session for same problem
    update\tDownload all solutions from working copy, and merges with local copy
    send <files>\tUpload files as solutions
""")
    exit(1)


def main():
    try:
        if argv[1] == 'init':
            process_init(argv[2:])
        elif argv[1] == 'relogin':
            process_relogin(argv[2:])
        elif argv[1] == 'update':
            process_update(argv[2:])
        elif argv[1] == 'send':
            process_send(argv[2:])
        else:
            print_help()
    except PolygonNotLoginnedError:
        print('Can not login to polygon. Use relogin to update session')


if __name__ == "__main__":
    main()
