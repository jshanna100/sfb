import numpy as np
import mne
import pickle
from os.path import isdir

from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report

from sklearn.ensemble import RandomForestClassifier

def dict_to_array(in_dict, factors):
    X = []
    for factor in factors:
        if factor[0] == "freqs":
            for band in factor[2]:
                X.append(np.squeeze(in_dict["freqs"][factor[1]][band]))
        else:
            X.append(in_dict["amps"][factor[1]])
    X = np.array(X).T
    return X

if isdir("/home/jev"):
    root_dir = "/home/jev/hdd/sfb/"
elif isdir("/home/jeff"):
    root_dir = "/home/jeff/hdd/jeff/sfb/"
proc_dir = root_dir
bands = ["delta", "theta", "alpha", "sigma", "beta"]
factors = [["freqs","EEG Fpz-Cz",bands], ["freqs","EEG Pz-Oz",bands],
           ["amps",'EOG horizontal']]

with open("{}freq_mat.pickle".format(proc_dir), "rb") as f:
    freqs = pickle.load(f)
features = dict_to_array(freqs, factors)
ys = np.load("{}ys.npy".format(proc_dir))

x_train, x_test, y_train, y_test = train_test_split(features, ys, test_size=0.2)
hyper_params = {"n_estimators":[100,150,200,250,300], "max_features":[None, "sqrt", "log2"]}

clf = GridSearchCV(RandomForestClassifier(), hyper_params, n_jobs=4, verbose=10)
clf.fit(x_train, y_train)

y_pred = clf.predict(x_test)

with open("hyperparameter_CV.txt", "wt") as f:
    f.write(classification_report(y_test, y_pred))
best_model = clf.best_estimator_
best_model.fit(features, ys)
with open("sleep_stage_classifier.pickle", "wb") as f:
    pickle.dump(best_model, f)
