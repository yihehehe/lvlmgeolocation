# LVLM Geolocation

Code for "From Snapshot to Snooping: From Snapshot to Snooping: An Empirical Study on Geolocation Privacy Leakage in Large Vision Language Models"

## Environment Setup

```bash
conda create -n lvlm_geo python==3.9.24
conda activate lvlm_geo
pip install -r requirements.txt
```

## Dataset

- YFCC4K: http://www.mediafire.com/file/3og8y3o6c9de3ye/yfcc4k.zip <br>
Sample images:
<p align="center">
<img height="160" alt="10735218284" src="https://github.com/user-attachments/assets/bd4013ee-e118-44e6-855d-6d181bf6e4a9" />
<img height="160" alt="11080170865" src="https://github.com/user-attachments/assets/b1f64b8e-b9c7-4fd7-b55a-a4e37884f044" />
<img height="160" alt="10644134743" src="https://github.com/user-attachments/assets/8b647184-e3ab-45e2-a30a-059b9275d516" />
<img height="160" alt="12138201714" src="https://github.com/user-attachments/assets/6808b028-a79c-4f94-ae24-bb23f91d9d44" />
<img height="160" alt="13862786315" src="https://github.com/user-attachments/assets/57cdf8ae-59ad-428a-8845-a4b799486e45" />
</p>

- Additional images from Flickr: <br>
Option 1. Access flickr urls and ground truth geolocation in flickr6k_url.csv <br>
Option 2. run retriever.py to get extra images from Flickr <br>
Sample images:
<p align="center">
<img width="1023" height="625" alt="africa_53463000878" src="https://github.com/user-attachments/assets/f9de8b19-b11d-45e9-9b01-2721b5e2cce3" />
<img width="800" height="1024" alt="africa_53434010756" src="https://github.com/user-attachments/assets/4da2924e-44d5-4931-99f4-05faf74301d9" />
<img width="1023" height="753" alt="africa_53437671733" src="https://github.com/user-attachments/assets/503c862c-6285-457d-8daf-dfda8a74be8e" />
<img width="1024" height="882" alt="africa_53471545404" src="https://github.com/user-attachments/assets/268192eb-9fac-45c7-9c45-033fa3e087cf" />
<img width="1024" height="683" alt="africa_53496493907" src="https://github.com/user-attachments/assets/64644035-1787-41f4-9874-fa105f023c69" />
</p>



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

