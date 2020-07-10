def remove_prefix(string: str, prefix: str) -> str:
    """
    Removes prefix from string
    :param string:
    :param prefix:
    :return: string without prefix
    """
    if string.startswith(prefix):
        return string[len(prefix):]
    return string
