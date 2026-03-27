import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

import sklearn.linear_model as skl_lm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, det_curve, accuracy_score
import statsmodels.formula.api as smf

from sklearn.model_selection import train_test_split
from sklearn.metrics import DetCurveDisplay, RocCurveDisplay

# ==============================================================================
# Step 1: Data Processing
# ==============================================================================

# mortgage_data --> mData
# hpi_state     --> hData
# rate          --> rData
mData = pd.read_csv("data/mortgage_data.csv", dtype={"source": str})
mData['fthb_flg'] = mData.fthb_flg.factorize()[0]   # convert N/Y to 0/1
mData['source'] = mData.source.factorize()[0]         # convert FD/FN to 0/1
mData['ori_m'] = mData['frst_dte'].apply(lambda x: int(x.split('/')[1]))
mData['ori_y'] = mData['frst_dte'].apply(lambda x: int(x.split('/')[2]))

hData = pd.read_csv("data/hpi_state.csv")
hData = hData[(hData['year'] >= 1997) & (hData['year'] <= 2008)]

rData = pd.read_csv("data/rate.csv")
rData = rData[rData['year'] <= 2008]

# ------------------------------------------------------------------------------
# Append macro variables
# ------------------------------------------------------------------------------
mData.insert(mData.shape[1], 'pst_1year', 0.0)   # past one-year HPI change
mData.insert(mData.shape[1], 'pst_3year', 0.0)   # past three-year HPI change
mData.insert(mData.shape[1], 'frm_rate', 0.0)    # 30-year FRM rate
mData.insert(mData.shape[1], 'tre_rate', 0.0)    # 3-month treasury rate

for i in range(2000, 2008):
    # For January: use prior month (December of previous year),
    # except for year 2000 where we fall back to January itself.
    if i != 2000:
        tre_jan = rData[(rData['year'] == i - 1) & (rData['month'] == 12)].treasury_3mon_rate.iloc[0]
        frm_jan = rData[(rData['year'] == i - 1) & (rData['month'] == 12)].FRM30_rate.iloc[0]
    else:
        tre_jan = rData[(rData['year'] == i) & (rData['month'] == 1)].treasury_3mon_rate.iloc[0]
        frm_jan = rData[(rData['year'] == i) & (rData['month'] == 1)].FRM30_rate.iloc[0]

    mData.loc[(mData['ori_m'] == 1) & (mData['ori_y'] == i), 'tre_rate'] = tre_jan
    mData.loc[(mData['ori_m'] == 1) & (mData['ori_y'] == i), 'frm_rate'] = frm_jan

    for j in range(2, 13):
        tre = rData[(rData['year'] == i) & (rData['month'] == j - 1)].treasury_3mon_rate.iloc[0]
        frm = rData[(rData['year'] == i) & (rData['month'] == j - 1)].FRM30_rate.iloc[0]
        mData.loc[(mData['ori_m'] == j) & (mData['ori_y'] == i), 'tre_rate'] = tre
        mData.loc[(mData['ori_m'] == j) & (mData['ori_y'] == i), 'frm_rate'] = frm

mData.info()
print(mData.head(5))

# ==============================================================================
# Step 2: Train / Test Split (stratified by origination year)
# ==============================================================================

Xvari = [
    'source', 'Quarter_orig', 'orig_rt', 'oltv', 'ocltv', 'dti',
    'cscore_b', 'mi_pct', 'fthb_flg', 'num_bo', 'num_unit',
    'tre_rate', 'frm_rate'
]

X_train = pd.DataFrame()
y_train = pd.DataFrame()
X_test  = pd.DataFrame()
y_test  = pd.DataFrame()

for i in range(2000, 2007):
    a = mData[mData['Year_orig'] == i]
    X_tr, X_te, y_tr, y_te = train_test_split(
        a[Xvari], a[['delinquent30']], test_size=0.33, random_state=0
    )
    X_train = pd.concat([X_train, X_tr], axis=0)
    X_test  = pd.concat([X_test,  X_te], axis=0)
    y_train = pd.concat([y_train, y_tr], axis=0)
    y_test  = pd.concat([y_test,  y_te], axis=0)

# ==============================================================================
# Step 3: Statsmodels Logit (for coefficient summary)
# ==============================================================================

est1 = smf.logit(
    'delinquent30 ~ ' + ' + '.join(Xvari),
    pd.concat([X_train, y_train], axis=1)
).fit()
print(est1.summary().tables[1])

# ==============================================================================
# Step 4: Sklearn Logistic Regression (for prediction & evaluation)
# ==============================================================================

est = LogisticRegression(solver='lbfgs')
est.fit(X_train, y_train.values.ravel())

# --- Predict and check at threshold = 0.5 ---
y_pred = pd.DataFrame({'prob': est.predict(X_test)})
y_pred['prob'] = (y_pred['prob'] > 0.5).astype(int)
print(confusion_matrix(y_test, y_pred))
print('Accuracy:', accuracy_score(y_test, y_pred))

# ==============================================================================
# Step 5: Error Rate vs. Threshold (DET-style)
# ==============================================================================

probs_y = est.predict_proba(X_test)
fpr, fnr, thresholds = det_curve(y_test, probs_y[:, 1])

plt.figure()
plt.title("False positive rate vs. false negative rate", fontsize=16)
plt.plot(thresholds, fpr, "r--", label="False positive")
plt.plot(thresholds, fnr, "b--", label="False negative")
plt.ylabel("Error Rate")
plt.xlabel("Threshold")
plt.legend(loc="right")
plt.xlim([-0.05, 0.55])
plt.ylim([-0.05, 0.75])
plt.tight_layout()
plt.show()

# ==============================================================================
# Step 6: ROC and DET Curves
# ==============================================================================

fig, [ax_roc, ax_det] = plt.subplots(1, 2, figsize=(11, 5))

RocCurveDisplay.from_estimator(est, X_test, y_test, ax=ax_roc)
DetCurveDisplay.from_estimator(est, X_test, y_test, ax=ax_det)

ax_roc.set_title("ROC curve", fontsize=16)
ax_det.set_title("DET curve", fontsize=16)

fig.tight_layout()
plt.show()
