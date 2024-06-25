import json
import requests
from util import CommonUtil

# 1. generate code
# 2. filter code
# 3. data struct
def gen_prompt(s):
    pre = "# Please include a bug in your implementation of the following function.\n"
    return pre + s


def generate_code(prompt):
    # API_URL = "https://api-inference.huggingface.co/models/google/gemma-7b-it"
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": "Bearer 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"}
    # headers = {"Authorization": "Bearer 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"}

    proxies = {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890",
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "return_full_text": True,
            "max_new_tokens": 256,
            "temperature": 0.9
        },
        "options": {
            "use_cache": False
        }
    }
    response = requests.post(API_URL, headers=headers, json=payload, proxies=proxies)
    return response.json()


def save_mutants(problems, targets, file_path, num):
    result = []
    with open(file_path, "ab") as fp:
        for p in targets:
            for i in range(num):
                tmp = {"task_id": p}
                response = generate_code(gen_prompt(problems[p]["prompt"]))
                # print(response)
                tmp.update(response[0])

                print("-----------------" + p + "---------------")
                print(tmp["generated_text"])
                fp.write((json.dumps(tmp) + "\n").encode("utf-8"))
                result.append(tmp)
    return result


if __name__ == '__main__':
    file_path = "D:\projects\developing\\2023\FormalSpecification\data-set\HumanEvalPlus-Mini-v0.1.9.jsonl\\results\\bug-code\\natural\\answers\code_plus.jsonl"
    data_set_path = "D:\projects\developing\\2023\FormalSpecification\data-set\HumanEvalPlus-Mini-v0.1.9.jsonl\\HumanEvalPlus-Mini-v0.1.9.jsonl"
    problems = CommonUtil.read_jsonl(data_set_path)
    codes = CommonUtil.read_file(file_path)

    tmp = {"HumanEval/" + str(i): [] for i in [2, 8, 13, 19, 29, 30, 34, 35, 42, 45, 49, 50, 55, 60, 67, 72, 76, 139, 162]}
    for each in codes:
        if each["task_id"] in tmp.keys():
            tmp[each["task_id"]].append(each)

    for key, value in tmp.items():
        if len(value) < 50:
            save_mutants(problems, [key], file_path, 50 - len(value))
