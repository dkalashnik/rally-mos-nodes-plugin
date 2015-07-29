from rally.task.scenarios import base
from rally.plugins.openstack.scenarios.nova import utils as nova_utils
from rally.task import types
from rally.task import validation
from rally import consts


class ServiceScenario(base.Scenario):
    @base.atomic_action_timer("service.kill")
    def kill_service_by_pid(self, controller, pid):
        pass

    @base.atomic_action_timer("service.kill")
    def kill_service_by_name(self, controller, name):
        controller.os.killall_processes(name)

    @base.atomic_action_timer("service.stop")
    def stop_service(self, cluster, name):
        pass

    @base.atomic_action_timer("service.start")
    def wait_for_service_start(self, controller, name):
        pass


class ServiceDisaster(ServiceScenario,
                      nova_utils.NovaScenario):
    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @base.scenario()
    def kill_master_resource(self, resource):
        cluster = self.context['cluster']
        controller = cluster.get_random_controller()
        master_node_name = \
            controller.pacemaker.get_clone_set_master_node(resource)
        master_controller = cluster.get_by_hostname(master_node_name)
        self.kill_service_by_name(master_controller, resource)

    @types.set(image=types.ImageResourceType,
               flavor=types.FlavorResourceType)
    @validation.image_valid_on_flavor("flavor", "image")
    @validation.required_services(consts.Service.NOVA)
    @validation.required_openstack(users=True)
    @base.scenario()
    def stop_master_resource(self, resource):
        cluster = self.context['cluster']
        controller = cluster.get_random_controller()
        master_node_name = \
            controller.pacemaker.get_clone_set_master_node(resource)
        master_controller = cluster.get_by_hostname(master_node_name)
        self.stop_service(master_controller)
