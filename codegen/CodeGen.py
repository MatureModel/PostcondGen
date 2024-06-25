import json
import requests
from util import CommonUtil
from CodeFilter import test_buggy_codes

# 1. generate code
# 2. filter code
# 3. data struct
def gen_prompt(s):
    pre = "# Please include a bug in your implementation of the following function.\n"
    return pre + s


def generate_code(prompt):
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": "API_KEY"}

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


def main():
    codes_path = "filepath"
    data_set_path = "filepath"
    buggy_codes_path = "filepath"

    problems = CommonUtil.read_jsonl(data_set_path)
    codes = CommonUtil.read_file(codes_path)

    tmp = {"HumanEval/" + str(i): [] for i in range(164)}
    for each in codes:
        if each["task_id"] in tmp.keys():
            tmp[each["task_id"]].append(each)

    for key, value in tmp.items():
        if len(value) < 50:
            value.append(save_mutants(problems, [key], codes_path, 50 - len(value)))
        test_buggy_codes(key, value, buggy_codes_path)

if __name__ == '__main__':
    main()