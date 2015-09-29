import random
import logging
import time

from rally import consts
from rally.plugins.openstack.scenarios.nova import utils as nova_utils
from rally.task import atomic
from rally.task import scenario
from rally.task import types
from rally.task import validation

from nodes import helpers
from nodes.host_actions import utils

logger = logging.getLogger(__name__)


class ServiceScenario(scenario.Scenario):
    @atomic.action_timer("service.kill")
    def kill_service_by_name(self, controller, name):
        logger.info("Start killing for {0} on {1}"
                    .format(name, controller.hostname))
        controller.os.kill_process_by_name(name)

    @atomic.action_timer("sevice.start")
    def wait_for_service_start(self, controller, name):
        logger.info("Start waiting for {0} on {1}"
                    .format(name, controller.hostname))
        helpers.wait_for(lambda: controller.os.check_process(name))

    @atomic.action_timer("cluster.recovery")
    def wait_for_cluster_online(self, cluster):
        utils.wait_for_cluster_online(cluster)


class ServiceRobustness(ServiceScenario,
                        nova_utils.NovaScenario):

    @scenario.configure()
    def kill_master_resource(self, resource, process_name,
                             wait_between=60):
        cluster = self.context['cluster']
        controller = cluster.get_random_controller()
        master_node_name = \
            controller.pacemaker.get_clone_set_master_node(resource)
        master_controller = cluster.get_by_hostname(master_node_name)

        self.kill_service_by_name(master_controller, process_name)
        self.wait_for_service_start(master_controller, process_name)
        self.wait_for_cluster_online(cluster)

        time.sleep(wait_between)

    @scenario.configure()
    def kill_clone_set_random_resource(self, resource, process_name,
                                       wait_between=60, nodes_count=1):
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
        self.wait_for_cluster_online(cluster)

        time.sleep(wait_between)

    @scenario.configure()
    def kill_process_on_random_node(self, process_name, node_role,
                                    nodes_count=1, wait_between=60):
        cluster = self.context['cluster']
        nodes = cluster.filter_by_role(node_role)
        nodes = random.sample(nodes, nodes_count)

        for node in nodes:
            self.kill_service_by_name(node, process_name)
        for node in nodes:
            self.wait_for_service_start(node, process_name)
        self.wait_for_cluster_online(cluster)

        time.sleep(wait_between)


class ServiceRobustnessNovaCheck(ServiceScenario,
                                 nova_utils.NovaScenario):
    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @scenario.configure()
    def kill_master_resource(self, resource, process_name,
                             image, flavor, wait_between=60,
                             force_delete=False):
        cluster = self.context['cluster']
        controller = cluster.get_random_controller()
        master_node_name = \
            controller.pacemaker.get_clone_set_master_node(resource)
        master_controller = cluster.get_by_hostname(master_node_name)

        self.kill_service_by_name(master_controller, process_name)
        self.wait_for_service_start(master_controller, process_name)
        self.wait_for_cluster_online(cluster)

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
                                       nodes_count=1, force_delete=False):
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
        self.wait_for_cluster_online(cluster)

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
                                    wait_between=60, force_delete=False):
        cluster = self.context['cluster']
        nodes = cluster.filter_by_role(node_role)
        nodes = random.sample(nodes, nodes_count)

        for node in nodes:
            self.kill_service_by_name(node, process_name)
        for node in nodes:
            self.wait_for_service_start(node, process_name)
        self.wait_for_cluster_online(cluster)

        server = self._boot_server(image, flavor)
        self.sleep_between(10, 30)
        self._delete_server(server, force=force_delete)

        time.sleep(wait_between)
