import mne
import numpy as np
import pandas as pd
from scipy.stats import circmean
from os.path import join
import statsmodels.formula.api as smf
import seaborn as sns
from circular_hist import circ_hist_norm
import matplotlib.pyplot as plt
from pycircstat.tests import watson_williams, vtest, kuiper
from astropy.stats import kuiper_two
plt.ion()
import matplotlib
font = {'weight' : 'bold',
        'size'   : 28}
matplotlib.rc('font', **font)

def r_vector(rad):
    x_bar, y_bar = np.cos(rad).mean(), np.sin(rad).mean()
    r_mean = circmean(rad, low=-np.pi, high=np.pi)
    r_norm = np.linalg.norm((x_bar, y_bar))

    return r_mean, r_norm


root_dir = "/home/jev/hdd/sfb2/"
proc_dir = join(root_dir, "proc")
fig_dir = join(root_dir, "figs")

ROIs = ["frontal", "parietal"]
pfs = [[12, 15], [15, 18]]

for ROI in ROIs:
    epo = mne.read_epochs(join(proc_dir, f"grand_{ROI}_SI-epo.fif"))
    df = epo.metadata

    subjs = list(df["Subj"].unique())
    subjs.sort()
    conds = ["sham", "stim"]
    polarities = ["anodal", "cathodal"]
    osc_types = ["SO"]

    SI_df_dict = {"Subj":[], "OscType":[], "Cond":[], "StimType":[],
                "Polarity":[], "SI_norm":[], "SM_norm":[], "SI_mean":[], "SM_mean":[]}
    for pf in pfs:
        for subj in subjs:
            for osc in osc_types:
                for cond in conds:
                    for polarity in polarities:
                        query_str = f"Subj=='{subj}' and OscType=='{osc}' and Cond=='{cond}' and Polarity=='{polarity}'"
                        this_df = df.query(query_str)
                        if len(this_df) > 10:
                            SIs = this_df["SI"].values
                            SMs = this_df["Spind_Max_{}-{}Hz".format(pf[0], pf[1])].values
                            SI_mean, SI_r_norm = r_vector(SIs)
                            SM_mean, SM_r_norm = r_vector(SMs)
                            SI_df_dict["Subj"].append(subj)
                            SI_df_dict["OscType"].append(osc)
                            SI_df_dict["Cond"].append(cond)
                            SI_df_dict["StimType"].append(cond)
                            SI_df_dict["Polarity"].append(polarity)
                            SI_df_dict["SI_norm"].append(SI_r_norm)
                            SI_df_dict["SM_norm"].append(SM_r_norm)
                            SI_df_dict["SI_mean"].append(SI_mean)
                            SI_df_dict["SM_mean"].append(SM_mean)
        SI_df = pd.DataFrame.from_dict(SI_df_dict)

        for osc in osc_types:
            fig, axes = plt.subplots(len(conds),len(polarities),figsize=(38.4,21.6),
                                    subplot_kw={"projection":"polar"})
            for pol_idx, pol in enumerate(polarities):
                for cond_idx, cond in enumerate(conds):
                    query_str = f"OscType=='{osc}' and Cond=='{cond}' and Polarity=='{pol}'"
                    this_df = df.query(query_str)
                    this_SI_df = SI_df.query(query_str)
                    subj_spinds = this_SI_df["SM_mean"].values
                    subj_mean, subj_r_norm = r_vector(subj_spinds)
                    mean, r_norm = r_vector(this_df["Spind_Max_{}-{}Hz".format(pf[0], pf[1])].values)
                    vecs = [[(subj_mean, subj_r_norm), {"color":"red","linewidth":4}],
                            [(mean, r_norm), {"color":"blue","linewidth":4}]]
                    circ_hist_norm(axes[pol_idx, cond_idx], this_df[f"Spind_Max_{pf[0]}-{pf[1]}Hz"].values,
                                points=subj_spinds, vecs=vecs, alpha=0.3,
                                points_col="red", bins=48)
                    axes[pol_idx,cond_idx].set_title(f"{cond} {pol}")
            plt.suptitle(f"Spindle ({pf[0]}-{pf[1]}Hz) Peak on {osc} phase, {ROI}")
            plt.tight_layout()
            plt.savefig(join(fig_dir, f"polar_hist_{osc}_{pf[0]}-{pf[1]}Hz_{ROI}.png"))

        d = SI_df.query("OscType=='SO'")
        fig, ax = plt.subplots(figsize=(38.4,21.6))
        sns.barplot(data=d, x="Cond", hue="Polarity", y="SM_norm", ax=ax)
        plt.ylabel("Resultant Vector")
        plt.suptitle("Slow Oscillations")
        plt.savefig(join(fig_dir, "resvec_bar_SO_all.png"))

        formula = "SM_norm ~ C(StimType, Treatment('sham'))*C(Polarity, Treatment('anodal'))"
        mod = smf.mixedlm(formula, data=d, groups=SI_df["Subj"])
        mf = mod.fit(reml=False)
        print(mf.summary())

        formula = "SI_norm ~ C(StimType, Treatment('sham'))*C(Polarity, Treatment('anodal'))"
        mod = smf.mixedlm(formula, data=d, groups=SI_df["Subj"])
        mf = mod.fit(reml=False)
        print(mf.summary())

# # for figure 1
# pfs = [[12, 15], [15, 18]]
# mos_text = '''
#            PPP
#            012
#            012
#            012
#            012
#            012
#            012
#            012
#            345
#            345
#            345
#            345
#            345
#            345
#            345
#            '''
# fig, axes = plt.subplot_mosaic(mos_text, subplot_kw={"projection":"polar"},
#                                figsize=(21.6, 21.6))
# for pf_idx, pf in enumerate(pfs):
#     print("\n{}-{}Hz".format(pf[0], pf[1]))
#     SI_df_dict = {"Subj":[], "Sync":[], "OscType":[], "StimType":[],
#                   "SM_norm":[], "SM_mean":[]}
#     for subj in subjs:
#         for osc in osc_types:
#             for cond in conds:
#                 query_str = "Subj=='{}' and OscType=='{}' and StimType=='{}'".format(subj, osc, cond)
#                 this_df = df.query(query_str)
#                 if len(this_df) > 10:
#                     SIs = this_df["SI"].values
#                     SMs = this_df["Spind_Max_{}-{}Hz".format(pf[0], pf[1])].values
#                     SI_mean, SI_r_norm = r_vector(SIs)
#                     SM_mean, SM_r_norm = r_vector(SMs)
#                     SI_df_dict["Subj"].append(subj)
#                     SI_df_dict["Sync"].append(this_df["Sync"].iloc[0])
#                     SI_df_dict["OscType"].append(osc)
#                     SI_df_dict["StimType"].append(cond)
#                     SI_df_dict["SM_norm"].append(SM_r_norm)
#                     SI_df_dict["SM_mean"].append(SM_mean)

#     SI_df = pd.DataFrame.from_dict(SI_df_dict)

#     colors = ["blue", "red", "green"]
#     cond_subj_spinds = {}
#     cond_spinds = {}
#     for cond_idx, cond in enumerate(conds):
#         #this_ax = axes[pf_idx, cond_idx]
#         this_ax = axes[str(cond_idx + pf_idx*3)]
#         query_str = "OscType=='SO' and StimType=='{}'".format(cond)
#         this_df = df.query(query_str)
#         this_SI_df = SI_df.query(query_str)
#         cond_subj_spinds[cond] = this_SI_df["SM_mean"].values
#         cond_spinds[cond] = this_df["Spind_Max_{}-{}Hz".format(pf[0], pf[1])].values
#         subj_mean, subj_r_norm = r_vector(cond_subj_spinds[cond])
#         mean, r_norm = r_vector(this_df["Spind_Max_{}-{}Hz".format(pf[0], pf[1])].values)
#         print("{}: subj_mean: {}/{} subj_r_norm: {}".format(cond, np.round(subj_mean, 3), np.round(360+np.rad2deg(subj_mean), 2), np.round(subj_r_norm, 2)))
#         print("{}: mean: {}/{} r_norm: {}\n".format(cond, np.round(mean, 3), np.round(360+np.rad2deg(mean), 2), np.round(r_norm, 2)))
#         vecs = [[(subj_mean, subj_r_norm), {"color":"gray","linewidth":8}],
#                 [(mean, r_norm), {"color":colors[cond_idx],"linewidth":8}]]
#         circ_hist_norm(this_ax, this_df["Spind_Max_{}-{}Hz".format(pf[0], pf[1])].values,
#                        points=cond_subj_spinds[cond], vecs=vecs, alpha=0.3,
#                        color=colors[cond_idx], points_col="gray", bins=24,
#                        dot_size=280)
#         this_ax.tick_params(pad=25)


# plt.suptitle("Spindle Peak on SO phase", fontsize=52)
# axes["P"].axis("off")
# #axes["W"].axis("off")
# axes["0"].set_title("12-15Hz\n", fontsize=52)
# axes["3"].set_title("15-18Hz\n", fontsize=52)
# axes["3"].set_xlabel("\nSham", fontsize=52)
# axes["4"].set_xlabel("\nEigen frequency", fontsize=52)
# axes["5"].set_xlabel("\nFixed frequency", fontsize=52)
# plt.tight_layout()
# plt.savefig("../images/polar_hist_fig1_SO_{}".format(method))
# plt.savefig("../images/polar_hist_fig1_SO_{}.svg".format(method))
