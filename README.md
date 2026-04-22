# LVLM Geolocation

Code for "From Snapshot to Snooping: From Snapshot to Snooping: An Empirical Study on Geolocation Privacy Leakage in Large Vision Language Models"

## Environment Setup

```bash
conda create -n lvlm_geo python==3.9.24
conda activate lvlm_geo
pip install -r requirements.txt
```

## Dataset

- YFCC4K: http://www.mediafire.com/file/3og8y3o6c9de3ye/yfcc4k.zip
- Additional images from Flickr:
Option 1. Access flickr urls and ground truth geolocation in flickr6k_url.csv <br>
Option 2. run retriever.py to get extra images from Flickr


## Usage - crawl images from Flickr

Run `retriever.py`, set the following fields:

`API_KEY`:  your API key from Flickr (requires Flickr Pro) <br>
`API_SECRET`: your API secret from Flickr (requires Flickr Pro) <br>



## Usage - query the model

Run `query_0shot.py`, set the following fieds:

`API_KEY`: your personal OpenRouter API key <br>
`model`: OpenRouter model code <br>
`IMAGE_FOLDER`: path to the input image file <br>
`OUTPUT_CSV`: path to the prediction file <br>
`PROPMT_TEXT`

The OpenRouter codes of all 14 models we evaluated are as follows:
  
  * anthropic/claude-sonnet-4.5
  * anthropic/claude-opus-4.6
  * google/gemini-2.5-flash-image
  * google/gemini-3.1-pro-preview
  * mistralai/mistral-medium-3.1
  * mistralai/mistral-small-2603
  * x-ai/grok-4
  * x-ai/grok-4.20
  * meta-llama/llama-4-scout
  * meta-llama/llama-4-maverick
  * qwen/qwen2.5-vl-72b-instruct
  * qwen/qwen3.5-397b-a17b
  * openai/gpt-4o-mini
  * openai/o3


## Usage - evaluation

* run eval.py for distance-based evaluation, set the following fields:

`ground_truth_file`: path to the ground truth csv <br>
`predicted_file`: path to the prediction csv

* run eval-match.py for matching-based evaluation at city-/country-/continent-level, set the following fields:

`PRED_CSV`: path to the prediction csv <br>
`GT_CSV`: path to the ground truth csv <br>
`OUT_CSV`: path to the evaluation csv

## Reference

Nam Vo, Nathan Jacobs and James Hays. "Revisiting IM2GPS in the Deep Learning Era". ICCV 2017. <br>
Flickr API Documentation. https://www.flickr.com/services/api/ <br>
OpenRouter. Terms of Service. https://openrouter.ai/terms <br>
OpenRouter. OpenRouter API Documentation. https://openrouter.ai/docs/api-reference/overview

