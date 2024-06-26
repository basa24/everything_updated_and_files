# -*- coding: utf-8 -*-
"""yolov8_inference_evaluation_each_class

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/14SvhJVbPkvp_q_fSYpfvDLfQti-pd-RF
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
from google.colab.patches import cv2_imshow
resolution = 640

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
import json

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



for key in categoryid_to_name.values():
  word_to_check = key

# Use list comprehension to check if the word is in the array
  is_present = any(word_to_check == word for word in coco_names)

  if is_present:
    continue
  else:
    print(f"{word_to_check} is not present in the array.")

#Accessing validation images from mydrive
  # Initialize lists to store extracted information


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

  start_time = time.time()

  results = model.predict(image_path, save_conf=True, conf =0.5)

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

# If you want to modify the original DataFrame in-place, you can use:
# df.sort_values(by='image id', ascending=True, inplace=True)


#print("\n", elapsed_time_approx,"seconds") figure this out later
# Reset index to get the index as a column
df_sorted.reset_index(inplace=True, drop=True)

# Now add a new column 'bbox_id' which is just a sequence of numbers equal to the row number
df_sorted['bbox_id'] = df_sorted.index
df_sorted['bbox_id'] = df_sorted['bbox_id'].astype(int)


# Now your df_sorted contains a 'bbox_id' column which uniquely identifies each bounding box
df_sorted

#getting data frame from anotated images
import pandas as pd
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

df_annot

# Assuming df_sorted and df_annot are your DataFrames

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
matches = []

# Iterate over each prediction
for index, row in df_sorted.iterrows():
    image_id = row['image id']
    class_name = row['name']
    pred_box = row['bounding box']

    # Filter ground truths for the same image ID and class name
    gt_filtered = df_annot[(df_annot['image id'] == image_id) & (df_annot['name'] == class_name)]

    best_iou = 0
    best_gt = None

    # Compare with each ground truth bounding box
    for _, gt_row in gt_filtered.iterrows():
        gt_box = gt_row['bounding box']
        iou = calculate_iou(pred_box, gt_box)

        if iou > best_iou:
            best_iou = iou
            best_gt = gt_box

    # If a match was found, append it to the matches list
    if best_iou > 0:  # You can set a threshold if needed
        matches.append({
            'image id': image_id,
            'class name': class_name,
            'pred box': pred_box,
            'gt box': best_gt,
            'iou': best_iou
        })

# Convert matches to DataFrame for easier analysis
df_matches = pd.DataFrame(matches)

df_matches

# Prepare a list to hold match results, now including confidence, bbox_id, and gt_id
matches = []

# Iterate over each prediction in df_sorted
for index, row in df_sorted.iterrows():
    image_id = row['image id']
    class_name = row['name']
    pred_box = row['bounding box']
    confidence = row['confidence']  # Extract confidence
    bbox_id = row['bbox_id']  # Extract bbox_id

    # Filter ground truths for the same image ID and class name
    gt_filtered = df_annot[(df_annot['image id'] == image_id) & (df_annot['name'] == class_name)]

    best_iou = 0
    best_gt = None
    best_gt_id = None  # Initialize variable to store the best matching gt_id
    best_confidence = confidence  # Keep the confidence of the current prediction
    best_bbox_id = bbox_id  # Keep the bbox_id of the current prediction

    # Compare with each ground truth bounding box
    for _, gt_row in gt_filtered.iterrows():
        gt_box = gt_row['bounding box']
        gt_id = gt_row['gt_id']  # Extract the gt_id for the current ground truth
        iou = calculate_iou(pred_box, gt_box)

        if iou > best_iou:
            best_iou = iou
            best_gt = gt_box
            best_gt_id = gt_id  # Update the best_gt_id when a new best match is found

    # If a match was found, append it to the matches list, including confidence, bbox_id, and now gt_id
    if best_iou > 0.5:  # Using 0.5 as the IoU threshold for a match to be considered true positive
        matches.append({
            'image id': image_id,
            'class name': class_name,
            'pred box': pred_box,
            'gt box': best_gt,
            'iou': best_iou,
            'confidence': best_confidence,  # Include confidence
            'bbox_id': best_bbox_id,  # Include bbox_id
            'gt_id': best_gt_id  # Include the gt_id of the matched ground truth
        })

# Convert matches to DataFrame for easier analysis
df_matches_with_confidence = pd.DataFrame(matches)

# Now df_matches includes 'iou', 'confidence', 'bbox_id', and 'gt_id' for each match

df_matches_with_confidence

# Check for one-to-one mapping of bbox_id to gt_id
# A one-to-one mapping means each bbox_id and gt_id appears exactly once

# Checking for any predicted bbox_id being mapped to more than one gt_id
pred_to_gt_mapping_issues = df_matches_with_confidence.duplicated(subset=['bbox_id'], keep=False)
if pred_to_gt_mapping_issues.any():
    print("Issues found with predicted bounding boxes being mapped to multiple ground truth boxes:")
    print(df_matches_with_confidence[pred_to_gt_mapping_issues].sort_values(by='bbox_id'))
else:
    print("All predicted bounding boxes are uniquely mapped to ground truth boxes.")

# Checking for any ground truth gt_id being mapped to more than one bbox_id
gt_to_pred_mapping_issues = df_matches_with_confidence.duplicated(subset=['gt_id'], keep=False)
if gt_to_pred_mapping_issues.any():
    print("\nIssues found with ground truth boxes being mapped to multiple predicted bounding boxes:")
    print(df_matches_with_confidence[gt_to_pred_mapping_issues].sort_values(by='gt_id'))
else:
    print("\nAll ground truth boxes are uniquely mapped to predicted bounding boxes.")

# Sort df_sorted by 'confidence' to prioritize high confidence predictions
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

# Ensure df_matches_with_confidence now represents a strict one-to-one matching



# Check for one-to-one mapping of bbox_id to gt_id
# A one-to-one mapping means each bbox_id and gt_id appears exactly once

# Checking for any predicted bbox_id being mapped to more than one gt_id
pred_to_gt_mapping_issues = df_matches_with_confidence.duplicated(subset=['bbox_id'], keep=False)
if pred_to_gt_mapping_issues.any():
    print("Issues found with predicted bounding boxes being mapped to multiple ground truth boxes:")
    print(df_matches_with_confidence[pred_to_gt_mapping_issues].sort_values(by='bbox_id'))
else:
    print("All predicted bounding boxes are uniquely mapped to ground truth boxes.")

# Checking for any ground truth gt_id being mapped to more than one bbox_id
gt_to_pred_mapping_issues = df_matches_with_confidence.duplicated(subset=['gt_id'], keep=False)
if gt_to_pred_mapping_issues.any():
    print("\nIssues found with ground truth boxes being mapped to multiple predicted bounding boxes:")
    print(df_matches_with_confidence[gt_to_pred_mapping_issues].sort_values(by='gt_id'))
else:
    print("\nAll ground truth boxes are uniquely mapped to predicted bounding boxes.")

df_matches_with_confidence

from scipy.optimize import linear_sum_assignment
import numpy as np

# Function to calculate IoU, already defined in your workflow
def calculate_iou(boxA, boxB):
    # Your IoU calculation code here
    pass

# Construct the cost matrix
num_preds = len(df_sorted)
num_gts = len(df_annot)
cost_matrix = np.zeros((num_preds, num_gts))

for i, pred_row in df_sorted.iterrows():
    for j, gt_row in df_annot.iterrows():
        # Calculate IoU and negate it because we want to maximize IoU (minimize cost)
        cost_matrix[i, j] = -calculate_iou(pred_row['bounding box'], gt_row['bounding box'])

# Apply the Hungarian algorithm
row_inds, col_inds = linear_sum_assignment(cost_matrix)

# Filter matches by IoU threshold and construct the matches DataFrame
matches = []
for row, col in zip(row_inds, col_inds):
    iou = -cost_matrix[row, col]  # Negate again to get the original IoU value
    if iou >= 0.5:  # Apply IoU threshold
        match = {
            'image id': df_sorted.iloc[row]['image id'],
            'class name': df_sorted.iloc[row]['name'],
            'pred box': df_sorted.iloc[row]['bounding box'],
            'gt box': df_annot.iloc[col]['bounding box'],
            'iou': iou,
            'confidence': df_sorted.iloc[row]['confidence'],
            'bbox_id': df_sorted.iloc[row]['bbox_id'],
            'gt_id': df_annot.iloc[col]['gt_id']  # Assuming df_annot has 'gt_id' column
        }
        matches.append(match)

# Convert matches to DataFrame
df_matches_optimal = pd.DataFrame(matches)

# Now df_matches_optimal represents the optimal one-to-one mapping

df_tp = df_matches_with_confidence[df_matches['iou'] >= 0.5]

unique_classes = df_annot['name'].unique()
class_metrics = {}

for class_name in unique_classes:
    # TP for current class
    tp = len(df_tp[df_tp['class name'] == class_name])

    # FP calculations
    total_preds_for_class = len(df_sorted[df_sorted['name'] == class_name])
    fp = total_preds_for_class - tp

    # FN calculations
    total_gts_for_class = len(df_annot[df_annot['name'] == class_name])
    fn = total_gts_for_class - tp

    # Calculate precision, recall, and F1 score
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Storing the calculated metrics
    class_metrics[class_name] = {'Precision': precision, 'Recall': recall, 'F1 Score': f1_score, 'TP': tp, 'FP': fp, 'FN': fn}

# Convert to DataFrame for easier viewing
df_class_metrics = pd.DataFrame.from_dict(class_metrics, orient='index')
df_class_metrics

from sklearn.metrics import average_precision_score, precision_recall_curve
import numpy as np

# Initialize dictionary to hold class-specific metrics
class_metrics = {}

# Ensure df_matches contains 'iou' column for IoU values between predictions and ground truths
df_matches_filtered = df_matches[df_matches['iou'] >= 0.5]  # Consider as TP those with IoU >= 0.5

# Get unique classes from both predictions and annotations
unique_classes = set(df_sorted['name'].unique()).union(set(df_annot['name'].unique()))

for class_name in unique_classes:
    # Filter detections and ground truths for the current class
    class_preds = df_sorted[df_sorted['name'] == class_name]
    class_gts = df_annot[df_annot['name'] == class_name]

    # Match only those that are considered true positives
    class_matches = df_matches_filtered[df_matches_filtered['class name'] == class_name]

    TP = len(class_matches)
    FP = len(class_preds) - TP
    FN = len(class_gts) - TP  # Ensure FN is not negative


    # Calculate Precision, Recall, F1 Score
    Precision = TP / (TP + FP) if TP + FP > 0 else 0
    Recall = TP / (TP + FN) if TP + FN > 0 else 0
    F1_Score = 2 * (Precision * Recall) / (Precision + Recall) if Precision + Recall > 0 else 0

    # Calculate Average IoU for this class
    ious = class_matches['iou']
    Average_IoU = np.mean(ious) if not ious.empty else 0

    # For AP calculation, refer to your existing methodology or precision_recall_curve as shown
    # For simplicity, this part is omitted here. You can include your AP calculation method.

    # Store metrics
    class_metrics[class_name] = {
        'Precision': Precision,
        'Recall': Recall,
        'F1 Score': F1_Score,
        'Average IoU': Average_IoU,
        'TP': TP,
        'FP': FP,
        'FN': FN,
        # Include 'AP': AP if you calculate it as per your method
    }

# Optionally, convert to DataFrame for easier analysis
import pandas as pd
df_class_metrics = pd.DataFrame.from_dict(class_metrics, orient='index').reset_index()
df_class_metrics.rename(columns={'index': 'Class'}, inplace=True)
df_class_metrics.index.name = 'Row Number'
df_class_metrics.reset_index(inplace=True)
df_class_metrics



import numpy as np
import pandas as pd

# Define the function to calculate AP
def calculate_AP(precision_recall_points):
    precision_recall_points.sort(key=lambda x: x[0])  # Sort by recall
    precision_recall_points.insert(0, (0, 1))  # Add a point at recall = 0
    precision_recall_points.append((1, precision_recall_points[-1][1]))  # Add a point at recall = 1
    ap = 0
    for i in range(1, len(precision_recall_points)):
        recall_diff = precision_recall_points[i][0] - precision_recall_points[i - 1][0]
        precision_avg = (precision_recall_points[i][1] + precision_recall_points[i - 1][1]) / 2
        ap += recall_diff * precision_avg
    return ap

# Initialize a dictionary to store AP for each class
class_AP = {}

# Iterate through each unique class to calculate AP
for class_name in unique_classes:
    # Filter matches and ground truths for the current class
    class_matches = df_matches_filtered[df_matches_filtered['class name'] == class_name]
    class_preds = df_sorted[df_sorted['name'] == class_name]
    class_annots = df_annot[df_annot['name'] == class_name]

    # Calculate TP, FP, and FN
    TP = len(class_matches)
    FP = len(class_preds) - TP
    FN = len(class_annots) - TP

    # Ensure that FN is not negative
    FN = max(FN, 0)

    # Generate precision and recall points for the current class
    precision_recall_points = []
    if TP + FP > 0 and TP + FN > 0:
        precision = TP / (TP + FP)
        recall = TP / (TP + FN)
        precision_recall_points.append((recall, precision))

    # Add a dummy point for AP calculation in case there are no true positives
    if not precision_recall_points:
        precision_recall_points.append((0, 1))

    # Calculate AP for the class
    class_AP[class_name] = calculate_AP(precision_recall_points)

# Optionally, convert the AP dictionary to a DataFrame for easier analysis
df_class_AP = pd.DataFrame(list(class_AP.items()), columns=['Class', 'AP'])
df_class_AP

# Initialize dictionary to hold class-specific metrics
class_metrics = {}

# Iterate through each unique class found in the predictions
for class_name in set(class_names):  # Assuming `obj` contains class names of predictions
    # Filter matches, predictions, and annotations for the current class
    class_matches = df_matches[df_matches['class name'] == class_name]
    class_preds = df_sorted[df_sorted['name'] == class_name]
    class_annots = df_annot[df_annot['name'] == class_name]

    # Calculate True Positives, False Positives, and False Negatives
    TP = len(class_matches)
    FP = len(class_preds) - TP
    FN = len(class_annots) - TP

    # Calculate Precision, Recall, and F1 Score
    Precision = TP / (TP + FP) if TP + FP > 0 else 0
    Recall = TP / (TP + FN) if TP + FN > 0 else 0
    F1_Score = 2 * (Precision * Recall) / (Precision + Recall) if (Precision + Recall) > 0 else 0

    # Store metrics for the current class
    class_metrics[class_name] = {
        'Precision': Precision,
        'Recall': Recall,
        'F1 Score': F1_Score,
        'TP': TP,
        'FP': FP,
        'FN': FN
    }

# Optionally, print or store class-specific metrics for further analysis
count = 0
for class_name, metrics in class_metrics.items():
    print(f"Class: {class_name}, Metrics: {metrics}")
    count = count+1

print (count)

df_class_metrics = pd.DataFrame.from_dict(class_metrics, orient='index')

# Reset the index to add a column with the original index (class names)
# Then reset the index again to make the DataFrame index start from 1, which effectively adds row numbers
df_class_metrics.reset_index(inplace=True)
df_class_metrics.rename(columns={'index': 'Class'}, inplace=True)
df_class_metrics.index = range(1, len(df_class_metrics) + 1)

# Now df_class_metrics includes row numbers and class names
df_class_metrics

unique_class_names = df_annot['name'].unique().tolist()
count = 0
for i in unique_class_names:
  count = count +1

print(count)

ious = df_matches['iou']
average_iou = sum(ious) / len(ious)
average_time=sum(times) / len(times)
TP = sum(iou > 0.5 for iou in ious)
FP = len(df_sorted) - TP
FN = len(df_annot) - TP


precision = TP / (TP + FP)
recall = TP / (TP + FN)
f1_score = 2 * (precision * recall) / (precision + recall)
print(f"Precision: {precision:.2f} \nRecall: {recall:.2f} \nF1 Score: {f1_score:.2f} \nAverage iou: {average_iou:.2f}\nCorrect Predictions(TP): {TP:.2f} \nMispredictions/duplicate detections(FP): {FP:.2f} \nMissed detections(FN): {FN:.2f} \nAverage time: {average_time:.2f}")

resolution=str(resolution)
data = {
    "Model": ["YOLOv8n"],
    "Image resolution": [resolution+" x "+resolution],
    "TP": [TP],
    "FP": [FP],
    "FN": [FN],
    "Precision": [precision],
    "Recall": [recall],
    "F1 Score": [f1_score],
    "Average IoU": [average_iou],
    "Average Time": [average_time]
    }

# Create the DataFrame
df_results = pd.DataFrame(data)
df_results

import numpy as np

# Assuming df_sorted, df_annot, and df_matches are already defined as per your description

# Filter df_matches for IoU >= 0.5
df_matches_filtered = df_matches[df_matches['iou'] >= 0.5]

# Define a function to calculate Average Precision (AP) for a class
def calculate_AP(precision_recall_points):
    # Sort by recall
    precision_recall_points.sort(key=lambda x: x[0])
    # Add a point for recall = 0 with precision = 1
    precision_recall_points.insert(0, (0, 1))
    # Add a point for recall = 1 with the last precision
    precision_recall_points.append((1, precision_recall_points[-1][1]))

    # Calculate the area under the curve using the trapezoidal rule
    ap = 0
    for i in range(1, len(precision_recall_points)):
        recall_diff = precision_recall_points[i][0] - precision_recall_points[i-1][0]
        precision_avg = (precision_recall_points[i][1] + precision_recall_points[i-1][1]) / 2
        ap += recall_diff * precision_avg
    return ap

# Get unique classes
unique_classes = df_sorted['name'].unique()
APs = {}

for class_name in unique_classes:
    class_preds = df_sorted[df_sorted['name'] == class_name]
    class_gts = df_annot[df_annot['name'] == class_name].shape[0]

    TP = FP = 0
    precision_recall_points = []

    for _, pred in class_preds.iterrows():
        # Convert 'pred box' to a tuple for comparison
        pred_box_tuple = tuple(pred['bounding box'])

        # Adjusted .apply() to compare 'pred box' tuples
        match = df_matches_filtered.apply(lambda x: x['class name'] == class_name and tuple(x['pred box']) == pred_box_tuple, axis=1)

        if match.any():
            TP += 1
        else:
            FP += 1

        precision = TP / (TP + FP) if TP + FP > 0 else 0
        recall = TP / class_gts if class_gts > 0 else 0
        precision_recall_points.append((recall, precision))

    # Calculate AP for this class, using your calculate_AP function
    APs[class_name] = calculate_AP(precision_recall_points)

# Calculate mAP by averaging APs
mAP = np.mean(list(APs.values()))
print(f"mAP (IoU >= 0.5): {mAP:.4f}")

"""- Accuracy is used when the True Positives and True negatives are more important while F1-score is used when the False Negatives and False Positives are crucial
- Accuracy can be used when the class distribution is similar while F1-score is a better metric when there are imbalanced classes as in the above case.
- In most real-life classification problems, imbalanced class distribution exists and thus F1-score is a better metric to evaluate our model on.

- Scope: F1 score is typically used for binary or multi-class classification tasks focusing on the balance between precision and recall at a specific decision threshold. mAP is used in scenarios like object detection where the accuracy of both the classification and localization (bounding box prediction) matters across multiple classes and thresholds.
- Complexity: The calculation and interpretation of the F1 score are straightforward, focusing on a single threshold. mAP involves integrating over a curve and averaging across classes and/or IoU thresholds, making it a more comprehensive but complex metric.
- Application: F1 is ideal for tasks where false positives and false negatives need to be equally penalized. mAP is suited for evaluating models where the accuracy of detecting and precisely localizing multiple objects is crucial.

https://medium.com/analytics-vidhya/accuracy-vs-f1-score-6258237beca2#:~:text=Accuracy%20is%20used%20when%20the,as%20in%20the%20above%20case.
"""

df_results["mAP"]=[mAP]
df_results

file_path_csv = '/content/drive/MyDrive/files and others for ee/model_evaluation_empty.csv'  # Replace with your actual file path

# Append the DataFrame to the existing CSV without including the header
df_results.to_csv(file_path_csv, mode='a', index=False, header=False)

print(resolution)