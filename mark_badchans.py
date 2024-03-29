import mne
from os import listdir
import re
from anoar import BadChannelFind
from os.path import isdir


root_dir = "/home/jev/hdd/sfb/"

proc_dir = root_dir+"proc/"
conds = ["eig5m","fix5m","eig2m","fix2m","eig30s","fix30s","sham30s", "sham2m", "sham5m"]
filelist = listdir(proc_dir)

for filename in filelist:
    this_match = re.match("scaf_NAP_(\d{3})_(.*)-raw.fif",filename)
    if this_match:
        subj, cond = this_match.group(1), this_match.group(2)
        if cond not in conds:
            continue
        raw = mne.io.Raw(proc_dir+filename,preload=True)
        picks = mne.pick_types(raw.info, eeg=True)
        bcf = BadChannelFind(picks, thresh=0.5)
        bad_chans = bcf.recommend(raw)
        print(bad_chans)
        raw.info["bads"].extend(bad_chans)
        raw.save("{}bscaf_NAP_{}_{}-raw.fif".format(proc_dir,subj,cond),overwrite=True)
