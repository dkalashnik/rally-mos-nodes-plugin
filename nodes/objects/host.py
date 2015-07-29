from oslo_utils import importutils

from nodes.host_actions import general_client
from nodes.host_actions import pacemaker_client


class Host(object):
    def __init__(self, transport_driver, address,
                 roles=None, *args, **kwargs):
        self.transport = importutils.import_object(transport_driver,
                                                   address, *args, **kwargs)
        self.address = address

        if roles is None:
            self.roles = []
        else:
            self.roles = roles

        self.exec_command = self.transport.exec_command

    @property
    def hostname(self):
        return self.os.hostname

    @property
    def os(self):
        return general_client.GeneralActionsClient(self.transport)

    @property
    def pacemaker(self):
        return pacemaker_client.PacemakerActionsClient(self.transport)
