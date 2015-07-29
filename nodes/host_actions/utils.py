from nodes import helpers


def check_all_nodes_online_nailgun(master_node):
    check_command = ("fuel nodes | grep False && "
                     "echo 'Some nodes offline' || echo 'No offline nodes'")
    return 'No offline nodes' in master_node.exec_command(check_command)


def check_mysql_status(controller):
    command = ("mysql -e \"show status like 'wsrep_local_state_comment'\""
               " | grep 'Synced' &> /dev/null && echo 'OK' || echo 'FAIL'")
    return "OK" in controller.exec_command(command)


def check_rabbit_cluster_online(controller, ctrls_num=3):
    cmd = "rabbitmqctl cluster_status"
    status = controller.exec_command(cmd)
    start = status.index('running_nodes')
    end = status[start:].index('}')
    return status[start:start+end].count("@") == ctrls_num


def check_rabbitmq_queues_sync(controller):
    cmd = "rabbitmqctl list_queues state"
    output = controller.exec_command(cmd).splitlines()
    output = output[1:-1]
    return all(['running' in queue_state for queue_state in output])


def wait_for_cluster_online(cluster):
    master_node = cluster.filter_by_role("master").first()
    helpers.wait_for(
        lambda: check_all_nodes_online_nailgun(master_node))

    controllers = cluster.filter_by_role("controller")
    for node in controllers:
        node.pacemaker.wait_for_all_nodes_online()
        helpers.wait_for(lambda: check_mysql_status(node))
        helpers.wait_for(lambda: check_rabbit_cluster_online(
            node, len(controllers)))
        helpers.wait_for(lambda: check_rabbitmq_queues_sync(
            node))
