from rally.common.i18n import _
from rally import exceptions as rally_exceptions


class NoValidHost(rally_exceptions.RallyException):
    msg_fmt = _("No host with condition '%(condition)' in cluster")


class EmptyCluster(rally_exceptions.RallyException):
    msg_fmt = _("No hosts in cluster")


class TimeoutException(rally_exceptions.RallyException):
    msg_fmt = _("Request timed out.")


class SSHTimeout(rally_exceptions.RallyException):
    msg_fmt = _("Connection to the %(host)s via SSH timed out.\n"
                "User: %(user)s, Password: %(password)s")


class SSHCommandFailed(rally_exceptions.RallyException):
    msg_fmt = _("Execution of %(command)s on host %(host)s failed:\n"
                "%(stderr)s")
