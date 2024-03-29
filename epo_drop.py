import mne
from os import listdir
import re
import numpy as np
from os.path import isdir

if isdir("/home/jev"):
    root_dir = "/home/jev/hdd/sfb/"
elif isdir("/home/jeff"):
    root_dir = "/home/jeff/hdd/jeff/sfb/"
proc_dir = root_dir+"proc/"
conds = ["eig5m","fix5m","eig2m","fix2m","eig30s","fix30s","sham30s", "sham2m", "sham5m"]
filelist = listdir(proc_dir)
chans = ["central"]

for filename in filelist:
    this_match = re.match("NAP_(\d{3})_(.*)_(.*)_(.*)-epo.fif",filename)
    if this_match:
        subj, cond = this_match.group(1), this_match.group(2)
        ort, osc_type = this_match.group(3), this_match.group(4)
        if cond not in conds:
            continue
        epo = mne.read_epochs(proc_dir+filename)
        picks = mne.pick_channels(epo.ch_names,chans)
        epo_data = epo.get_data()
        thresh = 5e-4
        print("Threshold: {}".format(thresh))
        drop_inds = []
        pick = picks[chans.index(ort)]
        for epo_idx in range(len(epo)):
            if (epo_data[epo_idx,pick,].max() -
                epo_data[epo_idx,pick,].min()) > thresh:
                drop_inds.append(epo_idx)
        print(drop_inds)

        #drop_inds = []  # DROP NOTHING

        epo.drop(drop_inds)
        if len(epo):
            epo.save("{}d_NAP_{}_{}_{}_{}-epo.fif".format(proc_dir,subj,cond,ort,osc_type), overwrite=True)
