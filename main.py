from util import CommonUtil
from condgen import CondGen
from evaluator import Evaluator
import os

def main():
    data_set_path = "file_path"
    buggy_codes_path = "file_path"
    problems = CommonUtil.read_jsonl(data_set_path)

    base_dir = "file_path"
    prompt_version = "0shot"
    targets = problems.keys()

    res_dir = base_dir + "answer\\"
    os.makedirs(res_dir, exist_ok=True)
    res_path = res_dir + "answer.jsonl"
    eval_path = base_dir + "eval.jsonl"
    complete_path = base_dir + "completeness.jsonl"

    responses = {i: [] for i in targets}
    if os.path.isfile(res_path):
        current_responses = CommonUtil.read_file(res_path)
        for each in current_responses:
            if each["task_id"] in responses.keys():
                responses[each["task_id"]].append(each)

    CondGen.to_response(problems, responses, prompt_version, res_path)

    Evaluator.to_eval_correctness(problems, targets, prompt_version, res_path, eval_path)
    Evaluator.to_eval_completeness(problems, buggy_codes_path, eval_path, complete_path)
