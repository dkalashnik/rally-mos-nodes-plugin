import logging

from lxml import etree

from nodes import helpers
from nodes.host_actions import base

logger = logging.getLogger(__name__)


class PacemakerActionsClient(base.BaseHostActionsClient):
    def wait_for_node_went_down(self, timeout=1200):
        helpers.wait_for(lambda: not self.check_all_nodes_online(),
                         timeout=timeout)

    def wait_for_all_nodes_online(self, timeout=1200):
        helpers.wait_for(self.check_all_nodes_online,
                         timeout=timeout)

    def wait_for_management_vip(self, timeout=600):
        helpers.wait_for(self.get_management_vip_node, timeout=timeout)

    def _get_crm_mon_xml(self):
        return etree.XML(self.transport.exec_command('crm_mon --as-xml'))

    def _get_first_subsection(self, xml, section_name):
        for section in xml:
            if section.tag == section_name:
                return section

    def _get_subsections_list(self, xml, section_name):
        result = []
        for section in xml:
            if section.tag == section_name:
                result.append(section)
        return result

    def _get_resource_by_id(self, resources_list, resource_id):
        for resource in resources_list:
            if resource.get('id') == resource_id:
                return resource

    def get_resource_node(self, resource_id):
        resources = self._get_first_subsection(self._get_crm_mon_xml(),
                                               'resources')
        resources = self._get_subsections_list(resources, 'resource')
        resource = self._get_resource_by_id(resources, resource_id)
        node_name = self._get_first_subsection(resource, 'node').get('name')
        logger.info("Found {0} on node {1}".format(resource_id, node_name))
        return node_name

    def _get_clone_set_nodes_by_conditions(self,
                                           clone_set_conditions,
                                           resource_conditions):
        result = []
        resources = self._get_first_subsection(self._get_crm_mon_xml(),
                                               'resources')
        clone_sets = self._get_subsections_list(resources, 'clone')
        for clone_set in clone_sets:
            if not all([condition(clone_set)
                        for condition in clone_set_conditions]):
                continue
            for resource in self._get_subsections_list(clone_set, 'resource'):
                if not all([condition(resource)
                            for condition in resource_conditions]):
                    continue
                node = self._get_first_subsection(resource, 'node')
                result.append(node.get('name'))
        return result

    def get_clone_set_nodes(self, resource_id):
        nodes = self._get_clone_set_nodes_by_conditions(
            clone_set_conditions=[],
            resource_conditions=[
                lambda resource: resource.get('id') == resource_id,
                lambda resource: resource.get('active') == 'true'])
        logger.info("Found {0} resource on nodes: {1}"
                    .format(resource_id, ', '.join(nodes)))
        return nodes

    def get_clone_set_master_node(self, resource_id):
        node = self._get_clone_set_nodes_by_conditions(
            clone_set_conditions=[
                lambda clone_set: clone_set.get('multi_state') == 'true'],
            resource_conditions=[
                lambda resource: resource.get('id') == resource_id,
                lambda resource: resource.get('active') == 'true',
                lambda resource: resource.get('role') == 'Master'])[0]
        logger.info("Found Master {0} resource on node: {1}"
                    .format(resource_id, node))
        return node

    def get_clone_get_slave_nodes(self, resource_id):
        nodes = self._get_clone_set_nodes_by_conditions(
            clone_set_conditions=[
                lambda clone_set: clone_set.get('multi_state') == 'true'],
            resource_conditions=[
                lambda resource: resource.get('id') == resource_id,
                lambda resource: resource.get('active') == 'true',
                lambda resource: resource.get('role') == 'Slave'])
        logger.info("Found Slave {0} resource on nodes: {1}"
                    .format(resource_id, ', '.join(nodes)))
        return nodes

    def get_public_vip_node(self):
        resource_id = 'vip__public'
        return self.get_resource_node(resource_id)

    def get_management_vip_node(self):
        resource_id = 'vip__management'
        return self.get_resource_node(resource_id)

    def get_online_nodes(self):
        nodes = self._get_first_subsection(self._get_crm_mon_xml(), 'nodes')
        nodes = self._get_subsections_list(nodes, 'node')
        return [node.get('name')
                for node in nodes if node.get('online') == 'true']

    def check_all_nodes_online(self):
        nodes = self._get_first_subsection(self._get_crm_mon_xml(), 'nodes')
        nodes = self._get_subsections_list(nodes, 'node')
        return all(node.get('online') == 'true' for node in nodes)
