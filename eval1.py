import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
import warnings
warnings.filterwarnings('ignore')



def geoscore(lat_gt, lon_gt, lat_pred, long_pred, max_score=5000.0, decay_constant=1492.7, max_distance_km=20037.5):

    distance_km = haversine_distance(lat_gt, lon_gt, lat_pred, long_pred)
    if distance_km >= max_distance_km:
        return 0.0

    return max_score * np.exp(-distance_km / decay_constant)


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points 
    on the Earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine distance
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    r = 6371  # Radius of Earth in km
    return c * r

def clean_and_match_data(ground_truth_df, predicted_df):
    """
    Clean data and match images between the two datasets
    """
    # Basic cleaning: strip whitespace from string columns
    string_columns = ['city', 'country', 'continent']
    for df in [ground_truth_df, predicted_df]:
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.lower()
    
    common_columns = ground_truth_df.columns.intersection(predicted_df.columns)
    
     # identifier column
    possible_id_columns = ['filename', 'image_id']
    image_id_col = None
    
    for col in possible_id_columns:
        if col in common_columns:
            image_id_col = col
            break
    
    if image_id_col:
        print(f"Using '{image_id_col}' to match images between datasets")
        # Merge datasets on the image identifier
        merged_df = pd.merge(
            ground_truth_df, 
            predicted_df, 
            on=image_id_col, 
            suffixes=('_gt', '_pred'),
            how='inner'
        )
        print(f"Successfully matched {len(merged_df)} images")
    else:
        print("Warning: No common image identifier found. Assuming rows are in same order.")
        print(f"Ground truth rows: {len(ground_truth_df)}, Predicted rows: {len(predicted_df)}")
        
        # Reset indices to ensure alignment
        ground_truth_df = ground_truth_df.reset_index(drop=True)
        predicted_df = predicted_df.reset_index(drop=True)
        
        # Use minimum length to avoid index errors
        min_len = min(len(ground_truth_df), len(predicted_df))
        ground_truth_df = ground_truth_df.head(min_len)
        predicted_df = predicted_df.head(min_len)
        
        # Combine datasets by column
        merged_df = ground_truth_df.copy()
        for col in predicted_df.columns:
            if col + '_gt' in merged_df.columns:
                merged_df[col + '_pred'] = predicted_df[col]
            else:
                merged_df[col + '_pred'] = predicted_df[col]
    
    return merged_df

def calculate_evaluation_metrics(merged_df):
    """
    Calculate all evaluation metrics
    """
    results = []
    
    for idx, row in merged_df.iterrows():
        # Extract coordinates
        try:
            gt_lat = float(row.get('latitude_gt', row.get('lat_gt', np.nan)))
            gt_lon = float(row.get('longitude_gt', row.get('lon_gt', row.get('longitude_gt', np.nan))))
            pred_lat = float(row.get('latitude_pred', row.get('lat_pred', np.nan)))
            pred_lon = float(row.get('longitude_pred', row.get('lon_pred', row.get('longitude_pred', np.nan))))
        except (ValueError, TypeError):
            print(f"Warning: Could not parse coordinates for row {idx}")
            continue
        
        # Calculate Haversine distance
        if not any(pd.isna([gt_lat, gt_lon, pred_lat, pred_lon])):
            distance_km = haversine_distance(gt_lat, gt_lon, pred_lat, pred_lon)
        else:
            distance_km = np.nan
        
        
        # Store results
        result_row = {
            'image_index': idx,
            'haversine_distance_km': distance_km,
            'geoscore': geoscore(gt_lat, gt_lon, pred_lat, pred_lon),
            'gt_latitude': gt_lat,
            'gt_longitude': gt_lon,
            'pred_latitude': pred_lat,
            'pred_longitude': pred_lon,
        }
        
        # Add image identifier if available
        possible_id_columns = ['filename', 'image_id']
        for col in possible_id_columns:
            if f'{col}_gt' in row:
                result_row['image_id'] = row[f'{col}_gt']
                break
            elif col in row:
                result_row['image_id'] = row[col]
                break
        
        results.append(result_row)
    
    return pd.DataFrame(results)

def calculate_overall_metrics(results_df):
    """
    Calculate overall evaluation metrics including RMSE
    """
    # Remove rows with NaN distances for RMSE calculation
    valid_distances = results_df['haversine_distance_km'].dropna()
    
    if len(valid_distances) == 0:
        print("Warning: No valid distance calculations found!")
        return {}
    
    overall_metrics = {
        'total_images': len(results_df),
        'images_with_valid_coords': len(valid_distances),
        'mean_haversine_distance_km': np.mean(valid_distances),
        'median_haversine_distance_km': np.median(valid_distances),
        'std_haversine_distance_km': np.std(valid_distances),
        'min_haversine_distance_km': np.min(valid_distances),
        'max_haversine_distance_km': np.max(valid_distances),
        'rmse_km': np.sqrt(np.mean(valid_distances**2)),  # RMSE
        'mean_geoscore': np.mean(results_df['geoscore']),
        'max_geoscore': np.max(results_df['geoscore']),
    }
    
    # Calculate accuracy at various thresholds
    thresholds = [1, 10, 25, 100, 500, 1000]
    for threshold in thresholds:
        overall_metrics[f'acc_{threshold}km'] = np.mean(valid_distances <= threshold)
    
    return overall_metrics

def main(ground_truth_file, predicted_file, output_file):
    """
    Main function to run the evaluation analysis
    """
    print("Loading data...")
    
    # Load CSV files
    ground_truth_df = pd.read_csv(ground_truth_file, encoding='latin-1')
    predicted_df = pd.read_csv(predicted_file, encoding='latin-1') 
    
    print(f"Ground truth data: {len(ground_truth_df)} rows, {len(ground_truth_df.columns)} columns")
    print(f"Predicted data: {len(predicted_df)} rows, {len(predicted_df.columns)} columns")
    print(f"Ground truth columns: {list(ground_truth_df.columns)}")
    print(f"Predicted columns: {list(predicted_df.columns)}")
    
    # Clean and match data
    print("\nMatching images between datasets...")
    merged_df = clean_and_match_data(ground_truth_df, predicted_df)
    
    # Calculate evaluation metrics
    print("Calculating evaluation metrics...")
    results_df = calculate_evaluation_metrics(merged_df)
    
    # Calculate overall metrics
    print("Calculating overall metrics...")
    overall_metrics = calculate_overall_metrics(results_df)
    
    # Save detailed results
    print(f"Saving results to {output_file}...")
    results_df.to_csv(output_file, index=False)
    results_df['image_id'] = results_df['image_id'].astype(str)
    
    # Save overall metrics to a separate file
    overall_file = output_file.replace('.csv', '_overall_metrics.csv')
    overall_df = pd.DataFrame([overall_metrics])
    overall_df.to_csv(overall_file, index=False)
    
    # Print summary
    print("\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    print(f"Total images evaluated: {overall_metrics.get('total_images', 'N/A')}")
    print(f"Images with valid coordinates: {overall_metrics.get('images_with_valid_coords', 'N/A')}")
    print(f"\nDistance Metrics:")
    print(f"  RMSE: {overall_metrics.get('rmse_km', 'N/A'):.2f} km")
    print(f"  Mean Distance: {overall_metrics.get('mean_haversine_distance_km', 'N/A'):.2f} km")
    print(f"  Median Distance: {overall_metrics.get('median_haversine_distance_km', 'N/A'):.2f} km")
    print(f"  Mean GeoScore: {overall_metrics.get('mean_geoscore', 'N/A'):.2f} ")
    print(f"  Std Distance: {overall_metrics.get('std_haversine_distance_km', 'N/A'):.2f} km")
    
    
    print(f"\nAccuracy at Thresholds:")
    for threshold in [1, 10, 25, 100, 500, 1000]:
        key = f'acc_{threshold}km'
        if key in overall_metrics:
            print(f"  Within {threshold} km: {overall_metrics[key]:.2%}")
    
    print(f"\nDetailed results saved to: {output_file}")
    print(f"Overall metrics saved to: {overall_file}")


if __name__ == "__main__":

    

    ground_truth_file = r"  "
    predicted_file = r"  "
    
    output_file = "eval.csv"
    
    main(ground_truth_file, predicted_file, output_file)