import random
import time

from rally.task.scenarios import base
from rally.plugins.openstack.scenarios.nova import utils as nova_utils
from rally.task import types
from rally.task import validation
from rally import consts

from nodes.host_actions import utils


class ControllerScenario(base.Scenario):
    @base.atomic_action_timer("controller.force_reboot")
    def force_reboot_controller(self, controller):
        controller.os.force_reboot()
        while True:
            try:
                controller.os.get_date()
            except Exception:
                return
            else:
                time.sleep(1)

    @base.atomic_action_timer("controller.grace_reboot")
    def grace_reboot_controller(self, controller):
        controller.os.graceful_reboot()
        while True:
            try:
                controller.os.get_date()
            except Exception:
                return
            else:
                time.sleep(1)

    @base.atomic_action_timer("controller.boot")
    def wait_for_boot(self, controller):
        while True:
            try:
                controller.os.get_date()
            except Exception:
                time.sleep(1)
            else:
                return

    @base.atomic_action_timer("cluster.recovery")
    def wait_for_cluster_online(self, cluster):
        utils.wait_for_cluster_online(cluster)


class ControllerDisaster(ControllerScenario,
                         nova_utils.NovaScenario):

    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @base.scenario()
    def reboot_random_controllers(self, image, flavor,
                                  force_reboot=True,
                                  force_delete=True,
                                  controllers_count=1,
                                  controller_names=None,
                                  exclude_controllers=None):
        cluster = self.context['cluster']

        if not isinstance(exclude_controllers, list):
            exclude_controllers = [exclude_controllers]

        if not isinstance(controller_names, list):
            controller_names = [controller_names]

        if controller_names is None:
            controllers = random.sample(
                filter(lambda node: node.hostname not in exclude_controllers,
                       cluster), controllers_count)
        else:
            controllers = []
            for hostname in controller_names:
                controllers.append(cluster.get_by_hostname(hostname))

        for controller in controllers:
            if force_reboot:
                self.force_reboot_controller(controller)
            else:
                self.grace_reboot_controller(controller)

        for controller in controllers:
            self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)

        server = self._boot_server(image, flavor)
        self.sleep_between(10, 30)
        self._delete_server(server, force=force_delete)

    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @base.scenario()
    def reboot_controller_with_primitive(self, resource, image, flavor,
                                         force_reboot=True,
                                         force_delete=True):
        cluster = self.context['cluster']

        controller = random.choice(cluster)
        node_name = controller.pacemaker.get_resource_node(resource)
        controller = cluster.get_by_hostname(node_name)

        if force_reboot:
            self.force_reboot_controller(controller)
        else:
            self.grace_reboot_controller(controller)

        self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)

        server = self._boot_server(image, flavor)
        self.sleep_between(10, 30)
        self._delete_server(server, force=force_delete)

    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @base.scenario()
    def reboot_controller_with_master_resource(self, resource, image, flavor,
                                               force_reboot=True,
                                               force_delete=True):
        cluster = self.context['cluster']

        controller = random.choice(cluster)
        node_name = controller.pacemaker.get_clone_set_master_node(resource)
        controller = cluster.get_by_hostname(node_name)

        if force_reboot:
            self.force_reboot_controller(controller)
        else:
            self.grace_reboot_controller(controller)

        self.wait_for_boot(controller)
        self.wait_for_cluster_online(cluster)

        server = self._boot_server(image, flavor)
        self.sleep_between(10, 30)
        self._delete_server(server, force=force_delete)
