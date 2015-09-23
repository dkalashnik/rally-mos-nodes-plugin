import ConfigParser
import cStringIO
import logging
import socket

from nodes import exceptions
from nodes.host_actions import base

logger = logging.getLogger(__name__)


class GeneralActionsClient(base.BaseHostActionsClient):
    @property
    def hostname(self):
        command = 'hostname'
        return self.transport.exec_command(command).strip()

    def get_file_content(self, filename):
        command = 'cat %s' % filename
        ret_code, output, stderr = self.transport.exec_sync(command)
        if ret_code is not 0:
            raise exceptions.SSHCommandFailed(command=command,
                                              host=self.hostname,
                                              stderr=stderr)
        return output

    def get_date(self):
        return self.transport.exec_command("date")

    def get_ini_config(self, filename):
        data = self.get_file_content(filename)
        configfile = cStringIO.StringIO(data)
        config = ConfigParser.ConfigParser()
        config.readfp(configfile)
        return config

    def graceful_reboot(self):
        logger.info("Grace reboot node: {0}".format(self.hostname))
        self.transport.exec_command("nohup reboot >/dev/null &")

    def force_reboot(self):
        logger.info("Force reboot node: {0}".format(self.hostname))
        self.transport.exec_command("reboot --force >/dev/null &")

    def get_pids(self, process_name):
        cmd = ("ps -ef | grep {0} | grep -v 'grep' | "
               "awk {'print $2'}".format(process_name))
        return self.transport.exec_command(cmd).split('\n')

    def kill_process_by_pid(self, pid):
        logger.info("Killing process pid {0} on node {1}"
                    .format(pid, self.hostname))
        self.transport.exec_command("kill -9 {0}".format(pid))

    def kill_process_by_name(self, process_name):
        logger.info("Killing {0} processes on node {1}"
                    .format(process_name, self.hostname))
        for pid in self.get_pids(process_name):
            self.kill_process_by_pid(pid)

    def killall_processes(self, process_name):
        logger.info("Kill all processes {0} on node {1}"
                    .format(process_name, self.hostname))
        self.transport.exec_command("killall -9 {0}".format(process_name))

    def check_process(self, name):
        ret_code, _, _ = self.transport.exec_sync(
            "ps ax | grep {0} | grep -v grep".format(name))
        return ret_code == 0

    def tcp_ping(self):
        try:
            s = socket.socket()
            s.connect(self.transport.address, 22)
            s.close()
        except socket.error:
            return False
        return True
