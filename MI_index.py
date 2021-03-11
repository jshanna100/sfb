import mne
from tensorpac import Pac
from tensorpac.methods import modulation_index, phase_locking_value
import pandas as pd
import numpy as np
from os.path import isdir
import matplotlib.pyplot as plt
import pickle
plt.ion()


if isdir("/home/jev"):
    root_dir = "/home/jev/hdd/sfb/"
elif isdir("/home/jeff"):
    root_dir = "/home/jeff/hdd/jeff/sfb/"
proc_dir = root_dir+"proc/"

n_jobs = 4
chan = "central"
osc_types = ["SO", "deltO"]
#osc_types = ["SO"]
sfreq = 100.
phase_freqs = [(0.16, 1.25),(1.25, 4)]
power_freqs = (13, 16)
conds = ["sham", "eig", "fix"]
durs = ["30s", "2m", "5m"]
osc_cuts = [(-1.25,1.25),(-.75,.75)]
osc_cuts = [(.15,.7),(-.75,.75)]
method = "hilbert"

epo = mne.read_epochs("{}grand_{}_finfo-epo.fif".format(proc_dir, chan),
                      preload=True)
epo.resample(sfreq, n_jobs="cuda")

osc_types = ["SO", "deltO"]
epos = []
dfs = []
for osc, osc_cut, pf in zip(osc_types, osc_cuts, phase_freqs):
    p = Pac(f_pha=np.linspace(pf[0],pf[1],10),
            f_amp=np.linspace(power_freqs[0],power_freqs[1],10),
            dcomplex=method)

    this_epo = epo["OscType == '{}'".format(osc)]
    this_df = this_epo.metadata.copy()
    cut_inds = this_epo.time_as_index((osc_cut[0], osc_cut[1]))
    data = this_epo.get_data()[:,0,] * 1e+6

    phase = p.filter(this_epo.info["sfreq"], data, ftype="phase", n_jobs=n_jobs)
    power = p.filter(this_epo.info["sfreq"], data, ftype="amplitude", n_jobs=n_jobs)

    power = power[...,cut_inds[0]:cut_inds[1]]#.mean(0)
    phase = phase[...,cut_inds[0]:cut_inds[1]]#.mean(0)

    p.idpac = (1,0,0)
    mvl = p.fit(phase, power)
    mvl = mvl.mean(0).mean(0)
    mvl = {"pac":mvl, "pvals":p.pvalues}
    with open("{}mvl_{}.pickle".format(proc_dir, osc), "wb") as f:
        pickle.dump(mvl, f)
    p.idpac = (5,0,0)
    plv = p.fit(phase, power)
    plv = plv.mean(0).mean(0)
    plv = {"pac":plv, "pvals":p.pvalues}
    with open("{}plv_{}_{}.pickle".format(proc_dir, osc, method), "wb") as f:
        pickle.dump(plv, f)
    p.idpac = (4,0,0)
    nd = p.fit(phase, power)
    nd = nd.mean(0).mean(0)
    nd = {"pac":nd, "pvals":p.pvalues}
    with open("{}nd_{}_{}.pickle".format(proc_dir, osc, method), "wb") as f:
        pickle.dump(nd, f)


    this_df["MVL"] = mvl["pac"]
    this_df["PLV"] = plv["pac"]
    this_df["ND"] = nd["pac"]
    dfs.append(this_df)

new_df = pd.concat(dfs, ignore_index=True)

new_df.to_pickle("{}ModIdx_{}.pickle".format(proc_dir, method))
