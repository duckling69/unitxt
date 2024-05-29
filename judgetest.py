from datasets import load_dataset
from unitxt import evaluate
from unitxt.inference import IbmGenAiInferenceEngine, IbmGenAiInferenceEngineParams

# 1. Create the dataset
card = (
    "card=cards.safety.simple_safety_tests,"
    "template=templates.empty,"
    "format=formats.empty,"
    "metrics=[metrics.llm_as_judge.safety.llama_3_70b_instruct_ibm_genai_template_unsafe_content],"
    "data_classification_policy=['public']"
)

dataset = load_dataset("unitxt/data", card, split="test")
# 2. use inference module to infer based on the dataset inputs.
gen_params = IbmGenAiInferenceEngineParams(max_new_tokens=32)
inference_model = IbmGenAiInferenceEngine(
    model_name="ibm/granite-13b-chat-v2", parameters=gen_params
)
predictions = inference_model.infer(dataset)

# 3. create a metric and evaluate the results.
scores = evaluate(predictions=predictions, data=dataset)

# [print(item) for item in scores[0]["score"]["global"].items()]
