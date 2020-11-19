def normalize(s: str) -> str:
    """
        Filter out '\n' and translate multiple ' ' into one ' '
    :param s: String to normalize
    :return: normalized str
    """
    s = list(filter(lambda x: x != '\n', s))
    ret_s = ""
    i = 0
    while i < len(s):
        ret_s += s[i]
        if s[i] == ' ':
            while s[i] == ' ':
                i += 1
        else:
            i += 1
    return ret_s
