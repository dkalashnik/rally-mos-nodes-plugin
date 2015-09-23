import random
import time

from rally import consts
from rally.plugins.openstack.scenarios.nova import utils as nova_utils
from rally.task import atomic
from rally.task import scenario
from rally.task import types
from rally.task import validation

from nodes import helpers


class ServiceScenario(scenario.Scenario):
    @atomic.action_timer("process.kill")
    def kill_processes_by_name(self, controller, name):
        controller.os.kill_process_by_name(name)

    @atomic.action_timer("service.start")
    def wait_for_process_start(self, controller, name):
        helpers.wait_for(lambda: controller.os.check_process(name))


class ServiceDisaster(ServiceScenario,
                      nova_utils.NovaScenario):
    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def kill_master_resource(self, resource, process_name,
                             image, flavor, wait_between=60,
                             boot_server=True, force_delete=False):
        cluster = self.context['cluster']
        controller = cluster.get_random_controller()
        master_node_name = \
            controller.pacemaker.get_clone_set_master_node(resource)
        master_controller = cluster.get_by_hostname(master_node_name)

        self.kill_service_by_name(master_controller, process_name)
        self.wait_for_service_start(master_controller, process_name)

        if boot_server:
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
    def kill_clone_set_random_resource(self, resource, process_name,
                                       image, flavor, wait_between=60,
                                       nodes_count=1, boot_server=True,
                                       force_delete=False):
        cluster = self.context['cluster']
        controller = cluster.get_random_controller()
        nodes = \
            controller.pacemaker.get_clone_set_nodes(resource)
        controllers = [cluster.get_by_hostname(hostname)
                       for hostname in nodes]
        controllers = random.sample(controllers, nodes_count)

        for controller in controllers:
            self.kill_service_by_name(controller, process_name)
        for controller in controllers:
            self.wait_for_service_start(controller, process_name)

        if boot_server:
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
    def kill_process_on_random_node(self, process_name, node_role,
                                    image, flavor, nodes_count=1,
                                    wait_between=60, boot_server=True,
                                    force_delete=False):
        cluster = self.context['cluster']
        nodes = cluster.filter_by_role(node_role)
        nodes = random.sample(nodes, nodes_count)

        for node in nodes:
            self.kill_service_by_name(node, process_name)
        for node in nodes:
            self.wait_for_service_start(node, process_name)

        if boot_server:
            server = self._boot_server(image, flavor)
            self.sleep_between(10, 30)
            self._delete_server(server, force=force_delete)

        time.sleep(wait_between)
