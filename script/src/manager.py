#!/usr/local/easyops/python/bin/python
# _*_coding: utf-8_*_

import yaml
import os
import logging
import random
import logging.handlers
import yaml
import traceback

# pro
from util import common, cmd_util

restart_cmd = os.environ.get("EASYOPS_COLLECTOR_restart_cmd")
# collect_interval = os.environ.get("EASYOPS_COLLECTOR_collect_interval")
collect_file = os.environ.get("EASYOPS_COLLECTOR_collect_file")
job_id = os.environ.get("EASYOPS_COLLECTOR_job_id")
# intput_tag = os.environ.get("EASYOPS_COLLECTOR_intput_tag")
rsyslog_conf_path = os.environ.get("EASYOPS_COLLECTOR_rsyslog_conf_path")

easyops_server_ip = os.environ.get("EASYOPS_COLLECTOR_easyops_server_ip")
easyops_server_port = os.environ.get("EASYOPS_COLLECTOR_easyops_server_port")
app_id = os.environ.get("EASYOPS_COLLECTOR_app_id")
business_id = os.environ.get("EASYOPS_COLLECTOR_business_id")
host_ip = os.environ.get("EASYOPS_COLLECTOR_host_ip")

rsyslog_conf_tpl = '''
module(load="imfile")

input(type="imfile"
    File="{collect_file}"
    Tag="{input_tag}"
    Ruleset="sendToLogSer_{input_tag}"
    addMetadata="on")

template(name="{template_name}" type="list") {{
    constant(value="{{\\"")

    constant(value="host")
    constant(value="\\": \\"")
    constant(value="{host_ip}")
    constant(value="\\", \\"")

    constant(value="business_id")
    constant(value="\\": \\"")
    constant(value="{business_id}")
    constant(value="\\", \\"")

    constant(value="app_id")
    constant(value="\\": \\"")
    constant(value="{app_id}")
    constant(value="\\", \\"")

    constant(value="log_file_path")
    constant(value="\\": \\"")
    property(name="$!metadata!filename")
    constant(value="\\", \\"")

    constant(value="message")
    constant(value="\\": \\"")
    property(name="msg")
    constant(value="\\"")
    constant(value="}}")
    }}

ruleset(name="sendToLogSer_{input_tag}") {{
    action(type="omfwd"
           target="{easyops_server_ip}"
           port="{easyops_server_port}"
           protocol="tcp"
           template="{template_name}"
           queue.type="LinkedList" 
           queue.size="10000"
           queue.filename="q_{input_tag}"
           queue.highwatermark="9000"
           queue.lowwatermark="50"
           queue.maxdiskspace="500m"
           queue.saveonshutdown="on" 
           action.resumeRetryCount="-1"
           action.reportSuspension="on"
           action.reportSuspensionContinuation="on"
           action.resumeInterval="10")
    stop
}}
'''


def link_conf(src_file, dst_file):
    rcode, output = cmd_util.run_cmd("ln -sf {} {}".format(src_file, dst_file), shell=True)


def restart_rsyslog(cmd="service rsyslog restart"):
    logging.info('restrat rsyslog, cmd is %s', cmd)
    rcode, output = cmd_util.run_cmd(cmd, shell=True)
    logging.info("restart complete, rcode=%s, output=%s", rcode, output)
    return


def run():
    common.log_setup()
    # template_name = "easyops-rsyslog-template-{}-{}".format(job_id, collect_file)
    # work_dir = os.path.join(common.BASE_PATH, "rsyslog_state_file")
    # rsyslog_file_state_file = os.path.join(common.BASE_PATH, "rsyslog_state_file", "rsyslog_file_state_file")

    # if not os.path.exists(work_dir):
    #     os.makedirs(work_dir)

    # IP为空则从配置文件获取
    server_ip = random.choice(common.get_server_ip(easyops_server_ip))
    rsyslog_conf = rsyslog_conf_tpl.format(
        collect_file=collect_file,
        input_tag=job_id,
        template_name=job_id,
        easyops_server_ip=server_ip,
        easyops_server_port=easyops_server_port,
        business_id=business_id,
        app_id=app_id,
        host_ip=host_ip,
    )

    last_conf_md5 = common.get_last_conf_md5()
    logging.info(last_conf_md5)
    logging.info(rsyslog_conf)
    logging.info(common.get_md5(rsyslog_conf))
    if last_conf_md5 == common.get_md5(rsyslog_conf):
        logging.info("last conf md5 not change, return")
        return

    try:
        logging.info('start generate conf')
        common.record_conf_file(common.get_record_conf(
            common.get_md5(rsyslog_conf),
            job_id,
            rsyslog_conf_path,
            restart_cmd
        ))
        common.write_conf(rsyslog_conf, job_id)
        link_conf(common.get_conf_file_path(job_id), rsyslog_conf_path)
        restart_rsyslog(restart_cmd)
        logging.info('end generate conf')
    except Exception as e:
        raise e


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(e.message)
        logging.error(traceback.format_exc())
