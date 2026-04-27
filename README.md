# LVLM Geolocation

Code for "From Snapshot to Snooping: From Snapshot to Snooping: An Empirical Study on Geolocation Privacy Leakage in Large Vision Language Models"

## Environment Setup

```bash
conda create -n lvlm_geo python==3.9.24
conda activate lvlm_geo
pip install -r requirements.txt
```

## Dataset

- **YFCC4K:** http://www.mediafire.com/file/3og8y3o6c9de3ye/yfcc4k.zip <br><br>
**Sample images:**
<p align="center">
<img height="120" alt="10735218284" src="https://github.com/user-attachments/assets/bd4013ee-e118-44e6-855d-6d181bf6e4a9" />
<img height="120" alt="11080170865" src="https://github.com/user-attachments/assets/b1f64b8e-b9c7-4fd7-b55a-a4e37884f044" />
<img height="120" alt="10644134743" src="https://github.com/user-attachments/assets/8b647184-e3ab-45e2-a30a-059b9275d516" />
<img height="120" alt="12138201714" src="https://github.com/user-attachments/assets/6808b028-a79c-4f94-ae24-bb23f91d9d44" />
<img height="120" alt="13862786315" src="https://github.com/user-attachments/assets/57cdf8ae-59ad-428a-8845-a4b799486e45" />
<img height="120" alt="2599735063" src="https://github.com/user-attachments/assets/0b659e62-d1ba-4c11-a8f9-add0ebbe3a26" />
<img height="120" alt="63253036" src="https://github.com/user-attachments/assets/1d03b72e-f304-4a62-b638-220e23701f44" />
<img height="120" alt="4726231685" src="https://github.com/user-attachments/assets/bb56add4-351a-44d0-a1e9-a3e5a3cf4d1e" />





</p>

- **Additional images from Flickr:** <br>
**Option 1.** Access flickr urls and ground truth geolocation in dataset/flickr6k/flickr6k_url.csv <br>
**Option 2.** run retriever.py to get extra images from Flickr <br><br>
**Sample images:**
<p align="center">
<img height="120" alt="africa_53463000878" src="https://github.com/user-attachments/assets/f9de8b19-b11d-45e9-9b01-2721b5e2cce3" />
<img height="120" alt="north_america_canada_prairies_22007337885" src="https://github.com/user-attachments/assets/1c983a8d-0087-4b1a-8e7b-40ef195068f3" />
<img height="120" alt="north_america_canada_prairies_38137028676" src="https://github.com/user-attachments/assets/e91a9eed-c6c6-4c2b-a489-69c8169ee798" />
<img height="120" alt="north_america_canada_qc_46980026642" src="https://github.com/user-attachments/assets/e9b03bed-d3d2-4d3e-8b8a-4d16e8bb1fb7" />
<img height="120" alt="africa_53496493907" src="https://github.com/user-attachments/assets/64644035-1787-41f4-9874-fa105f023c69" />
<img height="120" alt="north_america_canada_qc_49866640516" src="https://github.com/user-attachments/assets/e935ed9c-0984-47d1-93ad-92414a39eeda" />
<img height="120" alt="north_america_39815320893" src="https://github.com/user-attachments/assets/604757ce-dc88-40d9-8a78-84de7f4ef289" />
<img height="120" alt="north_america_45970235445" src="https://github.com/user-attachments/assets/d3be09b3-7a93-4351-9971-067a80fe6197" />



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

