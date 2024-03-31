# everything_updated_and_files

- I had to make some modifications to the code as the matching algorithm didn't have one to  one matching. That is why there are two notebooks titled loop with correct matching. I also conducted the confidence threshold experiments in those same notebooks, but that outer loop can simply be removed if needed. 
- I have also inlcuded the colabs which I used to calculate average precision since average precsion requires a threshold of 0 and for the other metrics I just used a threshold of 0.5. This gave me average precsion per class. I also used the same colab to calculate mAP for varying image resolutions. 
- I also included the colabs which I used to calculate the metrics per class (precion, recall, f1score, average iou). I did this at a resolution of 640, the max.
- Finally there is a colab which I used to just make a csv which shows whether one metric is greater or less than the other creating a table showing which model outperforms the other in a given metric. 
- The separation of these different tasks into different colabs makes it easier to track my process. 
- There is also a zip file containing all the files which I used during the inference process and to save the data to.
- There is also an excel of all the final data.
