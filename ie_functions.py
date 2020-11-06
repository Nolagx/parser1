import re


def rgx(text, regex_formula):
    compiled_rgx = re.compile(regex_formula)
    num_groups = compiled_rgx.groups
    ret = []
    for match in re.finditer(compiled_rgx, text):
        cur_tuple = []
        if num_groups == 0:
            cur_tuple.append(match.span())
        else:
            for i in range(1, num_groups + 1):
                cur_tuple.append(match.span(i))
        ret.append(tuple(cur_tuple))
    return ret


def rgx_string(text, regex_formula):
    compiled_rgx = re.compile(regex_formula)
    num_groups = compiled_rgx.groups
    ret = []
    for match in re.finditer(compiled_rgx, text):
        cur_tuple = []
        if num_groups == 0:
            cur_tuple.append(match.group())
        else:
            for i in range(1, num_groups + 1):
                cur_tuple.append(match.group(i))
        ret.append(tuple(cur_tuple))
    return ret
