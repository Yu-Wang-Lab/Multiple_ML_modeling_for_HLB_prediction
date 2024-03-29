# Set work directory
import os
os.chdir("X:\\data\CN")
os.getcwd()

# Import packages
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import confusion_matrix
from sklearn.metrics import roc_curve, auc
from sklearn import metrics
from sklearn.linear_model import LogisticRegression
from sklearn import svm
from sklearn.neural_network import MLPClassifier
import matplotlib.pyplot as plt
import itertools
import warnings
from sklearn import manifold
from sklearn.metrics import matthews_corrcoef

# Ignore warnings
warnings.simplefilter("ignore")

# Define initial method and variable    
def testv1(method = 'rf'):
    accm = []
    senm = []
    spsm = []
    roc_aucm = []
    npvm = []
    prsm = []
    f1scorem = []
    tprs = []
    mccm = []
    mean_fpr = np.linspace(0, 1, 100)
    
    # Load data
    hd = pd.read_csv('data_healthy.csv')
    nhd = pd.read_csv('data_infected.csv')
    hd = hd.dropna()
    nhd = nhd.dropna()
    
    # Read features names
    feat = list(hd)
    feat = feat[1:]
    
    # Convert to numpy array
    hd = hd.values
    nhd = nhd.values
    
    # Read features and labels
    hdl = np.zeros((len(hd),))
    hdf = hd[:,1:]
    nhdl = np.ones((len(nhd),))
    nhdf = nhd[:,1:]
    
    # Apply cross-validation and multiple machine learning algorithms
    cv = StratifiedKFold(n_splits = 12, random_state = None, shuffle = False) # K-fold cross validation
    wdata = np.concatenate((hdf,nhdf))
    est_labels = np.zeros((len(wdata),))
    wlabel = np.concatenate((hdl,nhdl))
    stratified_10folds = cv.split(wdata, wlabel) #five folds
    importances = []
    
    for trind, teind in stratified_10folds:
        tr = wdata[trind] 
        trl = wlabel[trind]
        te = wdata[teind]
        tel = wlabel[teind]
        
        if method == 'rf':
           model = RandomForestClassifier(n_estimators =  60, max_depth = 2, random_state = 0).fit(tr,trl)
           importances.append(model.feature_importances_)
        if method == 'gbt':
           model = GradientBoostingClassifier(n_estimators =  60, max_depth = 2, random_state = 0).fit(tr,trl)
           importances.append(model.feature_importances_)

        elif method == 'lr-l1':
           model = LogisticRegression(penalty = 'l1', solver = 'liblinear').fit(tr,trl)
           importances.append(np.reshape(model.coef_,(len(feat,))))
        elif method == 'lr-l2':
           model = LogisticRegression(penalty = 'l2', solver = 'liblinear').fit(tr,trl)
           importances.append(np.reshape(model.coef_,(len(feat,))))
        elif method ==  'svm':
           model = svm.SVC(kernel = 'linear',probability = True).fit(tr,trl)
           importances.append(np.reshape(model.coef_,(len(feat,))))
        elif method == 'mlp':
           model = MLPClassifier(solver = 'adam', alpha = 1e-5, hidden_layer_sizes = (10, 4), random_state = 1).fit(tr,trl)
           importances.append(np.max(model.coefs_[0],axis = 1))
        
        pred = model.predict_proba(te)[:,1]
        thr = find_thr(model.predict_proba(tr)[:,1],trl)
        prr = np.where(pred > thr, 1, 0)
        est_labels[teind] = prr
        
        acc,sen,sps,roc_auc,prs,npv,f1score,mcc = performance_calculation(tel,prr,pred)
        accm.append(100*acc)
        senm.append(100*sen)
        spsm.append(100*sps)
        roc_aucm.append(100*roc_auc)
        prsm.append(100*prs)
        npvm.append(100*npv)
        f1scorem.append(100*f1score)
        mccm.append(100*mcc)
        
        fpr, tpr, thresholds = roc_curve(tel, pred)
        tprs.append(np.interp(mean_fpr, fpr, tpr))
        tprs[-1][0] = 0.0
    
    indices = np.argsort(np.mean(importances,axis = 0))[::-1]
    sorted_features = []
    for f in range(len(indices)):
        sorted_features.append(feat[indices[f]])
    # Save confusion matrix
    plot_confusion_matrix(confusion_matrix(wlabel,est_labels),['Healthy','Infected'],m + '_confusion_matrix.eps')
    
    # Save ROC curve
    plt.figure()
    mean_tpr = np.mean(tprs, axis = 0)
    mean_tpr[-1] = 1.0
    mean_auc = auc(mean_fpr, mean_tpr)
    std_auc = np.std(roc_aucm)
    plt.plot(mean_fpr, mean_tpr, color = 'b', label = r'Mean ROC (AUC = %0.2f $\pm$ %0.2f)' % (mean_auc, std_auc),lw = 2, alpha = .8)
    plt.plot([0, 1], [0, 1], color = 'navy', linestyle = '--')
    std_tpr = np.std(tprs, axis = 0)
    tprs_upper = np.minimum(mean_tpr + std_tpr, 1)
    tprs_lower = np.maximum(mean_tpr - std_tpr, 0)
    plt.fill_between(mean_fpr, tprs_lower, tprs_upper, color = 'grey', alpha = .2, label = r'$\pm$ 1 std. dev.')
    plt.xlabel('False Positive Rate (1 - Specificity)')
    plt.ylabel('True Positive Rate (Sensitivity)')
    
    plt.savefig(m + '_roc_curve.eps', format = 'eps', dpi = 1000)
    plt.close()
    return sorted_features, accm, senm*100, spsm*100, roc_aucm*100, prsm*100, npvm*100, f1scorem*100, est_labels, mccm, model

    # Convert to numpy array
    hd = hd.values
    nhd = nhd.values
    hdf = hd[:,1:]
    nhdf = nhd[:,1:]
    data = np.concatenate((hdf,nhdf))
    
    # Read features and labels
    hdl = np.zeros((len(hd),))
    nhdl = np.ones((len(nhd),))
    labels = np.concatenate((hdl,nhdl))
    
    fig = plt.figure(figsize = (6, 6))
    ax = plt.subplot(111)
    
    target_ids = range(2)
    tl = labels
    colors = ['darkgreen','orange']
    for i, c1, label in zip(target_ids, colors, ['Healthy', 'Infected']):
        plt.scatter(rdata[tl ==  i, 0], rdata[tl ==  i, 1], c = c1, label = label)
            
    chartBox = ax.get_position()
    ax.set_position([chartBox.x0, chartBox.y0, chartBox.width, chartBox.height])
    lgd =  ax.legend(loc = 'upper center', bbox_to_anchor = (1.2, 1), shadow = True, ncol = 1)
    plt.close(fig)

# Calculate performance
def performance_calculation(array1,array2,array3):
     tn, fp, fn, tp = confusion_matrix(array1,array2).ravel()
     total = tn+fp+fn+tp
     acc =  (tn+tp)/total
     sen = tp/(tp+fn)
     sps = tn/(tn+fp)
     prs = tp/(tp+fp)
     npv = tn/(tn+fn)
     f1score = 2* (sen*prs)/(prs+sen)
     fpr, tpr, thresholds = metrics.roc_curve(array1, array3)
     roc_auc = metrics.auc(fpr, tpr)
     mcc =  matthews_corrcoef(array1,array2)
     
     return acc,sen,sps,roc_auc,prs,npv,f1score,mcc

def find_thr(pred,label):
    
    # Find the best threshold where FPR and FNR points cross
    minn = 100000
    thrr = 0.4
    
    for thr in np.arange(0.1,1,0.05):
        prr = np.where(pred > thr, 1, 0)
        tn, fp, fn, tp = confusion_matrix(label,prr).ravel()
        if tp+fn > 0:
            frr = fn/(tp+fn)
        else:
            frr = 0
        if tn+fp > 0:    
            far = fp/(tn+fp)
        else:
            far = 0 
        if np.abs(frr - far) < minn:
            minn = np.abs(frr + far)
            thrr = thr
            
    return thrr
 
def plot_confusion_matrix(cm, classes, name, normalize = False, cmap = plt.cm.Blues):
    if normalize:
        cm = cm.astype('float') / cm.sum(axis = 1)[:, np.newaxis]

    plt.imshow(cm, interpolation = 'nearest', cmap = cmap)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes)
    plt.yticks(tick_marks, classes)

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j],horizontalalignment = "center", color = "white" if cm[i, j] > thresh else "black")

    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    plt.savefig(name, format = 'eps', dpi = 1000)
    plt.close()
    
# Test models
methods = ['lr-l1','lr-l2','mlp','rf','gbt','svm']
file = open('performance.txt',"w")
file.write('Method, Accuracy, Sensitivity, Specificity, AUC, Precision, Negative Predictive Value, F1 Score, MCC \n')

for m in methods:
    sorted_features, accm, senm, spsm, roc_aucm, prsm, npvm, f1scorem, est_labels, mccm, model = testv1(m)
    file.write(m + ':, ')
    file.write("%0.2f \u00B1 %0.2f, %0.2f \u00B1 %0.2f, %0.2f \u00B1 %0.2f, %0.2f \u00B1 %0.2f, %0.2f \u00B1 %0.2f, %0.2f \u00B1 %0.2f, %0.2f \u00B1 %0.2f,  %0.2f \u00B1 %0.2f \n" % (np.mean(accm),np.std(accm),np.mean(senm),np.std(senm),np.mean(spsm),np.std(spsm),np.mean(roc_aucm),np.std(roc_aucm),np.mean(prsm),np.std(prsm),np.mean(npvm),np.std(npvm),np.mean(f1scorem),np.std(f1scorem),np.mean(mccm),np.std(mccm)))
    df = pd.DataFrame(data = {"features": sorted_features})
    df.to_csv(m +'_ranked_features.csv', sep = ',',index = False)
    np.savetxt(m+'_estimated_labels.csv', est_labels.astype(np.int),delimiter = ', ',fmt = '%d')
    
    exec ("mdl_%s=model"%m[-1])
    if m == 'rf' or m == 'gbt':
      exec ("importance_%s = model.feature_importances_"%m[-1])
    if m == 'lr-l1' or m == 'lr-l2' or m == 'svm':
      exec ("coef_%s = model.coef_"%m[-1])
      exec ("intercept_%s = model.intercept_"%m[-1])
    if m == 'mlp':
      exec ("coef_%s=model.coefs_"%m[-1])
      exec ("intercepts_%s = model.intercepts_"%m[-1])

file.close()

## ----------------------------External test----------------------------
# Import test data
td = pd.read_csv('data_test.csv')
tdv = td.iloc[0:,2:]
tdv

# Predict label
pred_lr_l1 = mdl_1.predict(tdv)
print(pred_lr_l1)
pred_proba_lr_l1 = mdl_1.predict_proba(tdv)[:, 1]
print(pred_proba_lr_l1)

pred_lr_l2 = mdl_2.predict(tdv)
print(pred_lr_l2)
pred_proba_lr_l2 = mdl_2.predict_proba(tdv)[:, 1]
print(pred_proba_lr_l2)

pred_mlp = mdl_p.predict(tdv)
print(pred_mlp)
pred_proba_mlp = mdl_p.predict_proba(tdv)[:, 1]
print(pred_proba_mlp)

pred_rf = mdl_f.predict(tdv)
print(pred_rf)
pred_proba_rf = mdl_f.predict_proba(tdv)[:, 1]
print(pred_proba_rf)

pred_gbt = mdl_t.predict(tdv)
print(pred_gbt)
pred_proba_gbt = mdl_t.predict_proba(tdv)[:, 1]
print(pred_proba_gbt)

pred_svm = mdl_m.predict(tdv)
print(pred_svm)
pred_proba_svm = mdl_m.predict_proba(tdv)[:, 1]
print(pred_proba_svm)



