import json
import requests
from exacter import Exacter


def is_valid_response(response):
    res = Exacter.exact(response)
    res = Exacter.filter_valid_postconds(res)
    return len(res) != 0


def generate_prompt_v2(prompt_version, problem, post_cond):
    nl_descp = problem["prompt"]
    prompt = open(f"../prompts/{prompt_version}.txt", "r").read()
    prompt = prompt.replace("{{{natural_language_specification}}}", nl_descp)
    prompt = prompt.replace("{{{wrong_post-condition}}}", post_cond)

    return prompt


def generate_prompt(prompt_version, problem):
    function_name = problem["entry_point"]
    nl_descp = problem["prompt"]
    prompt = open(f"./prompts/{prompt_version}.txt", "r").read()
    prompt = prompt.replace("{{{function_name}}}", function_name)
    prompt = prompt.replace("{{{natural_language}}}", nl_descp)
    return prompt


def generate_postcond(prompt):
    # API_URL = "https://api-inference.huggingface.co/models/google/gemma-7b"
    # API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    API_URL = "https://api-inference.huggingface.co/models/google/gemma-1.1-7b-it"

    # headers = {"Authorization": "Bearer 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"}
    headers = {"Authorization": "Bearer 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"}
    proxies = {
        "http": "http://127.0.0.1:7890",
        "https": "http://127.0.0.1:7890",
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "return_full_text": False,
            "max_new_tokens": 256,
            "temperature": 0.7
        },
        "options": {
            "use_cache": False
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, proxies=proxies)
    except Exception:
        response = requests.post(API_URL, headers=headers, json=payload, proxies=proxies)

    return response.json()


def to_response(problems, responses, prompt_version, res_path):
    with open(res_path, "ab") as fp:
        for key, value in responses.items():
            time = 0
            while len(value) < 5 and time < 10:
                time += 1

                prompt = generate_prompt(prompt_version, problems[key])
                response = generate_postcond(prompt)
                result = {"task_id": key}
                result.update(response[0])

                print(key)
                print(response[0]["generated_text"])
                print("----")

                if is_valid_response(response[0]["generated_text"]) or 10 - time == 5 - len(value):
                    value.append(result)
                    fp.write((json.dumps(result) + "\n").encode("utf-8"))
