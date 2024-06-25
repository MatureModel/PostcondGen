import json
from util import CommonUtil
import func_timeout


def exact(code):
    code = code.split("```")[0]
    return code.split("if __name__ == \"__main__\":")[0]


def is_valid_code(code):
    try:
        compile(code, "<string>", "exec")
        return True
    except Exception:
        return False


@func_timeout.func_set_timeout(5)
def test_buggy_code(code, buggy_code, inputs, entry_point):
    exec_globals = {}
    exec(code, exec_globals)
    fn = exec_globals[entry_point]

    flag = True
    buggy_res = []
    for inp in inputs:
        try:
            exec_buggy_global = {}
            exec(buggy_code, exec_buggy_global)
            buggy_fn = exec_buggy_global[entry_point]

            expected_output = fn(*inp)
            buggy_output = buggy_fn(*inp)

            if expected_output != buggy_output:
                flag = False
                buggy_res.append(inp)
                buggy_res.append(buggy_output)
        except Exception:
            continue

    return flag, buggy_res


def test_buggy_codes(problem, buggy_codes):
    valid_buggy_codes = []
    valid_buggy_inputs = []
    good = []
    count = 0
    for buggy_code in buggy_codes:
        print(buggy_code)
        code = problem["prompt"] + problem["canonical_solution"]
        entry_point = problem["entry_point"]

        try:
            base_flag, base_buggy_inputs = test_buggy_code(
                code,
                buggy_code,
                problem["base_input"],
                entry_point)
            plus_flag, plus_buggy_input = test_buggy_code(
                code,
                buggy_code,
                problem["plus_input"],
                entry_point)
            if not base_flag or not plus_flag:
                count += 1
                tmp = base_buggy_inputs + plus_buggy_input
                good.append(tmp)
                if tmp not in valid_buggy_inputs:
                    valid_buggy_inputs.append(tmp)
                    valid_buggy_codes.append(buggy_code)
        except func_timeout.exceptions.FunctionTimedOut:
            continue

    # print(key)
    print(count)
    print(len(valid_buggy_codes))
    file_path = "D:\projects\developing\\2023\FormalSpecification\data-set\HumanEvalPlus-Mini-v0.1.9.jsonl\\results\\bug-code\\code02.jsonl"
    with open(file_path, "ab") as fp:
        tmp = {
            "task_id": problem["task_id"],
            "size": len(valid_buggy_codes),
            "total": count,
            "buggy_codes": valid_buggy_codes
        }
        fp.write((json.dumps(tmp) + "\n").encode("utf-8"))


if __name__ == '__main__':
    data_set_path = "D:\projects\developing\\2023\FormalSpecification\data-set\HumanEvalPlus-v0.1.9.jsonl\\HumanEvalPlus-v0.1.9.jsonl"
    problems = CommonUtil.read_jsonl(data_set_path)

    buggy_code_path = "D:\projects\developing\\2023\FormalSpecification\data-set\HumanEvalPlus-Mini-v0.1.9.jsonl\\results\\bug-code\\natural\\answers\code_plus.jsonl"
    codes = CommonUtil.read_file(buggy_code_path)

    tmp = {"HumanEval/" + str(i): [] for i in [76]}
    for each in codes:
        if each["task_id"] in tmp.keys():
            tmp[each["task_id"]].append(each)

    for key, value in tmp.items():
        buggy_codes = []
        num = 1
        for i in value:
            code = exact(i["generated_text"])
            if is_valid_code(code):
                print("gggggggggggggggggggggggggggggggg")
                print(num)
                print(code)
                buggy_codes.append(code)
                num += 1
            else:
                print("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
                print(num)
                print(code)
                num += 1
        test_buggy_codes(problems[key], buggy_codes)
