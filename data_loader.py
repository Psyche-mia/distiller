from pathlib import Path
import torch
import torchvision
import torchvision.transforms as transforms
import numpy as np
from torch.utils.data import Dataset

NUM_WORKERS = 4

# Use a different testset for cifar 10
USE_CIFAR_10_1 = False

from torch.utils.data import Dataset, DataLoader
from uda_dl import CIFAR10Policy

class CfDataset(Dataset):
    """Face Landmarks dataset."""

    def __init__(self, dataset, uda=False, transform=None, normalize=None):
        """
        Args:
            csv_file (string): Path to the csv file with annotations.
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.dataset = dataset
        self.uda = uda
     
        self.end_tf = transforms.Compose([
            transforms.ToTensor(),
            normalize,
        ])

        self.aug_tf = transforms.Compose([
            CIFAR10Policy(),
            transforms.ToTensor(),
            normalize,
        ])


    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        x, target = self.dataset[idx]

        if self.uda == True:
            normal_x = self.end_tf(x)
            aug_x = self.aug_tf(x)

            return normal_x, aug_x, target

        return self.end_tf(x), target



class TensorImgSet(Dataset):
    """TensorDataset with support of transforms.
    """

    def __init__(self, tensors, transform=None):
        self.imgs = tensors[0]
        self.targets = tensors[1]
        self.tensors = tensors
        self.transform = transform
        self.len = len(self.imgs)

    def __getitem__(self, index):
        x = self.imgs[index]
        if self.transform:
            x = self.transform(x)
        y = self.targets[index]
        return x, y

    def __len__(self):
        return self.len


def load_cifar_10_1():
    # @article{recht2018cifar10.1,
    #  author = {Benjamin Recht and Rebecca Roelofs and Ludwig Schmidt
    #  and Vaishaal Shankar},
    #  title = {Do CIFAR-10 Classifiers Generalize to CIFAR-10?},
    #  year = {2018},
    #  note = {\url{https://arxiv.org/abs/1806.00451}},
    # }
    # Original Repo: https://github.com/modestyachts/CIFAR-10.1
    data_path = Path(__file__).parent.joinpath("cifar10_1")
    label_filename = data_path.joinpath("v6_labels.npy").resolve()
    imagedata_filename = data_path.joinpath("v6_data.npy").resolve()
    print(f"Loading labels from file {label_filename}")
    labels = np.load(label_filename)
    print(f"Loading image data from file {imagedata_filename}")
    imagedata = np.load(imagedata_filename)
    return imagedata, torch.Tensor(labels).long()


def get_cifar(num_classes=100, dataset_dir="./data", batch_size=128):

    if num_classes == 10:
        # CIFAR10
        print("=> loading CIFAR10...")
        dataset = torchvision.datasets.CIFAR10
        normalize = transforms.Normalize(
            (0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
    else:
        # CIFAR100
        print("=> loading CIFAR100...")
        dataset = torchvision.datasets.CIFAR100
        normalize = transforms.Normalize(
            mean=[0.507, 0.487, 0.441], std=[0.267, 0.256, 0.276])

    train_transform = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        normalize,
    ])

    

    test_transform = transforms.Compose([
        transforms.ToTensor(),
        normalize,
    ])

    trainset = dataset(root=dataset_dir, train=True,
                       download=True,
                       transform=train_transform)

    # Use the normal cifar 10 testset or a new one to test true generalization
    if USE_CIFAR_10_1 and num_classes == 10:
        imagedata, labels = load_cifar_10_1()
        testset = TensorImgSet((imagedata, labels), transform=test_transform)
    else:
        testset = dataset(root=dataset_dir, train=False,
                          download=True,
                          transform=test_transform)
    
    
    train_loader = torch.utils.data.DataLoader(trainset,
                                               batch_size=batch_size,
                                               num_workers=NUM_WORKERS,
                                               pin_memory=True, shuffle=True)
    test_loader = torch.utils.data.DataLoader(testset,
                                              batch_size=batch_size,
                                              num_workers=NUM_WORKERS,
                                              pin_memory=True, shuffle=False)
    return train_loader, test_loader


def get_cifar_uda(num_classes=100, dataset_dir="./data", batch_size=128):

    if num_classes == 10:
        # CIFAR10
        print("=> loading CIFAR10...")
        dataset = torchvision.datasets.CIFAR10
        normalize = transforms.Normalize(
            (0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
    else:
        # CIFAR100
        print("=> loading CIFAR100...")
        dataset = torchvision.datasets.CIFAR100
        normalize = transforms.Normalize(
            mean=[0.507, 0.487, 0.441], std=[0.267, 0.256, 0.276])

    train_transform = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
    ])

    test_transform = transforms.Compose([
        transforms.ToTensor(),
        normalize,
    ])

    trainset = dataset(root=dataset_dir, train=True,
                       download=True,
                       transform=train_transform)

    # Use the normal cifar 10 testset or a new one to test true generalization
    if USE_CIFAR_10_1 and num_classes == 10:
        imagedata, labels = load_cifar_10_1()
        testset = TensorImgSet((imagedata, labels), transform=test_transform)
    else:
        testset = dataset(root=dataset_dir, train=False,
                          download=True,
                          transform=test_transform)
    
    uda_trainset = CfDataset(dataset=trainset, uda=True, normalize=normalize)
    train_loader = torch.utils.data.DataLoader(uda_trainset,
                                               batch_size=batch_size,
                                               num_workers=NUM_WORKERS,
                                               pin_memory=True, shuffle=True)
    test_loader = torch.utils.data.DataLoader(testset,
                                              batch_size=batch_size,
                                              num_workers=NUM_WORKERS,
                                              pin_memory=True, shuffle=False)
    return train_loader, test_loader
