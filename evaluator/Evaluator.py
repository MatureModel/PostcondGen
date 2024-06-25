import ast
import json
from exacter import Exacter
from util import CommonUtil
from math import comb


def read_args(source_code):
    # 解析源代码生成AST
    tree = ast.parse(source_code)

    # 用于存储找到的函数及其参数
    functions = {}

    # 遍历AST的每一个节点
    for node in ast.iter_child_nodes(tree):
        # 检查节点是否为函数定义
        if isinstance(node, ast.FunctionDef):
            # 提取函数名
            function_name = node.name
            # 提取参数列表
            params = [param.arg for param in node.args.args]
            # 将函数名和参数列表添加到列表中
            functions[function_name] = params

    return functions


def test_postcond_correctness(code, postcond, inputs, entry_point, args):
    exec_globals = {}
    exec(code, exec_globals)
    fn = exec_globals[entry_point]

    for inp in inputs:
        global_vars = dict(zip(args, inp))
        global_vars["return_val"] = fn(*inp)
        try:
            exec(postcond, global_vars)
        except AssertionError:
            print(f"{postcond} exec {inp}, output: {global_vars['return_val']}, AssertionError")
            return False
        except Exception:
            print(f"{postcond} exec {inp}, output: {global_vars['return_val']}, unexpected error")
            return False
    return True


def test_postcond_completeness(buggy_code, postcond, inputs, entry_point, args):
    exec_globals = {}
    exec(buggy_code, exec_globals)
    fn = exec_globals[entry_point]

    for inp in inputs:
        try:
            global_vars = dict(zip(args, inp))
            global_vars["return_val"] = fn(*inp)
            exec(postcond, global_vars)
        except AssertionError:
            print(f"{buggy_code} exec {inp}, detected by {postcond}")
            return True
        except Exception:
            continue
    return False


def evaluate_correctness(problem, postconds):
    correct_size = 0

    correct_postconds = []
    incorrect_postconds = []
    for postcond in postconds:
        print(postcond)

        code = problem["prompt"] + problem["canonical_solution"]
        entry_point = problem["entry_point"]
        functions = read_args(code)
        args = functions[entry_point]

        base_flag = test_postcond_correctness(
            code,
            postcond,
            problem["base_input"],
            entry_point,
            args)
        plus_flag = test_postcond_correctness(
            code,
            postcond,
            problem["plus_input"],
            entry_point,
            args)
        if base_flag and plus_flag:
            correct_size = correct_size + 1
            correct_postconds.append(postcond)
        else:
            incorrect_postconds.append(postcond)

        print("----")

    return correct_size, correct_postconds, incorrect_postconds


def evaluate_completeness(problem, postconds, buggy_codes):
    detected_size = 0

    detected_codes = []
    undetected_codes = []
    for buggy_code in buggy_codes:
        print(buggy_code)

        code = problem["prompt"] + problem["canonical_solution"]
        entry_point = problem["entry_point"]
        functions = read_args(code)
        args = functions[entry_point]

        base_flag = test_postcond_completeness(
            buggy_code,
            postconds,
            problem["base_input"],
            entry_point,
            args)
        plus_flag = test_postcond_completeness(
            buggy_code,
            postconds,
            problem["plus_input"],
            entry_point,
            args)
        if base_flag or plus_flag:
            detected_size = detected_size + 1
            detected_codes.append(buggy_code)
        else:
            undetected_codes.append(buggy_code)

        print("----")
    return detected_size, detected_codes, undetected_codes


def to_eval_correctness(problems, targets, postcond_type, responses_path, eval_path):
    responses = CommonUtil.read_file(responses_path)

    correct_responses = 0
    total = 0
    correct_total = 0
    result = {key: {"task_id": key, "correct_responses": 0, "size": 0, "correct_size": 0, "correct_postconds": [],
                    "incorrect_postconds": []} for key in targets}

    for value in responses:
        key = value["task_id"]
        print(key)
        response = value["generated_text"]
        postconds = Exacter.exact(response)
        postconds = Exacter.filter_valid_postconds(postconds)
        postconds = Exacter.filter_by_type(postconds, postcond_type)

        if key == "HumanEval/15":
            postconds = [each for each in postconds if "for" not in each]

        correct_size, correct_postconds, incorrect_postconds = evaluate_correctness(problems[key], postconds)

        result[key]["size"] += len(postconds)
        total += len(postconds)

        result[key]["correct_size"] += correct_size
        correct_total += correct_size

        result[key]["correct_postconds"] += correct_postconds
        result[key]["incorrect_postconds"] += incorrect_postconds

        if correct_size > 0:
            result[key]["correct_responses"] += 1
            correct_responses = correct_responses + 1

    correct_problem = 0
    rate = 0
    for task_id, eval_res in result.items():
        if len(eval_res["correct_postconds"]) > 0:
            correct_problem += 1
        total_balls = 5
        # 蓝球的数量
        blue_balls = total_balls - eval_res["correct_responses"]
        # 从5个球中取3个球都是蓝球的概率
        prob_all_blue = comb(blue_balls, 3) / comb(total_balls, 3)
        # 至少有一个红球的概率
        prob_at_least_one_red = 1 - prob_all_blue
        rate += prob_at_least_one_red

    with open(eval_path, "wb") as fp:
        for task_id, eval_res in result.items():
            fp.write((json.dumps(eval_res) + "\n").encode("utf-8"))
        data = {
            "model": "gemma-7b-it",
            "accept@1": correct_responses / len(responses),
            "accept@3": rate / len(targets),
            "accept@5": correct_problem / len(targets),
            "problem_num": len(targets),
            "correct_problem_cond_num": correct_problem,
            "response_num": len(responses),
            "correct_response_num": correct_responses,
            "total": total,
            "correct_total": correct_total,
            "total_correct_rate": correct_total / total
        }
        fp.write((json.dumps(data) + "\n").encode("utf-8"))


def to_eval_completeness(problems, buggy_codes_path, eval_path, completeness_path):
    buggy_codes = CommonUtil.read_jsonl(buggy_codes_path)
    postconds = CommonUtil.read_jsonl(eval_path)

    full_detected_prob = 0
    detected_bugs = 0
    total_bugs = 0

    result = {key: {"task_id": key, "size": 0, "detected_size": 0, "detected_codes": [], "undetected_codes": []}
              for key in postconds.keys()}

    for key, value in postconds.items():
        postcond = ""
        for cond in value["correct_postconds"]:
            postcond = postcond + cond + "\n"

        detected_size, detected_codes, undetected_codes = evaluate_completeness(problems[key], postcond,
                                                                                buggy_codes[key]["buggy_codes"])

        result[key]["size"] = len(buggy_codes[key]["buggy_codes"])
        result[key]["detected_size"] = detected_size
        result[key]["detected_codes"] = detected_codes
        result[key]["undetected_codes"] = undetected_codes

        total_bugs += len(buggy_codes[key]["buggy_codes"])
        detected_bugs += detected_size
        if detected_size == len(buggy_codes[key]["buggy_codes"]):
            full_detected_prob += 1

    print("completeness result")
    print(full_detected_prob)
    print(full_detected_prob / len(postconds.keys()))

    with open(completeness_path, "wb") as fp:
        for task_id, comp_res in result.items():
            fp.write((json.dumps(comp_res) + "\n").encode("utf-8"))
        data = {
            "model": "gemma-7b-it",
            "problem_num": len(postconds.keys()),
            "full_detected_prob": full_detected_prob,
            "full_detected_rate": full_detected_prob / len(postconds.keys()),
            "total_bugs": total_bugs,
            "detected_bugs": detected_bugs,
            "detected_bugs_rate": detected_bugs / total_bugs
        }
        fp.write((json.dumps(data) + "\n").encode("utf-8"))


def save_total(base_path):
    data_set_path = "D:\projects\developing\\2023\FormalSpecification\data-set\HumanEvalPlus-v0.1.9.jsonl\HumanEvalPlus-v0.1.9.jsonl"
    problems = CommonUtil.read_jsonl(data_set_path)

    result = {key: {"task_id": key, "size": 0, "correct_size": 0, "correct_postconds": [], "incorrect_postconds": []}
              for key in problems.keys()}

    types = ["arithmetic-bounds-check", "bool-case-check", "boundary-case-check", "container-elements-check",
             "container-property-check", "format-check", "null-check", "type-check-cot", "equality-check", "three-shot"]
    for i in types:
        single_eval_path = base_path + f"\\{i}\\eval.jsonl"
        evals = CommonUtil.read_jsonl(single_eval_path)

        for key, item in evals.items():
            task_id = item["task_id"]

            for cond in item["correct_postconds"]:
                result[task_id]["correct_postconds"].append(cond)

            for cond in item["incorrect_postconds"]:
                result[task_id]["incorrect_postconds"].append(cond)

    total = 0
    correct_total = 0
    num = 0
    for task_id in problems.keys():
        result[task_id]["size"] = len(result[task_id]["correct_postconds"]) + len(result[task_id]["incorrect_postconds"])
        result[task_id]["correct_size"] = len(result[task_id]["correct_postconds"])
        total = total + result[task_id]["size"]
        correct_total = correct_total + result[task_id]["correct_size"]
        if result[task_id]["correct_size"] > 0:
            num = num + 1

    with open(base_path + "\\total\\latest.jsonl", "wb") as fp:
        for task_id, eval_res in result.items():
            fp.write((json.dumps(eval_res) + "\n").encode("utf-8"))
        data = {
            "model": "gemma-7b-it",
            "problem_num": len(problems.keys()),
            "correct_problem_cond_num": num,
            "correct_rate": num / len(problems.keys()),
            "total": total,
            "correct_total": correct_total,
            "total_correct_rate": correct_total / total
        }
        fp.write((json.dumps(data) + "\n").encode("utf-8"))

if __name__ == '__main__':
    base_dir = "D:\projects\developing\\2023\FormalSpecification\\results\Mistral-7b\\categories"
    save_total(base_dir)

    data_set_path = "D:\projects\developing\\2023\FormalSpecification\data-set\HumanEvalPlus-v0.1.9.jsonl\HumanEvalPlus-v0.1.9.jsonl"
    problems = CommonUtil.read_jsonl(data_set_path)
    buggy_codes_path = "D:\projects\developing\\2023\FormalSpecification\\results\\bug-code\code.jsonl"
    eval_path = base_dir + "\\total\\latest.jsonl"
    complete_path = base_dir + "\\total\\latest_completeness.jsonl"

    to_eval_completeness(problems, buggy_codes_path, eval_path, complete_path)
