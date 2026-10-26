import os
import time
import requests
import json
import csv
import base64
from datetime import datetime

# OpenRouter API configuration
API_KEY = " "
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Input configuration
PROMPT_TEXT =  """


    """


IMAGE_FOLDER = " "
OUTPUT_CSV = " "

# --- New: operational settings ---
REQUESTS_TIMEOUT = 120      # seconds before a single request times out
RATE_LIMIT_DELAY = 1.0      # seconds to wait between consecutive requests
MAX_RETRIES = 3             # retries on timeout / transient server errors (5xx)

# --- New: cost tracking ---
COST_LOG = ""               # optional path; if empty, cost is only printed to console
ACCUMULATED_COST = 0.0      # running total, updated in-place


# Function to encode an image as Base64
def encode_image_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

# Function to query the OpenRouter API for visual question answering
def query_model(data_url):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": " ", # openrouter model
        "provider": {
             "allow_fallbacks": True
        },
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT_TEXT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]
            }
        ]
    }

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                url=API_URL,
                headers=headers,
                data=json.dumps(data),
                timeout=REQUESTS_TIMEOUT,
            )
        except requests.exceptions.Timeout:
            print(f"  [Timeout] attempt {attempt}/{MAX_RETRIES} — request exceeded {REQUESTS_TIMEOUT}s")
            last_error = "timeout"
            time.sleep(2 * attempt)  # incremental backoff
            continue
        except requests.exceptions.ConnectionError as e:
            print(f"  [ConnectionError] attempt {attempt}/{MAX_RETRIES}: {e}")
            last_error = str(e)
            time.sleep(2 * attempt)
            continue

        if response.status_code == 200:
            return response  # raw response object so caller can extract cost headers
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after else (5 * attempt)
            print(f"  [Rate-limited (429)] attempt {attempt}/{MAX_RETRIES} — waiting {wait:.0f}s")
            time.sleep(wait)
            last_error = "rate_limit"
            continue
        elif response.status_code >= 500:
            print(f"  [Server error ({response.status_code})] attempt {attempt}/{MAX_RETRIES}")
            time.sleep(2 * attempt)
            last_error = f"server_error_{response.status_code}"
            continue
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None

    print(f"  All {MAX_RETRIES} attempts failed ({last_error})")
    return None


def extract_cost(response):
    """Extract token usage and USD cost from an OpenRouter response.  Returns a dict."""
    info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0}

    # Try response body (usage block)
    try:
        body = response.json()
        usage = body.get("usage") or {}
        info["prompt_tokens"]     = usage.get("prompt_tokens", 0) or 0
        info["completion_tokens"] = usage.get("completion_tokens", 0) or 0
        info["total_tokens"]      = usage.get("total_tokens", 0) or 0
    except Exception:
        pass

    # Try response headers for pricing
    # OpenRouter sometimes puts cost in headers (varies by provider)
    cost_header = response.headers.get("x-openrouter-cost") or response.headers.get("X-OpenRouter-Cost")
    if cost_header:
        try:
            info["cost_usd"] = float(cost_header)
        except ValueError:
            pass

    # Fallback: if no header cost but tokens are present, try to parse pricing from
    # the 'upstream_cost' or another header
    if info["cost_usd"] == 0.0:
        upstream = (
            response.headers.get("x-openrouter-upstream-cost")
            or response.headers.get("X-OpenRouter-Upstream-Cost")
        )
        if upstream:
            try:
                info["cost_usd"] = float(upstream)
            except ValueError:
                pass

    # Also inspect the body for pricing info (some providers embed cost)
    if info["cost_usd"] == 0.0:
        try:
            body = response.json()
            pricing = body.get("pricing") or body.get("cost") or {}
            if isinstance(pricing, dict):
                info["cost_usd"] = float(pricing.get("total", 0) or 0)
        except Exception:
            pass

    return info


def process_response(response):
    # defensive extraction + logging for debugging
    try:
        if not isinstance(response, dict):
            print("Unexpected response type:", type(response))
            return None

        choices = response.get("choices")
        if not choices or not isinstance(choices, list):
            print("No choices in response:", json.dumps(response)[:1000])
            return None

        choice0 = choices[0]
        message = choice0.get("message") if isinstance(choice0, dict) else None
        if not message:
            print("No message in first choice:", json.dumps(choice0)[:1000])
            return None

        content = message.get("content")
        # content may be a string or a list of blocks
        if isinstance(content, list):
            # join text fields if present
            text = "".join(
                (block.get("text") if isinstance(block, dict) else str(block))
                for block in content
            )
        else:
            text = str(content)

        text = text.strip()
        if not text:
            print("Empty content in response:", json.dumps(response)[:1000])
            return None

        return text

    except Exception as e:
        print("Error processing response:", e)
        print("Full response (truncated):", json.dumps(response)[:2000])
        return None



# Main function to iterate through images, query the model, and save results
def main():
    global ACCUMULATED_COST

    # Get list of images in the folder
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('jpg', 'jpeg', 'png'))]
    total_images = len(image_files)
    processed = 0

    # Open cost log if path is provided
    cost_writer = None
    cost_csvfile = None
    if COST_LOG:
        cost_csvfile = open(COST_LOG, mode='w', newline='', encoding='utf-8')
        cost_writer = csv.writer(cost_csvfile)
        cost_writer.writerow(["timestamp", "filename", "prompt_tokens", "completion_tokens",
                              "total_tokens", "cost_usd", "accumulated_cost_usd"])

    # Open CSV file for writing results
    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["filename", "raw_res"])

        for image_file in image_files:
            # --- Rate limiting: wait before each request (skip first) ---
            if processed > 0:
                time.sleep(RATE_LIMIT_DELAY)

            image_path = os.path.join(IMAGE_FOLDER, image_file)
            image_base64 = encode_image_base64(image_path)
            data_url = f"data:image/jpeg;base64,{image_base64}"

            if not image_base64:
                print(f"Skipping image due to encoding error: {image_file}")
                continue

            print(f"Processing image [{processed+1}/{total_images}]: {image_file}")

            # Query the model (returns raw requests.Response on success)
            http_response = query_model(data_url)
            if http_response:
                # Extract cost info before parsing the body text
                cost_info = extract_cost(http_response)
                ACCUMULATED_COST += cost_info["cost_usd"]
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                print(f"  Tokens: {cost_info['total_tokens']} "
                      f"(prompt={cost_info['prompt_tokens']}, "
                      f"completion={cost_info['completion_tokens']}) | "
                      f"Cost: ${cost_info['cost_usd']:.6f} | "
                      f"Accumulated: ${ACCUMULATED_COST:.4f}")

                if cost_writer:
                    cost_writer.writerow([
                        ts, image_file,
                        cost_info["prompt_tokens"],
                        cost_info["completion_tokens"],
                        cost_info["total_tokens"],
                        f"{cost_info['cost_usd']:.6f}",
                        f"{ACCUMULATED_COST:.4f}",
                    ])
                    cost_csvfile.flush()

                # Process the model's text response
                response_body = http_response.json()
                text = process_response(response_body)

                # Write to CSV
                csv_writer.writerow([image_file, text])
            else:
                print(f"  Skipping image due to query error: {image_file}")

            processed += 1

    if cost_csvfile:
        cost_csvfile.close()

    # Final cost summary
    print(f"\nProcessing complete. Results saved to {OUTPUT_CSV}")
    print(f"Total images attempted: {processed}")
    print(f"Total accumulated cost: ${ACCUMULATED_COST:.4f}")


# Run the script
if __name__ == "__main__":
    main()