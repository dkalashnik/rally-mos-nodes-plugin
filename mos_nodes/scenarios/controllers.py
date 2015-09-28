import logging
import random
import time

from rally import consts
from rally.plugins.openstack.scenarios.nova import utils as nova_utils
from rally.task import atomic
from rally.task import scenario
from rally.task import types
from rally.task import validation

from nodes.host_actions import utils

logger = logging.getLogger(__name__)


class ControllerScenario(scenario.Scenario):
    @atomic.action_timer("controller.force_reboot")
    def force_reboot_controller(self, controller):
        controller.os.force_reboot()
        # NOTE(dkalashnik): waiter here is a kinda useless,
        # so just sleep for 10 seconds.
        time.sleep(10)

    @atomic.action_timer("controller.grace_reboot")
    def grace_reboot_controller(self, controller):
        controller.os.graceful_reboot()
        while controller.os.tcp_ping():
            time.sleep(1)

    @atomic.action_timer("controller.boot")
    def wait_for_boot(self, controller):
        while not controller.os.tcp_ping():
            time.sleep(1)

    @atomic.action_timer("cluster.recovery")
    def wait_for_cluster_online(self, cluster):
        utils.wait_for_cluster_online(cluster)


class ControllerRobustness(ControllerScenario):

    @scenario.configure()
    def reboot_random_controllers(self,
                                  force_reboot=True,
                                  controllers_count=1,
                                  wait_between=60):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")
        controllers = random.sample(controllers, controllers_count)

        for controller in controllers:
            if force_reboot:
                self.force_reboot_controller(controller)
            else:
                self.grace_reboot_controller(controller)

        for controller in controllers:
            self.wait_for_boot(controller)

        self.wait_for_cluster_online(cluster)

        time.sleep(wait_between)

    @scenario.configure()
    def sequential_controllers_reboot(self,
                                      force_reboot=True,
                                      controllers_count=1,
                                      wait_between=60):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")
        controllers = random.sample(controllers, controllers_count)

        for controller in controllers:
            if force_reboot:
                self.force_reboot_controller(controller)
            else:
                self.grace_reboot_controller(controller)

            self.wait_for_boot(controller)
            self.wait_for_cluster_online(cluster)

        time.sleep(wait_between)

    @scenario.configure()
    def reboot_controller_with_primitive(self, resource,
                                         force_reboot=True,
                                         wait_between=60):

        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")
        controller = random.choice(controllers)
        node_name = controller.pacemaker.get_resource_node(resource)
        controller = cluster.get_by_hostname(node_name)

        if force_reboot:
            self.force_reboot_controller(controller)
        else:
            self.grace_reboot_controller(controller)

        self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)

        time.sleep(wait_between)

    @scenario.configure()
    def reboot_controller_with_master_resource(self, resource,
                                               force_reboot=True,
                                               wait_between=60):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")

        controller = random.choice(controllers)
        node_name = controller.pacemaker.get_clone_set_master_node(resource)
        controller = cluster.get_by_hostname(node_name)

        if force_reboot:
            self.force_reboot_controller(controller)
        else:
            self.grace_reboot_controller(controller)

        self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)

        time.sleep(wait_between)


class ControllerRobustnessNovaCheck(ControllerScenario,
                                    nova_utils.NovaScenario):
    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def reboot_random_controllers(self, image, flavor,
                                  force_reboot=True, controllers_count=1,
                                  wait_between=60, force_delete=False):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")

        controllers = random.sample(controllers, controllers_count)

        for controller in controllers:
            if force_reboot:
                self.force_reboot_controller(controller)
            else:
                self.grace_reboot_controller(controller)

        for controller in controllers:
            self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)

        # NOTE(dkalashnik): Wait for keystone-memcache consistency
        time.sleep(300)

        server = self._boot_server(image, flavor)
        self.sleep_between(10, 30)
        self._delete_server(server, force=force_delete)

        time.sleep(wait_between)

    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def sequential_controllers_reboot(self, image, flavor,
                                      force_reboot=True, controllers_count=1,
                                      wait_between=60, boot_server=True,
                                      force_delete=False):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")
        controllers = random.sample(controllers, controllers_count)

        for controller in controllers:
            if force_reboot:
                self.force_reboot_controller(controller)
            else:
                self.grace_reboot_controller(controller)

            self.wait_for_boot(controller)
            self.wait_for_cluster_online(cluster)

        # NOTE(dkalashnik): Wait for keystone-memcache consistency
        time.sleep(300)

        server = self._boot_server(image, flavor)
        self.sleep_between(10, 30)
        self._delete_server(server, force=force_delete)

        time.sleep(wait_between)

    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def reboot_controller_with_primitive(self, image, flavor, resource,
                                         force_reboot=True, wait_between=60,
                                         boot_server=True, force_delete=False):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")
        controller = random.choice(controllers)
        node_name = controller.pacemaker.get_resource_node(resource)
        controller = cluster.get_by_hostname(node_name)

        if force_reboot:
            self.force_reboot_controller(controller)
        else:
            self.grace_reboot_controller(controller)

        self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)

        # NOTE(dkalashnik): Wait for keystone-memcache consistency
        time.sleep(300)

        server = self._boot_server(image, flavor)
        self.sleep_between(10, 30)
        self._delete_server(server, force=force_delete)

        time.sleep(wait_between)

    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def reboot_controller_with_master_resource(self, image, flavor, resource,
                                               force_reboot=True,
                                               wait_between=60,
                                               boot_server=True,
                                               force_delete=False):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")

        controller = random.choice(controllers)
        node_name = controller.pacemaker.get_clone_set_master_node(resource)
        controller = cluster.get_by_hostname(node_name)

        if force_reboot:
            self.force_reboot_controller(controller)
        else:
            self.grace_reboot_controller(controller)

        self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)

        # NOTE(dkalashnik): Wait for keystone-memcache consistency
        time.sleep(300)

        server = self._boot_server(image, flavor)
        self.sleep_between(10, 30)
        self._delete_server(server, force=force_delete)

        time.sleep(wait_between)
