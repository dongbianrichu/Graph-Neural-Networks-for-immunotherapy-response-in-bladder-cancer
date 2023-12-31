import sys
import os
import pandas as pd
import numpy as np
import tqdm
import torch
from sklearn.metrics import roc_auc_score
from utils import seed_torch
import random



###############################################################################
#                                                                             #
#               　　　　　　　  Ｄefine metrics     　　                         #
#                                                                             #
###############################################################################
def get_auc(outputs, labels):
    auc = roc_auc_score(labels, outputs)
    return auc


def get_acc(output, target):
    output = torch.sigmoid(output) >= 0.5
    target = target == 1.0
    return torch.true_divide((target == output).sum(dim=0), output.size(0)).item()


###############################################################################
#                                                                             #
#               　　　　　　　  Get sample's label  　　                         #
#                                                                             #
###############################################################################
def get_labels(dataset, df_os_1):
    real_labels = []
    for smp, data in dataset.items():
        if smp in df_os_1.id.values:
            real_labels.append(0.0)
        else:
            real_labels.append(1.0)
    real_labels = torch.tensor(real_labels)

    return real_labels



###############################################################################
#                                                                             #
#               　　　　　　　 transform dataset                                 #
#                                                                             #
###############################################################################
def transform_dataset(dataset, df_os_1, df_os_2):
    group1_smp = df_os_1.id.to_list()
    group2_smp = df_os_2.id.to_list()
    seed_torch(42)
    random.shuffle(group1_smp)
    seed_torch(42)
    random.shuffle(group2_smp)

    # train_dataset
    total_dataset = {}
    total_labels = []
    labels_ = group1_smp + group2_smp
    seed_torch(42)
    random.shuffle(labels_)
    for l in labels_:
        total_dataset[l] = dataset[l]
        if l in group1_smp:
            total_labels.append(0.0)
        else:
            total_labels.append(1.0)
    total_labels = torch.tensor(total_labels)

    return total_labels, total_dataset


###############################################################################
#                                                                             #
#               　　　　　　　  Define Evaluation        　　                    #
#                                                                             #
###############################################################################

def evalation(test_labels, test_dataset):

    # validation
    test_auc, test_acc = test_func(test_labels, test_dataset)

    print(
        'Acc: {:.5f}, Auc: {:.5f}\n'.format(
            test_acc, test_auc))


    return model



###############################################################################
#                                                                             #
#               　　　　　　　  Define Test         　　                         #
#                                                                             #
###############################################################################

def test_func(test_labels, test_dataset):
    out_probs = []
    for smp, data in tqdm.tqdm(test_dataset.items()):
        model.eval()
        with torch.no_grad():
            out_probs.append(model(data, device=device))

    out_probs = torch.cat(out_probs, dim=0).reshape(-1, 2).cpu()

    # output batch auc
    auc = get_auc(out_probs.detach().numpy()[:, 1], test_labels)

    # output batch acc
    out_classes = np.argmax(out_probs.detach().numpy(), axis=1)
    acc = sum(out_classes == test_labels.detach().numpy()) / len(test_labels)

    return auc, acc


#############################################################################
#                                                                             #
#               　　　　　　　  Define Predict        　　                         #
#                                                                             #
###############################################################################

def predict(test_dataset,outfile):
    out_probs = []
    for smp, data in tqdm.tqdm(test_dataset.items()):
        model.eval()
        with torch.no_grad():
            out_probs.append(model(data, device=device))

    out_probs = torch.cat(out_probs, dim=0).reshape(-1, 2).cpu()

    # output to
    out_classes = np.argmax(out_probs.detach().numpy(), axis=1)
    np.savetxt(outfile, out_classes, fmt='%.1f', delimiter=',')

    return  out_classes




if __name__ == '__main__':
    # set seed
    seed_torch(1024)

    train_step = True
    # Get configures
    #config = get_config(sys.argv[1])
    ## device
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    ## project root dir
    project_root_dir = './'
    ## dataset file path
    path_dataset = os.path.join(project_root_dir, 'Dataset/pathway_reactome_ssgsea4.pt')
    ## cilical file path
    path_cli = os.path.join(project_root_dir, 'Dataset/clinical.txt')
    ## model
    path_model = os.path.join(project_root_dir, 'ICI_predict_model.pt')
    ## model_run
    model_predict = 'True'
    ## 输出预测结果
    outfile_tcga = 'predict_result.csv'

    # Run Group for Patients
    df_os = pd.read_table(path_cli)
    df_os_1 = df_os[df_os.Type == 0]
    df_os_2 = df_os[df_os.Type == 1]
    print('Non-responder number: {}; Responder number: {}'.format(df_os_1.shape[0], df_os_2.shape[0]))

    # Read dataset
    print('[INFO] Load dataset...\n')
    dataset = torch.load(path_dataset)

    transformed_labels, transformed_dataset = transform_dataset(dataset, df_os_1, df_os_2)

    if model_predict == "True":
        print('[INFO] model  predicting...\n')
        torch.backends.cudnn.enabled = False

        if os.path.exists(path_model):
            print('[INFO] loading\n')
            model = torch.load(path_model).to(device)
            predict_label1 = evalation(transformed_labels, transformed_dataset)
            predict_label2 = predict(transformed_labels, transformed_dataset)

        else:
            os._exit()




