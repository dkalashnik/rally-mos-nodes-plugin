import random

from nodes import exceptions
from nodes.objects import host as host_obj


class Cluster(object):
    def __init__(self, hosts=None):
        """Container class for haos.objects.host.Host objects.

        :param hosts: list of haos.objects.host.Host objects
        :return: instance of Cluster
        """
        if not all([isinstance(host, host_obj.Host) for host in hosts]):
            raise ValueError
        if not isinstance(hosts, list):
            raise ValueError

        if hosts is not None:
            self.hosts = hosts
        else:
            self.hosts = []

    def __iter__(self):
        return iter(self.hosts)

    def __len__(self):
        return len(self.hosts)

    def __getitem__(self, index):
        return self.hosts[index]

    def __setitem__(self, index, host):
        if not isinstance(host, host_obj.Host):
            raise ValueError
        self.hosts[index] = host

    def __delitem__(self, index):
        del self.hosts[index]

    def first(self):
        try:
            return self.hosts[0]
        except IndexError:
            raise exceptions.EmptyCluster

    def filter_by_role(self, role):
        return Cluster(hosts=[x for x in self.hosts if role in x.roles])

    def get_by_address(self, address):
        for host in self.hosts:
            if host.address == address:
                return host
        return exceptions.NoValidHost(condition="address == {0}"
                                      .format(address))

    def get_by_hostname(self, hostname):
        for host in self.hosts:
            if host.hostname == hostname:
                return host
        raise exceptions.NoValidHost(condition="hostname == {0}"
                                     .format(hostname))

    def add_host(self, host):
        if not isinstance(host, host_obj.Host):
            raise ValueError
        self.hosts.append(host)

    def get_random_controller(self):
        return random.choice(self.hosts)
