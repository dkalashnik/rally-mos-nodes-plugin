from rally.task import context
from rally import consts

from nodes.host_actions import utils


@context.configure(name="recover_cloud", order=900)
class CloudNodesContext(context.Context):
    """This context allows to recover cloud after disaster tests."""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "additionalProperties": False,
        "properties": {
            "checks": {
                "type": "array",
                "default": []
            }
        }
    }

    def setup(self):
        pass

    def cleanup(self):
        cluster = self.context["cluster"]
        utils.wait_for_cluster_online(cluster)
