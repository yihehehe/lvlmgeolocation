# lvlmgeolocation

## Requirements

- python 3.9.24
- dependencies listed in requirements.txt


## Datasets

- public benchmark YFCC4K: http://www.mediafire.com/file/3og8y3o6c9de3ye/yfcc4k.zip
- additional image from Flickr: run script retriever_flickr.py, get API key with Flickr Pro.


## query the model

- run query_0shot.py with OpenRouter API key, the OpenRouter codes for all 14 models we evaluated are as follows:
  
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

## Evaluation


Reference:

* Nam Vo, Nathan Jacobs and James Hays. "Revisiting IM2GPS in the Deep Learning Era". ICCV 2017.
* Flickr API Documentation. https://www.flickr.com/services/api/. 
