from rally.task import context
from rally import consts

from nodes import objects


@context.configure(name="ssh_cloud", order=900)
class CloudNodesContext(context.Context):
    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {
            "transport_driver": {
                "type": "string",
                "default": "nodes.transport.ssh_transport.SSHTransport"
            },
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string"
                        },
                        "hostname": {
                            "type": "string"
                        },
                        "username": {
                            "type": "string"
                        },
                        "password": {
                            "type": "string"
                        },
                        "private_key": {
                            "type": "string"
                        },
                        "roles": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    }
                }
            }
        }
    }

    def setup(self):
        transport_driver = self.config.get("transport_driver")
        nodes = self.config.get("nodes")
        cluster = objects.Cluster()

        for node_args in nodes:
            cluster.add_host(
                objects.Host(transport_driver=transport_driver, **node_args))

        self.context["cluster"] = cluster

    def cleanup(self):
        pass
