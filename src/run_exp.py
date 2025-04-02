import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
import optuna
import joblib

from tqdm import tqdm

import sys
sys.path.append("..")

import argparse
from src.utils.driver import train_single_model
from src.utils.visualization import visualize_embedding
from src.utils.crystal_metric import crystal_metric
import json

import os
from datetime import datetime

data_id_choices = ["lattice", "greater", "family_tree", "equivalence", "circle", "permutation"]
model_id_choices = ["H_MLP", "standard_MLP", "H_transformer", "standard_transformer"]
split_choices = [1,2,3,4,5,6,7, 8]
wd_choices = [0.0005, 0.001, 0.003, 0.005, 0.007, 0.01, 0.012, 0.015, 0.02, 0.03, 0.05, 0.07, 0.1]
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Experiment')
    parser.add_argument('--seed', type=int, default=66, help='random seed')
    parser.add_argument('--data_id', type=str, required=True, choices=data_id_choices, help='Data ID')
    parser.add_argument('--model_id', type=str, required=True, choices=model_id_choices, help='Model ID')
    parser.add_argument('--split', type=int, required=False, choices=split_choices, help='To split running experiments')
    parser.add_argument('--wd', type=float, required=False, choices=wd_choices, help='weight decay')
    parser.add_argument('--n', type=int, required=False, default=1, help='n exponent value')


args = parser.parse_args()
seed = args.seed
data_id = args.data_id
model_id = args.model_id
split=args.split
n_exp = args.n

## ------------------------ CONFIG -------------------------- ##

data_size = 1000
train_ratio = 0.8
embd_dim = 16

lr = 0.002
weight_decay = 0.01 if "MLP" in model_id else 0.005

param_dict = {
    'seed': seed,
    'data_id': data_id,
    'data_size': data_size,
    'train_ratio': train_ratio,
    'model_id': model_id,
    'device': torch.device('cuda:0' if torch.cuda.is_available() else 'cpu'),
    'embd_dim': embd_dim,
    'n_exp': n_exp,
    'lr': lr,
    'weight_decay':weight_decay
}

results_root = f"../results/n_experiments/{n_exp}"

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
results_root = f"{results_root}/{current_datetime}-{seed}-{data_id}-{model_id}"
os.mkdir(results_root)


param_dict_json = {k: v for k, v in param_dict.items() if k != 'device'} #  since torch.device is not JSON serializable


with open(f"{results_root}/config.json", "w") as f:
    json.dump(param_dict_json, f, indent=4)

aux_info = {}
if data_id == "lattice":
    aux_info["lattice_size"] = 5
elif data_id == "greater":
    aux_info["p"] = 30
elif data_id == "equivalence":
    aux_info["mod"] = 5
elif data_id == "circle":
    aux_info["p"] = 31
elif data_id == "family_tree":
    aux_info["dict_level"] = 2
elif data_id == "permutation":
    aux_info["p"] = 4
else:
    raise ValueError(f"Unknown data_id: {data_id}")

# # Optuna study for lr/wd
# def loss_objective(trial):
#     weight_decay = trial.suggest_float('wd', 0, 0.01)
#     lr = trial.suggest_float('lr', 0.002, 0.005)

#     param_dict = {
#     'seed': seed,
#     'data_id': data_id,
#     'data_size': data_size,
#     'train_ratio': train_ratio,
#     'model_id': model_id,
#     'device': torch.device('cuda:0' if torch.cuda.is_available() else 'cpu'),
#     'embd_dim': embd_dim,
#     'n_exp': n_exp,
#     'lr': lr,
#     'weight_decay':weight_decay
#     }

#     ret_dic = train_single_model(param_dict)

#     test_loss = np.mean(ret_dic["results"]["test_losses"][-10:])

#     return test_loss

# study = optuna.create_study()
# study.optimize(loss_objective, n_trials = 15)
# joblib.dump(study, "wd_lr_study.pkl")

# print(study.best_params)

# # Train the model
# print(f"Training model with seed {seed}, data_id {data_id}, model_id {model_id}, n_exp {n_exp}, embd_dim {embd_dim}, weight decay {weight_decay}")
# ret_dic = train_single_model(param_dict)

# ## Exp1: Visualize Embeddings
# print(f"Experiment 1: Visualize Embeddings")
# model = ret_dic['model']
# dataset = ret_dic['dataset']
# torch.save(model.state_dict(), f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.pt")

# if hasattr(model.embedding, 'weight'):
#     visualize_embedding(model.embedding.weight.cpu(), title=f"{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}", save_path=f"{results_root}/emb_{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.png", dict_level = dataset['dict_level'] if 'dict_level' in dataset else None, color_dict = False if data_id == "permutation" else True, adjust_overlapping_text = False)
# else:
#     visualize_embedding(model.embedding.data.cpu(), title=f"{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}", save_path=f"{results_root}/emb_{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.png", dict_level = dataset['dict_level'] if 'dict_level' in dataset else None, color_dict = False if data_id == "permutation" else True, adjust_overlapping_text = False)


# ## Exp2: Metric vs Overall Dataset Size (fixed train-test split)
# print(f"Experiment 2: Metric vs Overall Dataset Size (fixed train-test split)")
# data_size_list = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
# for i in tqdm(range(len(data_size_list))):
#     data_size = data_size_list[i]
#     param_dict = {
#         'seed': seed,
#         'data_id': data_id,
#         'data_size': data_size,
#         'train_ratio': train_ratio,
#         'model_id': model_id,
#         'device': torch.device('cuda' if torch.cuda.is_available() else 'cpu'),
#         'embd_dim': embd_dim,
#         'n_exp': n_exp,
#         'lr': lr,
#         'weight_decay':weight_decay
#     }

#     print(f"Training model with seed {seed}, data_id {data_id}, model_id {model_id}, n_exp {n_exp}, embd_dim {embd_dim}")
#     ret_dic = train_single_model(param_dict)
#     model = ret_dic['model']
#     dataset = ret_dic['dataset']

#     torch.save(model.state_dict(), f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.pt")
#     with open(f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}_train_results.json", "w") as f:
#         json.dump(ret_dic["results"], f, indent=4)
    
#     if data_id == "family_tree":
#         aux_info["dict_level"] = dataset['dict_level']
    
#     if hasattr(model.embedding, 'weight'):
#         metric_dict = crystal_metric(model.embedding.weight.cpu().detach(), data_id, aux_info)
#     else:
#         metric_dict = crystal_metric(model.embedding.data.cpu(), data_id, aux_info)

#     with open(f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.json", "w") as f:
#         json.dump(metric_dict, f, indent=4)

# ## Exp3: Metric vs Train Fraction (fixed dataset size)
print(f"Experiment 3: Metric vs Train Fraction (fixed dataset size)")
train_ratio_list = []
if split == 1:
    train_ratio_list = np.arange(1, 5) / 10
if split == 2:
    train_ratio_list = np.arange(5,10) / 10

data_size = 1000
for i in tqdm(range(len(train_ratio_list))):
    train_ratio = train_ratio_list[i]
    param_dict = {
        'seed': seed,
        'data_id': data_id,
        'data_size': data_size,
        'train_ratio': train_ratio,
        'model_id': model_id,
        'device': torch.device('cuda' if torch.cuda.is_available() else 'cpu'),
        'embd_dim': embd_dim,
        'n_exp': n_exp,
        'lr': lr,
        'weight_decay':weight_decay
    }
    print(f"Training model with seed {seed}, data_id {data_id}, model_id {model_id}, n_exp {n_exp}, embd_dim {embd_dim}")
    ret_dic = train_single_model(param_dict)
    model = ret_dic['model']
    dataset = ret_dic['dataset']

    torch.save(model.state_dict(), f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.pt")
    with open(f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}_train_results.json", "w") as f:
        json.dump(ret_dic["results"], f, indent=4)
    torch.save(model.state_dict(), f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.pt")
    with open(f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}_train_results.json", "w") as f:
        json.dump(ret_dic["results"], f, indent=4)

    if data_id == "family_tree":
        aux_info["dict_level"] = dataset['dict_level']
    if data_id == "family_tree":
        aux_info["dict_level"] = dataset['dict_level']
    
    if hasattr(model.embedding, 'weight'):
        metric_dict = crystal_metric(model.embedding.weight.cpu().detach(), data_id, aux_info)
    else:
        metric_dict = crystal_metric(model.embedding.data.cpu(), data_id, aux_info)
    if hasattr(model.embedding, 'weight'):
        metric_dict = crystal_metric(model.embedding.weight.cpu().detach(), data_id, aux_info)
    else:
        metric_dict = crystal_metric(model.embedding.data.cpu(), data_id, aux_info)

    with open(f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}_metric.json", "w") as f:
        json.dump(metric_dict, f, indent=4)
    with open(f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}_metric.json", "w") as f:
        json.dump(metric_dict, f, indent=4)

## Exp4: Grokking plot: Run with different seeds
print(f"Experiment 4: Train with different seeds")

seed_list = []
if split == 3:
    seed_list = np.linspace(0, 1000, 20, dtype=int)[:4]
if split == 4:
    seed_list = np.linspace(0, 1000, 20, dtype=int)[4:7]
if split == 5:
    seed_list = np.linspace(0, 1000, 20, dtype=int)[7:10]
if split == 6:
    seed_list = np.linspace(0, 1000, 20, dtype=int)[10:13]
if split == 7:
    seed_list = np.linspace(0, 1000, 20, dtype=int)[13:17]
if split == 8:
    seed_list = np.linspace(0, 1000, 20, dtype=int)[17:]



for i in tqdm(range(len(seed_list))):
    seed = seed_list[i]
    data_size = 1000
    train_ratio = 0.8

    param_dict = {
        'seed': int(seed),
        'data_id': data_id,
        'data_size': data_size,
        'train_ratio': train_ratio,
        'model_id': model_id,
        'device': torch.device('cuda' if torch.cuda.is_available() else 'cpu'),
        'embd_dim': embd_dim,
        'n_exp': n_exp,
        'lr': lr,
        'weight_decay':weight_decay
    }
    print(f"Training model with seed {seed}, data_id {data_id}, model_id {model_id}, n_exp {n_exp}, embd_dim {embd_dim}")
    ret_dic = train_single_model(param_dict)
    model = ret_dic['model']
    dataset = ret_dic['dataset']
    torch.save(model.state_dict(), f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.pt")
    with open(f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}_train_results.json", "w") as f:
        json.dump(ret_dic["results"], f, indent=4)

    if data_id == "family_tree":
        aux_info["dict_level"] = dataset['dict_level']

    if hasattr(model.embedding, 'weight'):
        metric_dict = crystal_metric(model.embedding.weight.cpu().detach(), data_id, aux_info)
    else:
        metric_dict = crystal_metric(model.embedding.data.cpu(), data_id, aux_info)

    with open(f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.json", "w") as f:
        json.dump(metric_dict, f, indent=4)

# #Exp5: N Exponent value plot: Run with different n values, plot test accuracy vs. and explained variance vs.

# print(f"Experiment 5: Train with different exponent values")
# n_list = np.arange(1, 17, dtype=int)

# for i in tqdm(range(len(n_list))):
#     n_exp = n_list[i]
#     data_size = 1000
#     train_ratio = 0.8

#     param_dict = {
#         'seed': seed,
#         'data_id': data_id,
#         'data_size': data_size,
#         'train_ratio': train_ratio,
#         'model_id': model_id,
#         'device': torch.device('cuda' if torch.cuda.is_available() else 'cpu'),
#         'embd_dim': embd_dim,
#         'n_exp': n_exp
#     }
#     print(f"Training model with seed {seed}, data_id {data_id}, model_id {model_id}, n_exp {n_exp}, embd_dim {embd_dim}")
    
#     ret_dic = train_single_model(param_dict)
#     model = ret_dic['model']
#     dataset = ret_dic['dataset']
#     torch.save(model.state_dict(), f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.pt")
#     with open(f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}_train_results.json", "w") as f:
#         json.dump(ret_dic["results"], f, indent=4)

#     if data_id == "family_tree":
#         aux_info["dict_level"] = dataset['dict_level']

#     if hasattr(model.embedding, 'weight'):
#         metric_dict = crystal_metric(model.embedding.weight.cpu().detach(), data_id, aux_info)
#     else:
#         metric_dict = crystal_metric(model.embedding.data.cpu(), data_id, aux_info)

#     with open(f"{results_root}/{seed}_{data_id}_{model_id}_{data_size}_{train_ratio}_{n_exp}.json", "w") as f:
#         json.dump(metric_dict, f, indent=4)

