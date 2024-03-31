# -*- coding: utf-8 -*-
"""ap yolo.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1z8q1sMRJh7bf5mVHzEG8pucgL8Zwv-cl
"""

# -*- coding: utf-8 -*-
"""yolov8_inference_evaluation

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wzy9OBgmEoKBuHSKj8fHfS3VOPZ_e81S
"""

!pip install torch torchvision
!pip install ultralytics -q
!pip install pyyaml -q
import torch
import pandas as pd
import time
from PIL import Image
import cv2
import os
import json
from ultralytics import YOLO
import yaml
import numpy as np

from google.colab.patches import cv2_imshow


file_name = "../usr/local/lib/python3.10/dist-packages/ultralytics/cfg/datasets/coco8.yaml"
with open (file_name, "r") as stream:
    names = yaml.safe_load(stream)["names"]

coco_names= list(names.values())

# Load the pre-trained Faster R-CNN model
model = YOLO("yolov8n.pt")


if torch.cuda.is_available():
    print("GPU is available!")
else:
    print("GPU is not available.")
model.eval()

# Replace 'your_file.json' with the path to your actual JSON file
file_path = '/content/drive/MyDrive/files and others for ee/imagesvalidationids.json'

with open(file_path, 'r') as file:
    data = json.load(file)
file_name_to_id = {item['file_name']: item['id'] for item in data}

print(file_name_to_id)

file_path = '/content/drive/MyDrive/files and others for ee/categoriesvalidation.json'
with open(file_path, 'r') as file:
    data = json.load(file)
categoryid_to_name = {item['id']: item['name'] for item in data}

print(categoryid_to_name)

resolutions = [640, 540, 440, 340, 240]
for r in resolutions:
  resolution=r
  desired_resolution=(resolution, resolution)
  times=[]
  bboxes = []
  scores = []
  class_names = []
  image_names = []
  image_id_perdetection=[]
  from os import listdir
  directory="/content/drive/MyDrive/valid"
  for image in os.listdir(directory):
    image_path = "/content/drive/MyDrive/valid/"+image
        #print(image_path) works, every path accessed
    with Image.open(image_path) as img:
        resized_img = img.resize(desired_resolution)

    start_time = time.time()

    results = model.predict(resized_img, save_conf=True, conf = 0)

    end_time = time.time()  # Time after model prediction

    elapsed_time = end_time - start_time
    times.append(elapsed_time)

    # Apply confidence threshold
    json_output = results[0].tojson()

  # Parse the JSON output
    detections = json.loads(json_output)



    # Extract information for each detection
    for detection in detections:
        # Extract and store bounding box coordinates
        box = detection["box"]
        bbox = [box["x1"], box["y1"], box["x2"], box["y2"]]
        bboxes.append(bbox)

        # Extract and store confidence score
        confidence = detection["confidence"]
        scores.append(confidence)

        # Extract and store class name
        class_name = detection["name"]
        class_names.append(class_name)

        image_id = file_name_to_id[image]
        image_id_perdetection.append(image_id)

  dict = {'image id': image_id_perdetection, 'name': class_names, 'bounding box': bboxes, 'confidence': scores }

  df = pd.DataFrame(dict)

  pd.set_option('display.max_rows', None)  # This will allow all rows to be displayed
  pd.set_option('display.max_columns', None)  # This will allow all columns to be displayed

  df_sorted = df.sort_values(by='image id', ascending=True)


  #print("\n", elapsed_time_approx,"seconds") figure this out later
  # Reset index to get the index as a column
  df_sorted.reset_index(inplace=True, drop=True)

  # Now add a new column 'bbox_id' which is just a sequence of numbers equal to the row number
  df_sorted['bbox_id'] = df_sorted.index
  df_sorted['bbox_id'] = df_sorted['bbox_id'].astype(int)


  #getting data frame from anotated images
  file_path = '/content/drive/MyDrive/files and others for ee/modified_data_with_boundingboxes_try2.json'
  with open(file_path, 'r') as file:
      data = json.load(file)

  extracted_data = []
  for item in data:
      extracted_data.append({
          'image id': item['image_id'],
          'name': item['category_id'],
          'bounding box': item['bbox']
      })

  df_annot = pd.DataFrame(extracted_data)
  df_annot.reset_index(inplace=True, drop=True)

  # Now add a new column 'bbox_id' which is just a sequence of numbers equal to the row number
  df_annot['gt_id'] = df_annot.index
  df_annot['gt_id'] = df_annot['gt_id'].astype(int)


  def calculate_iou(boxA, boxB):
      # Unpack the bounding box coordinates and calculate their areas
      xA, yA, wA, hA = boxA
      xB, yB, wB, hB = boxB
      areaA = wA * hA
      areaB = wB * hB

      # Convert to corner coordinates
      xAmin, yAmin, xAmax, yAmax = xA, yA, xA + wA, yA + hA
      xBmin, yBmin, xBmax, yBmax = xB, yB, xB + wB, yB + hB

      # Calculate intersection coordinates
      xImin = max(xAmin, xBmin)
      yImin = max(yAmin, yBmin)
      xImax = min(xAmax, xBmax)
      yImax = min(yAmax, yBmax)

      # Calculate intersection area
      interArea = max(xImax - xImin, 0) * max(yImax - yImin, 0)

      # Calculate IoU
      iou = interArea / float(areaA + areaB - interArea)
      return iou

  # Prepare a list to hold match results
  # Assuming df_sorted has 'bbox_id' and 'confidence' as shown previously

  df_sorted = df_sorted.sort_values(by='confidence', ascending=False)

  # Initialize trackers for matched ground truth and predictions
  matched_gt = set()
  matched_preds = set()

  matches = []

  for _, pred_row in df_sorted.iterrows():
      pred_box = pred_row['bounding box']
      bbox_id = pred_row['bbox_id']
      image_id = pred_row['image id']
      class_name = pred_row['name']
      confidence = pred_row['confidence']

      # Skip if this prediction has already been matched
      if bbox_id in matched_preds:
          continue

      # Filter ground truths for the same image ID and class name that haven't been matched
      gt_filtered = df_annot[(df_annot['image id'] == image_id) &
                            (df_annot['name'] == class_name) &
                            (~df_annot['gt_id'].isin(matched_gt))]

      best_iou = 0
      best_match = None

      for _, gt_row in gt_filtered.iterrows():
          gt_box = gt_row['bounding box']
          gt_id = gt_row['gt_id']
          iou = calculate_iou(pred_box, gt_box)

          if iou > best_iou:
              best_iou = iou
              best_match = (gt_row['gt_id'], gt_box)

      # If a suitable match is found (IoU > 0.5), record the match
      if best_match and best_iou > 0.5:
          matched_gt.add(best_match[0])  # Mark this gt_id as matched
          matched_preds.add(bbox_id)  # Mark this bbox_id as matched

          matches.append({
              'image id': image_id,
              'class name': class_name,
              'pred box': pred_box,
              'gt box': best_match[1],
              'iou': best_iou,
              'confidence': confidence,
              'bbox_id': bbox_id,
              'gt_id': best_match[0]
          })

  # Convert matches to DataFrame for easier analysis
  df_matches_with_confidence = pd.DataFrame(matches)

  # Create a set of bbox_ids that are present in df_matches_with_confidence for quick lookup
  matched_bbox_ids = set(df_matches_with_confidence['bbox_id'])

  # Use the .apply() method to iterate over each row in df_sorted
  # and check if its bbox_id is in the set of matched_bbox_ids
  df_sorted['label'] = df_sorted['bbox_id'].apply(lambda x: 1 if x in matched_bbox_ids else 0)
  from sklearn.metrics import average_precision_score

  # Assuming df_sorted already exists and includes the columns: 'name', 'bbox_id', 'confidence', 'label'

  # Sort df_sorted by 'confidence' in descending order
  df_sorted = df_sorted.sort_values(by='confidence', ascending=False)

  # Get unique classes from the 'name' column
  unique_classes = df_sorted['name'].unique()

  # Initialize a list to hold AP scores for each class
  ap_scores = []

  # Iterate over each unique class to calculate AP
  for class_name in unique_classes:
      # Filter df_sorted for the current class
      class_df = df_sorted[df_sorted['name'] == class_name]

      # Construct y_true and y_scores for the current class
      y_true = class_df['label'].tolist()  # Labels indicating TP (1) or FP (0)
      y_scores = class_df['confidence'].tolist()  # Confidence scores of the predictions

      # Calculate AP using sklearn
      ap = average_precision_score(y_true, y_scores)

      # Append the class name and its AP to the list
      ap_scores.append({'class_name': class_name, 'AP': ap})

  # Convert the AP scores list to a DataFrame
  df_ap_scores = pd.DataFrame(ap_scores)
  df_ap_scores


  mAP = df_ap_scores['AP'].mean()
  str_resolution=str(resolution)
  data = {
    "Model": ["YOLO"],
    "Image resolution": [str_resolution+" x "+str_resolution],
    "mAP": [mAP]
  }
  # Assuming df_sorted, df_annot, and df_matches are already defined as per your description
  df_map = pd.DataFrame(data)
  file_path_csv = '/content/drive/MyDrive/files and others for ee/Yolo_evaluation_2nattempt - Sheet1.csv'  # Replace with your actual file path

      # Append the DataFrame to the existing CSV without including the header
  df_map.to_csv(file_path_csv, mode='a', index=False, header=True)





mAP = df_ap_scores['AP'].mean()

print(f"Mean Average Precision (mAP): {mAP}")