import chainlet


@chainlet.genlet
def remap(key_map, cull_unknown=True):
    """
    Map existing keys to new keys using a mapping

    :param key_map: mapping from old to new keys
    :type key_map: :py:class:`dict` or :py:class:`~collections.Mapping`
    :param cull_unknown: whether to remove all unmapped keys
    :type cull_unknown: bool
    :rtype: Generator[Dict, Dict, None]
    """
    input_dict = yield
    while True:
        output_dict = {}
        for key, val in input_dict.items():
            try:
                new_key = key_map[key]
            except KeyError:
                if not cull_unknown:
                    output_dict[key] = val
            else:
                output_dict[new_key] = val
        input_dict = yield output_dict


@chainlet.funclet
def update(value, iterable=None, **kwargs):
    """
    Insert ``key: value`` pairs into the report

    :param value: data chunk to operator on
    :type value: :py:class:`dict` or :py:class:`~collections.Mapping`
    :param iterable: iterable of ``(key, value)`` pairs
    :type iterable: iterable[(str, T)]
    :param kwargs: explicit ``key=value`` parameters
    """
    value = value.copy()
    if iterable:
        value.update(iterable, **kwargs)
    else:
        value.update(**kwargs)
    return value
