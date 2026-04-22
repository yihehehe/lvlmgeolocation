import flickrapi
import requests
import os
import csv
import time
import random
from pathlib import Path
from tqdm import tqdm
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import reverse_geocoder as rg
from PIL import Image
import io

class FlickrStreetViewCrawler:
    def __init__(self, api_key, api_secret, output_dir="flickr_dataset"):
        self.flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        self.geolocator = Nominatim(user_agent="flickr_geolocation")
        
        # Worldwide bounding boxes for balanced distribution
        self.regions = {
            'north_america': {'bbox': '-125,25,-65,50', 'target': 1000},
            'europe': {'bbox': '-10,35,40,60', 'target': 1000},
            'asia': {'bbox': '60,0,150,50', 'target': 1000},
            'south_america': {'bbox': '-80,-40,-35,15', 'target': 600},
            'africa': {'bbox': '-20,-35,50,35', 'target': 600},
            'oceania': {'bbox': '110,-45,180,-10', 'target': 400},
            'central_america': {'bbox': '-92,8,-77,23', 'target': 200},
            'middle_east': {'bbox': '25,15,60,40', 'target': 200}
        }
        
        # Street view related tags
        self.street_tags = [
            'street', 'streetview', 'streetphotography', 'urban', 'city',
            'building', 'architecture', 'road', 'cityscape', 'downtown',
            'town', 'citylife', 'urbanphotography', 'streetscape',
            'citystreet', 'urbanexploration'
        ]
        
        self.downloaded_images = set()
        self.metadata = []
    
    def reverse_geocode(self, lat, lon):
        """Reverse geocode coordinates to get country and location info"""
        try:
            # First try with reverse_geocoder (fast)
            result = rg.search((lat, lon))[0]
            country = result['cc']
            city = result['name']
            admin1 = result['admin1']
            
            # Then get more details with geopy
            time.sleep(1)  # Rate limiting
            location = self.geolocator.reverse(f"{lat}, {lon}", exactly_one=True, language='en')
            if location:
                address = location.raw.get('address', {})
                country = address.get('country', country)
                city = address.get('city') or address.get('town') or address.get('village') or city
            
            return {
                'country': country,
                'city': city,
                'region': admin1,
                'full_address': location.address if location else None
            }
        except (GeocoderTimedOut, Exception) as e:
            print(f"Geocoding failed for ({lat}, {lon}): {e}")
            return {'country': 'Unknown', 'city': 'Unknown', 'region': 'Unknown', 'full_address': None}
    
    def is_street_view_image(self, photo_info):
        """Check if image appears to be a street view"""
        try:
            # Check tags
            tags = photo_info.get('tags', {}).get('tag', [])
            tag_list = [tag.get('_content', '').lower() for tag in tags]
            
            # Check description and title
            description = photo_info.get('description', {}).get('_content', '').lower()
            title = photo_info.get('title', {}).get('_content', '').lower()
            
            # Street view indicators
            street_indicators = [
                'street', 'city', 'urban', 'building', 'road', 
                'downtown', 'town', 'cityscape', 'architecture', 'travel', 
                'photography', 'street view', 'scenic nature', 'nature', 'streetphoto'
            ]
            
            for indicator in street_indicators:
                if (indicator in tag_list or 
                    indicator in title or 
                    indicator in description):
                    return True
            
            return False
        except Exception as e:
            print(f"Error checking street view: {e}")
            return True  
    
    def download_image(self, photo_info, region_name):
        """Download individual image and return success status"""
        try:
            photo_id = photo_info['id']
            
            # Get available sizes
            sizes = self.flickr.photos.getSizes(photo_id=photo_id)
            size_info = sizes['sizes']['size']
            
            # Prefer large sizes
            preferred_sizes = ['Large', 'Medium', 'Original', 'Large 1600', 'Large 2048']
            image_url = None
            
            for size in preferred_sizes:
                for size_data in size_info:
                    if size_data['label'] == size:
                        image_url = size_data['source']
                        break
                if image_url:
                    break
            
            if not image_url:
                for size_data in size_info:
                    if size_data['label'] == 'Medium':
                        image_url = size_data['source']
                        break
            
            if not image_url:
                print(f"No suitable image size found for {photo_id}")
                return False

            response = requests.get(image_url, timeout=30)
            if response.status_code != 200:
                return False
            
            # Verify valid image
            try:
                img = Image.open(io.BytesIO(response.content))
                img.verify()
                
                if img.size[0] < 800 or img.size[1] < 600:
                    return False
                    
            except Exception:
                return False
            
            filename = f"{region_name}_{photo_id}.jpg"
            filepath = self.images_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return True, filename, image_url
            
        except Exception as e:
            print(f"Download failed: {e}")
            return False, None, None
    
    def search_region_images(self, region_name, bbox, target_count, max_per_page=100):
        """Search for images in a specific region"""
        region_images = []
        page = 1
        total_pages = 1
        
        print(f"🔍 Searching {region_name}...")
        
        while len(region_images) < target_count and page <= total_pages:
            try:
                # Search with geographic and street view filters
                photos = self.flickr.photos.search(
                    bbox=bbox,
                    has_geo=1,
                    tags=','.join(random.sample(self.street_tags, 5)),  # Random tags for variety
                    tag_mode='any',
                    extras='geo, tags, description, url_m, url_o, license',
                    per_page=max_per_page,
                    page=page,
                    sort='relevance'  # Get more relevant street views
                )
                
                if not photos or 'photos' not in photos:
                    break
                
                photos_data = photos['photos']
                total_pages = min(photos_data['pages'], 10)  # Limit pages to avoid timeout
                
                for photo in photos_data['photo']:
                    if len(region_images) >= target_count:
                        break
                    
                    photo_id = photo['id']
                    
                    # Skip if already downloaded
                    if photo_id in self.downloaded_images:
                        continue
                    
                    # Get detailed photo info
                    try:
                        photo_info = self.flickr.photos.getInfo(photo_id=photo_id)
                        photo_info = photo_info['photo']
                        
                        # Check if it's a street view
                        if not self.is_street_view_image(photo_info):
                            continue
                        
                        # Get coordinates
                        lat = float(photo_info['location']['latitude'])
                        lon = float(photo_info['location']['longitude'])
                        
                        # Download image
                        success, filename, image_url = self.download_image(photo_info, region_name)
                        if not success:
                            continue
                        
                        # Reverse geocode for location info
                        location_info = self.reverse_geocode(lat, lon)
                        
                        # metadata
                        image_data = {
                            'image_id': photo_id,
                            'filename': filename,
                            'region': region_name,
                            'latitude': lat,
                            'longitude': lon,
                            'country': location_info['country'],
                            'city': location_info['city'],
                            'region_name': location_info['region'],
                            'full_address': location_info['full_address'],
                            'title': photo_info.get('title', {}).get('_content', ''),
                            'description': photo_info.get('description', {}).get('_content', ''),
                            'tags': '|'.join([tag.get('_content', '') for tag in photo_info.get('tags', {}).get('tag', [])]),
                            'image_url': image_url,
                            'flickr_url': f"https://www.flickr.com/photos/{photo_info['owner']['nsid']}/{photo_id}",
                            'license': photo_info.get('license', ''),
                            'date_taken': photo_info.get('dates', {}).get('taken', ''),
                        }
                        
                        region_images.append(image_data)
                        self.downloaded_images.add(photo_id)
                        
                        print(f"✅ Downloaded {len(region_images)}/{target_count} for {region_name}")
                        
                        # Rate limiting
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"Error processing photo {photo_id}: {e}")
                        continue
                
                page += 1
                time.sleep(1)  # Rate limiting between pages
                
            except Exception as e:
                print(f"Search error in {region_name}, page {page}: {e}")
                break
        
        return region_images
    
    def crawl_balanced_dataset(self, total_target=5000):
        """Crawl images with balanced worldwide distribution"""
        print(f" Starting crawl for {total_target} images")
        
        all_images = []
        
        for region_name, region_info in self.regions.items():
            if len(all_images) >= total_target:
                break
            
            target = min(region_info['target'], total_target - len(all_images))
            bbox = region_info['bbox']
            
            region_images = self.search_region_images(region_name, bbox, target)
            all_images.extend(region_images)
            
            print(f" Completed {region_name}: {len(region_images)} images")
            
            # Save progress after each region
            self.save_metadata(all_images)
            
            # Longer break between regions
            time.sleep(5)
        
        print(f" Crawling complete! Downloaded {len(all_images)} images")
        return all_images
    
    def save_metadata(self, metadata, filename="flickr_metadata.csv"):
        """Save metadata to CSV file"""
        if not metadata:
            return
        
        df = pd.DataFrame(metadata)
        csv_path = self.output_dir / filename
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"💾 Metadata saved: {csv_path}")
    
    def analyze_distribution(self, metadata):
        """Analyze geographic distribution of downloaded images"""
        if not metadata:
            return
        
        df = pd.DataFrame(metadata)
        
        print("\nDistribution Analysis:")
        print("By Region:")
        print(df['region'].value_counts())
        print("\nBy Country:")
        print(df['country'].value_counts().head(10))
        
        # Save distribution report
        distribution_report = {
            'total_images': len(metadata),
            'regions': df['region'].value_counts().to_dict(),
            'top_countries': df['country'].value_counts().head(20).to_dict()
        }
        
        import json
        with open(self.output_dir / 'distribution_report.json', 'w') as f:
            json.dump(distribution_report, f, indent=2)

def main():
    API_KEY = " "
    API_SECRET = " "
    
    # Initialize crawler
    crawler = FlickrStreetViewCrawler(API_KEY, API_SECRET, "flickr_streetview_dataset")
    
    # Start crawling
    metadata = crawler.crawl_balanced_dataset(total_target=5000)
    
    # Analyze distribution
    crawler.analyze_distribution(metadata)
    
    print(f"📁 Saved in: {crawler.output_dir}")

if __name__ == "__main__":
    main()
