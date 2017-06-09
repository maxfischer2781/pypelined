import os


def validate_process(pid, name=None):
    """
    Check whether there is a process with `pid` and `name`

    :param pid: pid of the running process
    :param name: name of the running process
    :type name: str or None
    :returns: whether there is a process with the given name and pid
    :rtype: bool
    """
    try:
        with open(os.path.join('/proc', str(pid), 'comm')) as proc_comm:
            proc_name = next(proc_comm).strip()
    except (OSError, IOError):
        return False
    return name is None or name == proc_name
