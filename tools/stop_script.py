#!/usr/local/easyops/python/bin/python
# _*_coding: utf-8_*_

import os
import subprocess
import yaml

restart_cmd = os.environ.get("EASYOPS_COLLECTOR_restart_cmd")
collector_name = os.environ.get("EASYOPS_COLLECTOR_collector_name")
rsyslog_conf_path = os.environ.get("EASYOPS_COLLECTOR_rsyslog_conf_path")


def load_conf_file(conf_record_file="job_conf.ini"):
    try:
        with open(conf_record_file, "r") as f:
            content = f.read()
            conf = yaml.load(content)
            return conf
    except Exception as e:
        print e.message
        return {}


def run_cmd(command, shell=False, close_fds=True):
    proc = subprocess.Popen(
        command,
        close_fds=close_fds,  # only set to True when on Unix, for WIN compatibility
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    proc.wait()
    output, err = proc.communicate()

    result = err or output
    return proc.returncode, result


def unlink_conf(dst_file):
    return run_cmd("rm -f {}".format(dst_file), shell=True)


def get_conf_file_name(name):
    return os.path.join(name + ".conf")


def restart_rsyslog(cmd="service rsyslog restart"):
    return run_cmd(cmd, shell=True)


def run():
    recorded_conf = load_conf_file()
    file_name = recorded_conf.get("job_id", collector_name)
    real_restart_cmd = recorded_conf.get("restart_cmd", restart_cmd)
    real_rsyslog_conf_path = recorded_conf.get("rsyslog_conf_path", restart_cmd)
    conf_file = os.path.join(real_rsyslog_conf_path, get_conf_file_name(file_name))
    print unlink_conf(conf_file)
    print restart_rsyslog(real_restart_cmd)


if __name__ == "__main__":
    run()