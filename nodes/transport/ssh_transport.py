import cStringIO
import time

import paramiko

from nodes.transport import base


class SSHTransport(base.Transport):
    def __init__(self, address, username, password=None,
                 pkey=None, look_for_keys=False, *args, **kwargs):
        self.address = address
        self.username = username
        self.password = password
        self.pkey = paramiko.RSAKey.from_private_key(cStringIO.StringIO(pkey))
        self.look_for_keys = look_for_keys
        self.buf_size = 1024

    def _get_ssh_connection(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        ssh.connect(self.address, username=self.username,
                    password=self.password, pkey=self.pkey)
        return ssh

    def exec_sync(self, cmd):
        ssh = self._get_ssh_connection()
        channel = ssh.get_transport().open_session()
        channel.exec_command(cmd)
        out_data = []
        err_data = []
        try:
            while True:
                if not channel.exit_status_ready():
                    time.sleep(1)
                else:
                    break
                if channel.recv_ready():
                    out_data.append(channel.recv(self.buf_size))
                if channel.recv_stderr_ready():
                    err_data.append(channel.recv_stderr(self.buf_size))
            exit_status = channel.recv_exit_status()

        except Exception as e:
            channel.close()
            raise e

        return exit_status, ''.join(out_data), ''.join(err_data)
