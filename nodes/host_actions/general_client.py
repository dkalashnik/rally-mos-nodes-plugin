import ConfigParser
import cStringIO

from nodes import exceptions
from nodes.host_actions import base


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
        self.transport.exec_command("nohup reboot >/dev/null &")

    def force_reboot(self):
        self.transport.exec_command("reboot --force >/dev/null &")

    def kill_process_by_pid(self, pid):
        self.transport.exec_command("kill -9 {0}".format(pid))

    def killall_processes(self, name):
        self.transport.exec_command("killall -9 {0}".format(name))

    def check_process(self, name):
        ret_code, _, _ = self.transport.exec_sync(
            "ps ax | grep {0} | grep -v grep".format(name))
        return ret_code == 0
