import os
import cv2
import math
import sys, getopt
import piexif
import random
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
from utils import *
from glob import glob
from functools import reduce
from collections import defaultdict
from focal_loss import BinaryFocalLoss
from TrackNet import ResNet_Track
from tensorflow import keras
from parser import parser
from tensorflow.keras import backend as K

args = parser.parse_args()
tol = args.tol
save_weights = args.save_weights
HEIGHT = args.HEIGHT
WIDTH = args.WIDTH
BATCH_SIZE = args.batch_size
FRAME_STACK = args.frame_stack
BACK_FRAME_STACK = args.back_frame_stack
pre_trained = args.pre_trained
print("lerning rate: "+str(args.lr))
optimizer = keras.optimizers.Adadelta(learning_rate=args.lr)
if not pre_trained:
	model=ResNet_Track(input_shape=(FRAME_STACK, HEIGHT, WIDTH))
	model.compile(loss=BinaryFocalLoss(gamma=2), optimizer=optimizer, metrics=[keras.metrics.BinaryAccuracy()]) 
else:
	model=ResNet_Track(input_shape=(FRAME_STACK, HEIGHT, WIDTH))
	model.load_weights(args.load_weights)
	model.compile(loss=BinaryFocalLoss(gamma=2), optimizer=optimizer, metrics=[keras.metrics.BinaryAccuracy()])

print('Beginning training......')
match_path = args.match_folder
match_list = [os.sep.join([os.getcwd(), match_path, match]) for match in os.listdir(match_path)]

wait = 0
best_loss = float('inf')
losses = []
for i in range(args.epochs):
	x_train, x_test, y_train, y_test = split_train_test2(match_list, FRAME_STACK, BACK_FRAME_STACK, ratio=args.split_ratio, shuffle=True)
	train_steps = min(check_steps(x_train+x_test, BATCH_SIZE, FRAME_STACK), 1500)
	print("==========Epoch {}, Train steps: {}, Learning rate: {:.4f}==========".format(i, train_steps, float(K.get_value(model.optimizer.lr))))
	history = model.fit(data_generator2(BATCH_SIZE, x_train, y_train, FRAME_STACK, BACK_FRAME_STACK), 
						steps_per_epoch=train_steps,
						epochs=1,
						verbose=1)
	loss = sum(history.history['loss'])
	losses.append(loss)
	
	if not i%5:  # validation
		TP = TN = FP1 = FP2 = FN = 0
		test_iter = iter(data_generator2(BATCH_SIZE, x_test, y_test, FRAME_STACK, BACK_FRAME_STACK))
		test_steps = min(check_steps(x_test, BATCH_SIZE, FRAME_STACK),400)
		print("==========Epoch {} start validation========== ".format(i)+str(test_steps))
		for j in range(test_steps):
			x_batch, y_batch = next(test_iter)
			y_pred = model.predict(x_batch, batch_size=BATCH_SIZE)
			y_pred = y_pred > 0.5
			y_pred = y_pred.astype('float32')

			tp, tn, fp1, fp2, fn = confusion(y_pred, y_batch[:, 0,...], tol)
			TP += tp
			TN += tn
			FP1 += fp1
			FP2 += fp2
			FN += fn

		accuracy, precision, recall = compute_acc((TP, TN, FP1, FP2, FN))
		avg_acc = (accuracy + precision + recall)/3
		print("Epoch {} accuracy: {:.3f}".format(i, accuracy))
		print("Epoch {} precision: {:.3f}".format(i, precision))
		print("Epoch {} recall: {:.3f}".format(i, recall))
		print("Epoch {} average = (accuracy + precision + recall)/3: {:.3f}".format(i, avg_acc))

	# learnging rate callback and saving model
	if loss < best_loss - args.min_delta:
		wait = 0
		best_loss = loss
		model.save_weights(save_weights)
	else:
		wait += 1
		if wait >= args.patience:
			old_lr = float(K.get_value(model.optimizer.lr))
			if old_lr > args.min_lr:
				new_lr = old_lr * args.r_factor
				new_lr = max(new_lr, args.min_lr)
				K.set_value(model.optimizer.lr, new_lr)
				wait = 0
				print("Reduce model learning rate to {}".format(new_lr))
			
plt.plot(losses)
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Test'], loc='upper left')
plt.savefig("Loss_epoch.jpg")	

print('Saving weights......')
model.save_weights(save_weights+'_final')
print('Done......')
