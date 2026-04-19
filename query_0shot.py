import os
import requests
import json
import csv
import base64

# OpenRouter API configuration
API_KEY = " "   
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Input configuration
PROMPT_TEXT =  """

You are an expert geolocation analyst, please predict the geolocation for the provided imagery with utmost precision.  

You must give the answer that strictly uses the following format in the SAME line: 
	
    1. LATITUDE: ; 2. LONGITUDE: ; 3. LOCATION: (the according city, country and continent)

    Do not include any other content other than the above three pieces of information.
    
    
    """
 
        
        
IMAGE_FOLDER = " "
OUTPUT_CSV = " "  

# Function to encode an image as Base64
def encode_image_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
        
        
            # base64_image = base64.b64encode(image_file.read()).decode("utf-8")
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
    
    response = requests.post(url=API_URL, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

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
    # Get list of images in the folder
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('jpg', 'jpeg', 'png'))]
    
    # Open CSV file for writing results
    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        #  csv_writer.writerow(["filename","response"])
        csv_writer.writerow(["filename", "raw_res"])
        
        for image_file in image_files:

            image_path = os.path.join(IMAGE_FOLDER, image_file)
            image_base64 = encode_image_base64(image_path)
            data_url = f"data:image/jpeg;base64,{image_base64}"
            
            if not image_base64:
                print(f"Skipping image due to encoding error: {image_file}")
                continue
            
            print(f"Processing image: {image_file}")
            
            # Query the model
            response = query_model(data_url)
            if response:
                # Process the model's response
                response = process_response(response)
                
                # Write to CSV
                csv_writer.writerow([image_file, response])
            else:
                print(f"Skipping image due to query error: {image_file}")
    
    print(f"Processing complete. Results saved to {OUTPUT_CSV}")

# Run the script
if __name__ == "__main__":
    main()
