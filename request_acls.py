import os
import re
import json
import time
import codecs
import argparse
import subprocess
import pandas as pd

def add_log(file:str, info:list, cmd:str, errinfo:str):
    info = ','.join([str(i) for i in info])
    with open(file, 'a+') as file:
        file.write(info + '\t' + cmd + '\t' + errinfo + '\n')

def json_diff(resp_tips:dict, resp_docker:dict):
    try:
        resp_tips_str = json.dumps(resp_tips, sort_keys=True)
        resp_docker_str = json.dumps(resp_docker, sort_keys=True)
        return True if resp_tips_str == resp_docker_str else False
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
        return last_line.decode('utf-8')

def modify_phpfile(filepath, lineno, content=None):
        with open(filepath, 'r') as file:
            codes = file.readlines()
        if content:
            content = codecs.decode(content, 'unicode_escape')
            codes = codes[:lineno] + [content] + codes[lineno:]   
        else:
            codes = codes[:lineno] + codes[lineno+1:]
        codes = ''.join([line for line in codes])
        with open(filepath, 'w') as file_:
            file_.write(codes)
        time.sleep(3)

def execute_req(line):
    def combine_cmd(line):
        cmd = 'curl -d \''
        cmd += line['params'] + '\' '
        cmd += line['url'] + '?__cache__=0'
        return cmd

    def run_cmd(cmd):
        try:
            res = subprocess.check_output(cmd, shell=True)
            return json.loads(res.decode('utf-8'))
        except:
            add_log('./log/reqerr.log', line.tolist(), cmd, 'request error')
            return {'errNo':0, 'reqerr':1}

    line['url'] = line['url'].replace('127.0.0.1', achilles)
    cmd = combine_cmd(line)
    if pd.notna(line['filepath']):
        line['lineno'] = int(line['lineno'])
        line['filepath'] = os.path.join(php_pre, line['filepath'])
        modify_phpfile(line['filepath'], line['lineno'], line['content'])
    resp_docker = run_cmd(cmd)
    if ('errNo' not in resp_docker.keys()) or ('errNo' in resp_docker.keys() and resp_docker['errNo'] !=0):
            add_log('./log/resp_err.log', line.tolist(), cmd, 'response error(docker)')
    if 'n' == line['isnormal']:
        line['url'] = line['url'].replace('127.0.0.1', tips)
        cmd = combine_cmd(line)
        resp_tips = run_cmd(cmd)
        if ('errNo' not in resp_docker.keys()) or ('errNo' in resp_docker.keys() and resp_docker['errNo'] !=0):
            add_log('./log/resp_err.log', line.tolist(), cmd, 'response error(tips)')
        if ('reqerr' not in resp_tips.keys()) and (not json_diff(resp_tips, resp_docker)):
            add_log('./log/bug.log', line.tolist(), cmd, 'response different')
    else:
        if 'reqerr' not in resp_docker.keys():
            log_info = tail_wflog()
            err_info = re.findall(r'err[Mm]sg(.*)', log_info)
            print(log_info)
            print('*'*50)
            print(err_info)
            print(line['error'])
            print('='*50)
            if line['error'].lower() not in ",".join([err.lower() for err in err_info]):
                add_log('./log/bug.log', line.tolist(), cmd, 'errorType mismatch')
    if pd.notna(line['filepath']):
        modify_phpfile(line['filepath'], line['lineno'])

def run_lines(csv_file):
    df = pd.read_csv(csv_file)
    df.apply(execute_req, axis=1)

def main(csv_file):
    run_lines(os.path.join('./data', csv_file))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', type=str)
    args = parser.parse_args()
    csv_file = args.f

    tips = '192.168.7.171'
    achilles = '10.100.16.190'
    php_pre = '/home/homework/app/aclsphp/models/service/page/acls'
    wf_log = '/home/homework/log/aclsphp/aclsphp.log.wf'

    main(csv_file)