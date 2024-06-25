import json


def read_jsonl(filepath):
    lines = open(filepath, "r").read().split("\n")
    jsonl = [json.loads(line) for line in lines if line]
    jsonl = {task["task_id"]: task for task in jsonl if "task_id" in task.keys()}
    return jsonl


def read_file(filepath):
    lines = open(filepath, "r").read().split("\n")
    jsonl = [json.loads(line) for line in lines if line]
    return jsonl
