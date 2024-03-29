import mne
from mne.time_frequency import read_tfrs
import statsmodels.formula.api as smf
from statsmodels.regression.mixed_linear_model import MixedLM
import argparse
import pandas as pd
from os.path import isdir
import re
import numpy as np
import matplotlib.pyplot as plt
from mne.stats.cluster_level import _find_clusters
import pickle
plt.ion()
import warnings
warnings.filterwarnings("ignore")

def mass_uv_lmm(data, endog, exog, groups):
    exog_n = exog.shape[1]
    dat = data.reshape(len(data), data.shape[1]*data.shape[2])
    fits = []
    for pnt_idx in range(dat.shape[1]):
        print("{} of {}".format(pnt_idx, dat.shape[1]))
        endog = dat[:, pnt_idx]
        this_mod = MixedLM(endog, exog, groups)
        try:
            fits.append(this_mod.fit(reml=False))
        except:
            print("\nCoudn't fit model.\n")
            fits.append(None)
    return fits

if isdir("/home/jev"):
    root_dir = "/home/jev/hdd/sfb/"
elif isdir("/home/jeff"):
    root_dir = "/home/jeff/hdd/jeff/sfb/"
elif isdir("/home/jeffhanna/"):
    root_dir = "/scratch/jeffhanna/sfb/"
proc_dir = root_dir+"proc/"

n_jobs = 8
chan = "central"
baseline = "zscore"
osc = "SO"
durs = ["30s","2m","5m"]
sync_facts = ["syncfact", "nosyncfact"]
#sync_facts = ["syncfact"]
use_groups = ["group", "nogroup"]
#use_groups = ["nogroup"]
balance_conds = False
bootstrap = True
use_badsubjs = {"all_subj":[]}
use_badsubjs = {"bad10":["054","027","045","002","044","046","028","009","015","003"]}
use_badsubjs = {"bad7":["054","027","045","002","028","009","003"]}
use_badsubjs = {"sync":['002','003','005','006','007','009','013','015','016',
                        '017','018','021','022','024','025','026','027','028']}

for bs_name, bad_subjs in use_badsubjs.items():
    for use_group in use_groups:
        for sync_fact in sync_facts:
            for dur in durs:
                tfr = read_tfrs("{}grand_central_{}-tfr.h5".format(proc_dir, baseline))[0]
                tfr = tfr["OscType=='{}' and PrePost=='Post'".format(osc)]
                subjs = np.unique(tfr.metadata["Subj"].values)
                col = "Cond"
                t_string = "sham{}".format(dur)
                tfr = tfr["Cond=='eig{}' or Cond=='fix{}' or Cond=='sham{}'".format(dur,dur,dur)]
                # remove all subjects with missing conditions or not meeting synchronicity criterion
                for bs in bad_subjs:
                    print("Removing subject {}".format(bs))
                    tfr = tfr["Subj!='{}'".format(bs)]
                data = np.swapaxes(tfr.data[:,0],1,2)
                if baseline == "mean":
                    data *= 1e+12
                df = tfr.metadata.copy()
                df["Brain"] = np.zeros(len(df),dtype=np.float64)

                if sync_fact == "syncfact":
                    formula = "Brain ~ C({}, Treatment('{}'))*C(Sync, Treatment('sync'))".format(col,t_string)
                else:
                    formula = "Brain ~ C({}, Treatment('{}'))".format(col,t_string)
                outfile = "{}main_fits_{}_cond_{}_{}_{}_{}_{}.pickle".format(proc_dir, baseline, osc, dur, bs_name, use_group, sync_fact)
                groups = df["Subj"] if use_groups == "group" else pd.Series(np.zeros(len(df),dtype=int))
                md = smf.mixedlm(formula, df, groups=groups)
                endog, exog, groups, exog_names = md.endog, md.exog, md.groups, md.exog_names
                print(exog_names)
                #main result
                fits = mass_uv_lmm(data, endog, exog, groups)
                fits = {"exog_names":exog_names, "fits":fits}
                with open(outfile, "wb") as f:
                    pickle.dump(fits, f)
                del fits
