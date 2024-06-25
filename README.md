# PostcondGen

Codes for generating and evaluating postconditions using code comments in EvalPlus based on Large Language Model and Maturity Model.

## Perquisites

### HUGGINGFACE API Key

To access HUGGINGFACE API, you need a personal API key. Please fill your own API key into `api_key.txt`.

## Usage

To run PostcondGen, use command

```
python main.py
```

## Project Structure

+ codegen: to generate code mutants for EvalPlus problems.
+ condgen: to generate postcondtions for EvalPlus problems.
+ evaluator: to evaluate the quality of LLM-generated postconditions.
+ exacter: to exact the postcondtions from LLM response text.
+ prompts: various prompts for generating different categories of postondtions.
+ util: utility codes.