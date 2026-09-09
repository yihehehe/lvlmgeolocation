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


**Distribution of datasets across multi-dimensional categories:** 
<img width="1350" height="455" alt="image" src="https://github.com/user-attachments/assets/97f4131b-601a-4ecc-9dfa-8c33e3639e05" />

**Example cases of category-level analysis:** 
<img width="1503" height="258" alt="image" src="https://github.com/user-attachments/assets/c64043c2-b501-40ee-b447-dc9a3a7c1941" />


</p>



## Usage - crawl images from Flickr

Run `retriever.py`, set the following fields:

`API_KEY`:  your API key from Flickr (requires Flickr Pro) <br>
`API_SECRET`: your API secret from Flickr (requires Flickr Pro) <br>



## Usage - query the model

Run `query_0shot.py`, set the following fields:

`API_KEY`: your personal OpenRouter API key <br>
`model`: OpenRouter model code <br>
`IMAGE_FOLDER`: path to the input image file <br>
`OUTPUT_CSV`: path to the prediction file <br>
`PROPMT_TEXT`

The OpenRouter codes of all 14 models we evaluated are as follows:
  
  * anthropic/claude-sonnet-4.5
  * anthropic/claude-opus-4.6
  * anthropic/claude-opus-4.8
  * google/gemini-2.5-flash-image
  * google/gemini-3.1-pro-preview
  * mistralai/mistral-medium-3.1
  * mistralai/mistral-small-2603
  * x-ai/grok-4
  * x-ai/grok-4.20
  * x-ai/grok-4.6
  * meta-llama/llama-4-scout
  * meta-llama/llama-4-maverick
  * qwen/qwen2.5-vl-72b-instruct
  * qwen/qwen3.5-397b-a17b
  * openai/gpt-4o-mini
  * openai/o3
  * openai/gpt-5.5
  * minimax/minimax-m3
  * moonshotai/kimi-k2.7-code


## Usage - evaluation

* run eval.py for distance-based evaluation; set the following fields:

`ground_truth_file`: path to the ground truth csv <br>
`predicted_file`: path to the prediction csv

* run eval-match.py for matching-based evaluation at city-/country-/continent-level, set the following fields:

`PRED_CSV`: path to the prediction csv <br>
`GT_CSV`: path to the ground truth csv <br>
`OUT_CSV`: path to the evaluation csv

## Ablation Studies Results

### Effect of Regional Features


### Effect of Image Quality 
**Effect of Color Information** 
To quantify the extent to which LVLMs rely on chromatic cues for geolocation, we perform a controlled color-channel ablation. Specifically, we randomly sample a fixed subset of 100 RGB images from the dataset and construct a paired grayscale image for each. To avoid confounding changes in model input format, grayscale images are replicated across three channels and normalized identically to the RGB originals. Each of the three top-performing LVLMs (e.g., Claude-Opus-4.6, Gemini-3.1-Pro, and OpenAI o3) is evaluated on both the original RGB images and their grayscale counterparts under the zero-shot prompt. As shown in Table 7, the geolocation inference performance on grayscale images consistently decreases across all three LVLMs, with GeoScore dropping by −150.00 for Claude-Opus-4.6, −96.51 for Gemini-3.1-Pro, and −29.25 for o3, which confirms that color carries meaningful geolocation information by encoding region-specific cues such as vegetation hues, facade palettes, and distinctive color schemes of road signage and infrastructure. Furthermore, the Acc@25 km impact is comparatively mild with at most −3.00%, suggesting that color primarily refines distance-level precision rather than determining coarse location identity.
  
**Effect of Image Resolution** 
To assess how visual detail affects geolocation performance, we construct lower-resolution variants of a subset with 100 images using a controlled downsample-upsample procedure. For each image, we resize it downward so that its short side matches a predefined target resolution (e.g., 512, 256, or 128 pixels) while preserving the original aspect ratio, and then resize it back to the original dimensions using an upsampling method. This two-step operation ensures that every degraded image retains the same width and height as the original while progressively removing high-frequency details such as small text, distant signage, road markings, and fine textures. For example, an original image of size 1024×684 is downgraded to approximately 766 × 512 (DS512), 383 × 256 (DS256), and 192 × 128 (DS128), corresponding to 44.0%, 86.0%, and 96.5% reductions in pixel count relative to the original. As shown in Table 7, at mild blur (DS512), geolocation inference performance remains largely stable and in some cases even improves slightly (e.g., Gemini-3.1-Pro: +2.00% Acc@25 km, o3: +4.00%), which indicates that large-scale structures are preserved and sufficient for coarse geolocation. At medium blur (DS256), these LVLMs begin to show consistent degradation, with Gemini-3.1-Pro dropping by 154.54 in GeoScore. The strongest blur (DS128) produces the most obvious decrease across all models, with Gemini-3.1-Pro suffering the largest loss (−16.00% Acc@25 km, −632.32 GeoScore), followed by Claude-Opus-4.6 (−8.00% Acc@25km, −329.86 GeoScore). These results show that fine-grained visual cues, such as text on signage and detailed architectural features, are critical for accurate geolocation and are progressively lost as resolution decreases.

### Effect of Prompt Language

We investigate whether the language of the prompt affects geolocation performance by comparing an English prompt to a semantically equivalent zero-shot prompt written in the primary language of the image’s ground-truth country. Specifically, we sampled 50 images from the dataset for each of five countries (e.g., France, Russia, Germany, China, and Japan) and prepared two prompt variants per country: one in English and one in the respective native language. We report Acc@25 km and GeoScore under both prompting conditions for three top-performing LVLMs: Claude-Opus-4.6, Gemini-3.1-Pro, and OpenAI o3. The results are presented in Table 7. Across the 15 paired comparisons (5 languages × 3 models), 11 out of 15 demonstrate a higher GeoScore when the prompt is written in the native language, indicating that prompt language is a non-trivial factor in LVLM geolocation performance. The effect is most obvious for European languages: Russian prompts show the largest gains for Gemini-3.1-Pro (+412.61 GeoScore) and o3 (+10.25% Acc@25 km), while German prompts lead to a drastic improvement for OpenAI o3 (+29.25% Acc@25 km, +535.88 GeoScore). On the other hand, the benefit is less consistent for East Asian languages. For Chinese prompts, both Gemini-3.1-Pro and o3 show slight performance drops, and for Japanese prompts, Gemini-3.1-Pro declines by 6.00% in Acc@25 km and 129.87 in GeoScore. A plausible explanation is that native-language prompts better align with the LVLM’s instruction-tuning distribution for languages that are well represented in its training data, thereby more reliably eliciting geolocation-relevant reasoning, and the alignment advantage might not hold for less represented languages. In addition, native-language prompts may increase the model’s sensitivity to text-based visual evidence such as signage, place names, and scripts, effectively priming it toward linguistic cue extraction, which is particularly beneficial when the visible text in the image matches the prompt language.

 **Ablation studies on prompt language, color mode, and image resolution.**
 <img width="1287" height="466" alt="image" src="https://github.com/user-attachments/assets/0ecfaff8-6f48-4f80-8d34-59f6186e7b3a" />


## Reference

Nam Vo, Nathan Jacobs and James Hays. "Revisiting IM2GPS in the Deep Learning Era". ICCV 2017. <br>
Flickr API Documentation. https://www.flickr.com/services/api/ <br>
OpenRouter. Terms of Service. https://openrouter.ai/terms <br>
OpenRouter. OpenRouter API Documentation. https://openrouter.ai/docs/api-reference/overview

