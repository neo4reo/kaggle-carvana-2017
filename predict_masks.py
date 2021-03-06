import os
from time import clock

import numpy as np
from keras.applications.imagenet_utils import preprocess_input
from keras.preprocessing.image import array_to_img, img_to_array, load_img, flip_axis

from models import make_model
from params import args

os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu

prediction_dir = args.pred_mask_dir


def do_tta(x, tta_type):
    if tta_type == 'hflip':
        # batch, img_col = 2
        return flip_axis(x, 2)
    else:
        return x


def undo_tta(pred, tta_type):
    if tta_type == 'hflip':
        # batch, img_col = 2
        return flip_axis(pred, 2)
    else:
        return pred


def predict():
    output_dir = args.pred_mask_dir
    model = make_model((None, None, 3))
    model.load_weights(args.weights)
    batch_size = args.pred_batch_size
    nbr_test_samples = 100064

    filenames = [os.path.join(args.test_data_dir, f) for f in sorted(os.listdir(args.test_data_dir))]

    start_time = clock()
    for i in range(int(nbr_test_samples / batch_size) + 1):
        x = []
        for j in range(batch_size):
            if i * batch_size + j < len(filenames):
                img = load_img(filenames[i * batch_size + j], target_size=(args.img_height, args.img_width))
                x.append(img_to_array(img))
        x = np.array(x)
        x = preprocess_input(x, args.preprocessing_function)
        x = do_tta(x, args.pred_tta)
        batch_x = np.zeros((x.shape[0], 1280, 1920, 3))
        batch_x[:, :, 1:-1, :] = x
        preds = model.predict_on_batch(batch_x)
        preds = undo_tta(preds, args.pred_tta)
        for j in range(batch_size):
            filename = filenames[i * batch_size + j]
            prediction = preds[j][:, 1:-1, :]
            array_to_img(prediction * 255).save(os.path.join(output_dir, filename.split('/')[-1][:-4] + ".png"))
        time_spent = clock() - start_time
        print("predicted batch ", str(i))
        print("Time spent: {:.2f}  seconds".format(time_spent))
        print("Speed: {:.2f}  ms per image".format(time_spent / (batch_size * (i + 1)) * 1000))
        print("Elapsed: {:.2f} hours  ".format(time_spent / (batch_size * (i + 1)) / 3600 * (nbr_test_samples - (batch_size * (i + 1)))))

if __name__ == '__main__':
    predict()
