from rally.task import context
from rally import consts
import yaml

from nodes.objects import cluster
from nodes.objects import host


@context.configure(name="ssh_cloud", order=900)
class CloudNodesContext(context.Context):
    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {
            "fuel_master_address": {
                "type": "string",
                "default": "127.0.0.1"
            },
            "username": {
                "type": "string",
                "default": "root"
            },
            "password": {
                "type": "string",
                "default": "r00tme"
            },
            "transport_driver": {
                "type": "string",
                "default": "nodes.transport.ssh_transport.SSHTransport"
            },
            "data_source": {
                "type": "string",
                "default": "astute"
            },
            "data": {
                "type": "list",
                "default": []
            }
        }
    }

    def astute_adapter(self, master_node):
        astute_yaml = master_node.exec_command(
            "ssh $(fuel node | grep controller | head -n 1 | "
            "grep -E -o '([0-9]{1,3}[\.]){3}[0-9]{1,3}') "
            "'cat /etc/astute.yaml'")
        nodes = yaml.load(astute_yaml)['nodes']
        private_key = master_node.os.get_file_content("/root/.ssh/id_rsa")

        storage = {}
        for node in nodes:
            temp = storage.get(
                node['fqdn'],
                {'transport_driver': self.config.get('transport_driver'),
                 'fqdn': node['fqdn'],
                 'hostname': node['name'],
                 'pkey': private_key,
                 'internal_address': node['internal_address'],
                 'public_address': node['public_address'],
                 'address': node['public_address'],
                 # TODO(dkalashnik): Add username autofilling
                 'username': 'root',
                 'role': []})
            role = (node['role'] if node['role'] != 'primary-controller'
                    else 'controller')
            temp['role'].append(role)

            storage[node['fqdn']] = temp

        return [host.Host(**params) for params in storage.values()]

    def setup(self):
        fuel_master_credentials = {
            "transport_driver": self.config.get("transport_driver"),
            "address": self.config.get("fuel_master_address"),
            "roles": ["master"],
            "username": self.config.get("username"),
            "password": self.config.get("password"),
        }

        master_node = host.Host(**fuel_master_credentials)

        hosts = []
        if self.config.get("data_source") == "astute":
            hosts = self.astute_adapter(master_node)

        hosts.append(master_node)
        self.context["cluster"] = cluster.Cluster(hosts=hosts)

    def cleanup(self):
        pass
