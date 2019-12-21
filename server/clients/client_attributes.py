def default_attributes():
    return {
        "client": {"is_moderator": False},
        "ic": {"position": "", "muted": False},
        "ooc": {"name": None},
        "global": {"muted": False},
        "adverts": {"muted": False},
    }


def get_dict_attribute(dictionary, attr_path):
    path_split = attr_path.split(".")
    for path in path_split:
        dictionary = dictionary[path]
    return dictionary


def set_dict_attribute(dictionary, attr_path, value):
    path_split = attr_path.split(".", maxsplit=1)
    key = path_split[0]
    if len(path_split) == 1:
        dictionary[key] = value
        return
    path = path_split[1]
    set_dict_attribute(dictionary[key], path, value)
