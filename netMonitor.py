#!/usr/bin/env python3

import subprocess
import time
import json
import psutil
from copy import deepcopy
import os


class NetMonitor:
    """
    sleep_time (float/int) : it determines the time for the app to sleep between checking cycles.
    one_file (bool) :
            [true] :  the app will only care about only one report file
                      and keep replacing it each time the script is restarted.
            [False] : The app will create new report every time the service is restarted.
    
    excluded_apps (list) : list of apps you don't want to appear in the report file.
    """

    def __init__(self, sleep_time=0.5, one_file=True, excluded_apps=None):

        # Setup path of log or logs files.
        self.app_path = os.path.abspath(os.path.dirname(__file__))
        self.dir_log_path = os.path.join(self.app_path, 'app_reports')
        
        # one file or many
        self.one_file = one_file
        
        if not os.path.isdir(self.dir_log_path):
            os.mkdir(self.dir_log_path)

        # Setting up the dict of used ips.
        self.data = {
            "Started Time": time.strftime("%Y-%m-%d %I:%M:%S %p"),
            'Last Updated': '',
            "Tracked apps": list(),
            "UNKNOWN[no name]": {"ips": []},
        }
        if TESTING:
            self.data["UNKNOWN[unrecognized ips]"] = {"got_lines": []}

        if excluded_apps:
            self.data["Excluded apps"] = excluded_apps

        self.list_predefined_data_keys = tuple(self.data.keys())

        # run the app.
        self.run_app(sleep_time)

    def run_app(self, sleep_time):
        report_name = self.report_file()
        
        while True:
            swap_data = deepcopy(self.data)
          
            self.get_data()

            self.update_report_file(swap_data, report_name)
            
            time.sleep(sleep_time)

    
    def update_report_file(self, swapped, report_file_name):
        if swapped != self.data:
            self.data['Last Updated'] = time.strftime("%I:%M:%S %p")

            with open(report_file_name, 'w') as f:
            # don't print excluded data while keeping them .. to make sure to keep unnamed ips organized.

                if self.data.get("Excluded apps", False):
                    #update swapped before report ... to delete from it the excluded apps.
                    swapped = deepcopy(self.data)
                    for k in self.data["Excluded apps"]:
                        if swapped.get(k, False):
                            del swapped[k]
                    json.dump(swapped, f, indent=4)
                else:
                    json.dump(self.data, f, indent=4)
    
    def get_data(self):
        nets_got = psutil.net_connections()
        src_dst_list, no_clear_ips_conn = self.filter_net_psutil(nets_got)

        for src_dst in src_dst_list:
            self.add_to_no_name(src_dst)

        # add Lines that doesn't contain normal ips specified patterns.
        if TESTING:
            for line in no_clear_ips_conn:
                self.add_to_no_clear_ips(str(line))

    def filter_net_psutil(self, net_connections):
        """
        net_connections: List of lines to filter [ips, program name].
        return: tuple 2 lists (src_dst_list, no_clear_ips_conns)
        """
        src_dst_list = []
        no_clear_ips_conns = []

        for conn in net_connections:
            try:

                conn_pid = conn.pid
                program_name = subprocess.Popen(f"ps -o cmd= {conn_pid}",
                                                shell=True, stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE).communicate()
                src, dst = self.get_src_dst(conn)

                program_name = program_name[0].decode().replace("\n", '')
                program_name = ' '.join([c for c in program_name.split(' ') if c and not c.startswith('-')])
                
                if not program_name:
                    raise ValueError
                
                if main_program_name_only:
                    program_name = program_name.split(" ")[0].split('/')[-1]
                
                if program_name_limit and len(program_name) > program_name_limit:
                    program_name = program_name[:program_name_limit]
                
                self.data[program_name] = self.data.get(program_name, {'src': [], 'dst': []})
                
                if program_name not in self.data["Tracked apps"]:
                    self.data["Tracked apps"].append(program_name)

                if src not in self.data[program_name]['src']:
                    self.data[program_name]['src'].append(src)

                if dst not in self.data[program_name]['dst']:
                    self.data[program_name]['dst'].append(dst)

            except ValueError:
                
                if src and dst:
                    src_dst_list.append([src, dst])                    
                else:
                    no_clear_ips_conns.append(conn)

        return src_dst_list, no_clear_ips_conns

    def add_to_no_name(self, src_dst_list):
        line_to_add = src_dst_list[0] + " to " + src_dst_list[1]
        if not self.is_dst_ip_marked_to_app(src_dst_list[1]) and \
                line_to_add not in self.data["UNKNOWN[no name]"]['ips']:
            self.data["UNKNOWN[no name]"]['ips'].append(line_to_add)

    def add_to_no_clear_ips(self, line):
        if line and line not in self.data["UNKNOWN[unrecognized ips]"]['got_lines']:
            self.data["UNKNOWN[unrecognized ips]"]['got_lines'].append(line)

    def is_dst_ip_marked_to_app(self, ip):
        for k in self.data:
            if k in self.list_predefined_data_keys:
                continue
            if ip in self.data[k]['dst']:
                return True
        return False

    @staticmethod
    def get_src_dst(conn):
        src_dst = [None, None]
        if conn.laddr:
            src_dst[0] = conn.laddr.ip
        if conn.raddr:
            src_dst[1] = conn.raddr.ip
        return src_dst

    def report_file(self):
        if self.one_file:
            return os.path.join(self.dir_log_path, "apps_report.json")
        
        return os.path.join(self.dir_log_path, time.strftime("apps_report_%Y_%m_%d-%H_%M_%S.json"))


def get_conf_data(json_conf_file):
    with open(json_conf_file) as jf:
        conf_data = json.load(jf)
    return conf_data



if __name__ == '__main__':

    # read the config file.
    json_conf_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config_file.json')
    data = get_conf_data(json_conf_file_path)
    
    # responsible for activating (add_to_no_clear_ips) func.
    # This will show lines that couldn't capture for them neither true ips nor names [default: False].
    TESTING = data['testing']['data']
    
    # limit of app name captured length, must be true value of (int) to run.
    program_name_limit = data['name_limit']['data']
    
    # choose to only count for main program name like (python, java) for some program [which is not recommended for better monitor]
    main_program_name_only = data['main_program_name_only']['data']
    
    # list of apps to exclude from printing,
    # while keeping processing their data to make sure that non-named ips not related to them.
    excluded = data['excluded']['data']

    # Number of report files, and the sleep time before refreshing.
    one_file = data['one_file']['data']
    sleep_time = data['sleep']['data']
    
    # Run the App
    NetMonitor(one_file=one_file, sleep_time=sleep_time, excluded_apps=excluded)
