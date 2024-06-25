def filter_valid_postconds(postconds):
    valid_postconds = []
    for postcond in postconds:
        try:
            compile(postcond, '<string>', 'exec')
            valid_postconds.append(postcond)
        except SyntaxError:
            continue

    return valid_postconds


def filter_type_check_postconds(postconds):
    type_check_postconds = []
    for postcond in postconds:
        if "isinstance" in postcond:
            type_check_postconds.append(postcond)

    return type_check_postconds


def filter_null_check_postconds(postconds):
    null_check_postconds = []
    for postcond in postconds:
        if "None" in postcond:
            null_check_postconds.append(postcond)

    return null_check_postconds


def filter_boundary_case_check_postconds(postconds):
    boundary_case_check_postconds = []
    for postcond in postconds:
        if "if" in postcond:
            boundary_case_check_postconds.append(postcond)

    return boundary_case_check_postconds


def filter_elements_check_postconds(postconds):
    elements_check_postconds = []
    for postcond in postconds:
        if "len(return_val) == " not in postcond:
            elements_check_postconds.append(postcond)

    return elements_check_postconds


def filter_by_type(postconds, postcond_type):
    if "type-check" in postcond_type:
        return filter_type_check_postconds(postconds)
    elif "null-check" in postcond_type:
        return filter_null_check_postconds(postconds)
    elif "boundary-case-check" in postcond_type:
        return filter_boundary_case_check_postconds(postconds)
    elif "container-elements-check" in postcond_type:
        return filter_elements_check_postconds(postconds)
    else:
        return postconds


def exact(answer):
    postconds = []
    lines = answer.split("\n")

    postconds_lines = []
    is_start = False
    for line in lines:
        if not is_start and line == "```python":
            is_start = True
        elif is_start and line == "```":
            break
        elif is_start and line != "```python" and line != "```":
            postconds_lines.append(line)

    # normal post-conditions
    for line in postconds_lines:
        if line.startswith("assert") and "return_val" in line and line not in postconds:
            postconds.append(line)

    # if for post-conditions
    current_line = ""
    for line in postconds_lines:
        if line.startswith(("if", "for")) and current_line == "":
            current_line = line + "\n"
        elif current_line != "" and line.startswith(" ") or line.startswith("elif") or line.startswith(
                "else") or line.startswith("#") or line == '':
            current_line = current_line + line + "\n"
        elif current_line != "":
            if "assert" in current_line and "return_val" in current_line and current_line not in postconds:
                postconds.append(current_line)
            if line.startswith(("if", "for")):
                current_line = line + "\n"
            else:
                current_line = ""
    if "assert" in current_line and "return_val" in current_line and current_line not in postconds:
        postconds.append(current_line)

    return postconds
