import os
import re
import json
import subprocess
import pandas as pd

tips = '192.168.7.171'
achilles = '10.100.16.190'
php_pre = '/home/homework/app/aclsphp/models/service/page/acls'
wf_log = '/home/homework/log/aclsphp/aclsphp.log.wf'

def add_log(file:str, info:list, errinfo:str):
    info = ','.join([str(f) for f in info])
    with open(file, 'a+') as file:
        file.write(info + '\t' + errinfo + '\n')

def modify_phpfile(filepath, lineno, content=None):
    with open(filepath, 'r') as file:
        codes = file.readlines()
    if content:
        codes = codes[:lineno] + [content] + codes[lineno:]
        codes = ''.join([line for line in codes])
        with open(filepath, 'w') as file_:
            file_.write(codes)
    else:
        codes = codes[:lineno] + codes[lineno+1:]
        codes = ''.join([line for line in codes])
        with open(filepath, 'w') as file_:
            file_.write(codes)

def json_diff(resp_tips:str, resp_docker:str):
    try:
        resp_tips = json.dumps(json.loads(resp_tips), sort_keys=True).strip()
        resp_docker = json.dumps(json.loads(resp_docker), sort_keys=True).strip()
        return True if (resp_tips == resp_docker) else False
    except:
        return False

def tail_wflog():
    with open(wf_log, 'rb') as file:
        offset = -50
        while True:
            file.seek(offset, 2)
            lines = file.readlines()
            if len(lines) >= 2:
                last_line = lines[-1]
                break
            offset *= 2
        return last_line

def execute_req(line):
    def combine_cmd(line):
        cmd = 'curl -d \''
        cmd += line['params'] + '\' '
        cmd += line['url']
        return cmd

    def run_cmd(cmd):
        try:
            res = subprocess.check_output(cmd, shell=True)
            res = res.decode('utf-8')
            return res
        except:
            add_log('./log/reqerr.log', line.tolist(), 'request error')

    line['url'] = line['url'].replace('127.0.0.1', achilles)
    cmd = combine_cmd(line)
    if pd.notna(line['filepath']):
        line['filepath'] = os.path.join(php_pre, line['filepath'])
        modify_phpfile(line['filepath'], line['lineno'], line['content'])
    resp_docker = run_cmd(cmd)
    if 'n' == line['isnormal']:
        line['url'] = line['url'].replace('127.0.0.1', tips)
        cmd = combine_cmd(line)
        resp_tips = run_cmd(cmd)
        if ('errNo' not in resp_docker.keys()) or ('errNo' in resp_docker.keys() and resp_docker['errNo'] !=0):
            add_log('./log/resp_err.log', line.tolist(), 'response error')
        if not json_diff(resp_tips, resp_docker):
            add_log('./log/bug.log', line.tolist(), 'response different')
    else:
        wf_info = tail_wflog()
        err_info = re.findall(r'err[Mm]sg(.*)', wf_info)
        if line['error'].lower() not in ",".join([err.lower() for err in err_info]):
            add_log('./log/bug.log', line.tolist(), 'errorType mismatch')
    if pd.notna(line['filepath']):
        modify_phpfile(line['filepath'], line['lineno'])


def run_lines(csv_file):
    df = pd.read_csv(csv_file)
    df.apply(execute_req, axis=1)


def main():
    run_lines('./data/cases.csv')


if __name__ == '__main__':
    main()