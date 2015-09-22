from rally.task import atomic
from rally.task import scenario

from nodes import helpers


class ServiceScenario(scenario.Scenario):
    @atomic.action_timer("service.kill")
    def kill_service_by_pid(self, node, pid):
        node.os.kill_process_by_pid(pid)

    @atomic.action_timer("service.kill")
    def kill_service_by_name(self, controller, name):
        controller.os.killall_processes(name)

    @atomic.action_timer("service.start")
    def wait_for_service_start(self, controller, name):
        helpers.wait_for(lambda: controller.os.check_process(name))


class ServiceDisaster(ServiceScenario):

    @scenario.configure()
    def kill_master_resource(self, resource, process_name):
        cluster = self.context['cluster']
        controller = cluster.get_random_controller()
        master_node_name = \
            controller.pacemaker.get_clone_set_master_node(resource)
        master_controller = cluster.get_by_hostname(master_node_name)
        self.kill_service_by_name(master_controller, process_name)

        self.wait_for_service_start(master_controller, process_name)

    @scenario.configure()
    def kill_all_resources(self, process_name):
        cluster = self.context['cluster']
        controllers = cluster.filter_by_role("controller")
        for controller in controllers:
            self.kill_service_by_name(controller, process_name)

