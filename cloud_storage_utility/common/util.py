def strip_prefix(string, prefix):
    if string.startswith(prefix):
        return string[len(prefix) :]
    return string