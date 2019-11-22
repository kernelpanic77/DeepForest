"""
Prediction module. This module consists of predict utility function for the deepforest class
"""
import numpy as np
import copy
import glob
import keras
import cv2
import pandas as pd

#Retinanet-viz
from keras_retinanet.utils import image as keras_retinanet_image
from keras_retinanet.utils.visualization import draw_detections

#TODO check how this works with multiple classes
def label_to_name(image_classes, index):
    """ Map label to name.
    """
    label = image_classes[index]
    return label

def predict_image(model, image_path=None, raw_image = None, score_threshold = 0.05, max_detections= 200, return_plot=True, classes = ["Tree"]):
    """
    Predict invidiual tree crown bounding boxes for a single image
    
    Args:
        model (object): A keras-retinanet model to predict bounding boxes, either load a model from weights, use the latest release, or train a new model from scratch.  
        image_path (str): Path to image file on disk
        raw_image (str): Numpy image array in BGR channel order following openCV convention
        score_threshold (float): Minimum probability score to be included in final boxes, ranging from 0 to 1.
        max_detections (int): Maximum number of bounding box predictions per tile
        return_plot (bool):  If true, return a image object, else return bounding boxes as a numpy array
    
    Returns:
        raw_image (array): If return_plot is TRUE, the image with the overlaid boxes is returned
        image_detections: If return_plot is FALSE, a np.array of image_boxes, image_scores, image_labels
    """
    #predict
    if image_path:
        raw_image = cv2.imread(image_path)       
    image        = keras_retinanet_image.preprocess_image(raw_image)
    image, scale = keras_retinanet_image.resize_image(image)

    if keras.backend.image_data_format() == 'channels_first':
        image = image.transpose((2, 0, 1))

    # run network
    boxes, scores, labels = model.predict_on_batch(np.expand_dims(image, axis=0))[:3]

    # correct boxes for image scale
    boxes /= scale

    # select indices which have a score above the threshold
    indices = np.where(scores[0, :] > score_threshold)[0]

    # select those scores
    scores = scores[0][indices]

    # find the order with which to sort the scores
    scores_sort = np.argsort(-scores)[:max_detections]

    # select detections
    image_boxes      = boxes[0, indices[scores_sort], :]
    image_scores     = scores[scores_sort]
    image_labels     = labels[0, indices[scores_sort]]
    image_detections = np.concatenate([image_boxes, np.expand_dims(image_scores, axis=1), np.expand_dims(image_labels, axis=1)], axis=1)

    df = pd.DataFrame(image_detections, columns = ["xmin","ymin","xmax","ymax","score","label"])
    #Change numberic class into string label
    df.label = df.label.apply(lambda x: classes[x])
    
    if return_plot:
        draw_detections(raw_image, image_boxes, image_scores, image_labels, label_to_name=label_to_name, score_threshold=score_threshold)
        return raw_image                
    else:
        return df
