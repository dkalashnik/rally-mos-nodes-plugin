import random
import logging
import time

from rally.task import atomic
from rally.task import scenario

from nodes.host_actions import utils

logger = logging.getLogger(__name__)


class ControllerScenario(scenario.Scenario):
    @atomic.action_timer("controller.force_reboot")
    def force_reboot_controller(self, controller):
        controller.os.force_reboot()
        while True:
            try:
                controller.os.get_date()
            except Exception:
                return
            else:
                time.sleep(1)

    @atomic.action_timer("controller.grace_reboot")
    def grace_reboot_controller(self, controller):
        controller.os.graceful_reboot()
        while True:
            try:
                controller.os.get_date()
            except Exception:
                return
            else:
                time.sleep(1)

    @atomic.action_timer("controller.boot")
    def wait_for_boot(self, controller):
        while True:
            try:
                controller.os.get_date()
            except Exception:
                time.sleep(1)
            else:
                return

    @atomic.action_timer("cluster.recovery")
    def wait_for_cluster_online(self, cluster):
        utils.wait_for_cluster_online(cluster)


class ControllerDisaster(ControllerScenario):

    @scenario.configure()
    def reboot_random_controllers(self,
                                  force_reboot=True,
                                  controllers_count=1):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")

        controllers = random.sample(controllers, controllers_count)
        logger.info("Choose {0} controllers to reboot: {1}"
                    .format(controllers_count,
                            ' '.join([controller.hostname
                                      for controller in controllers])))

        for controller in controllers:
            if force_reboot:
                logger.info("Force rebooting {0}".format(controller.hostname))
                self.force_reboot_controller(controller)
            else:
                logger.info("Grace rebooting {0}".format(controller.hostname))
                self.grace_reboot_controller(controller)

        for controller in controllers:
            self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)

    @scenario.configure()
    def reboot_controller_with_primitive(self,
                                         resource,
                                         force_reboot=True):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")

        controller = random.choice(controllers)
        logger.info("Search for controller with {0}".format(resource))
        node_name = controller.pacemaker.get_resource_node(resource)
        controller = cluster.get_by_hostname(node_name)
        logger.info("Found {0} on controller {1}".format(resource,
                                                         controller.hostname))

        if force_reboot:
            logger.info("Force rebooting {0}".format(controller.hostname))
            self.force_reboot_controller(controller)
        else:
            logger.info("Grace rebooting {0}".format(controller.hostname))
            self.grace_reboot_controller(controller)

        self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)

    @scenario.configure()
    def reboot_controller_with_master_resource(self,
                                               resource,
                                               force_reboot=True):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")

        controller = random.choice(controllers)
        logger.info("Search for controller with {0}".format(resource))
        node_name = controller.pacemaker.get_clone_set_master_node(resource)
        controller = cluster.get_by_hostname(node_name)
        logger.info("Found {0} on controller {1}".format(resource,
                                                         controller.hostname))

        if force_reboot:
            logger.info("Force rebooting {0}".format(controller.hostname))
            self.force_reboot_controller(controller)
        else:
            logger.info("Grace rebooting {0}".format(controller.hostname))
            self.grace_reboot_controller(controller)

        self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)
