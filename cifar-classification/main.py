"""Train CIFAR10 and CIFAR100 with PyTorch."""
from __future__ import print_function

import torch
import torch.nn as nn
import torch.optim as optim
import torch.backends.cudnn as cudnn
import torchvision
import torchvision.transforms as transforms

import os
import argparse
import time
from models import resnet, densenet, vgg
# from adabound import AdaBound
from optim import *
from torch.optim import Adam, SGD
from optimizations import AdaBelief, DAdam, RAdam, DEAdam, EAdam


def get_parser():
    parser = argparse.ArgumentParser(description='PyTorch CIFAR10 Training')
    parser.add_argument('--total_epoch', default=200, type=int, help='Total number of training epochs')
    parser.add_argument('--decay_epoch', default=150, type=int, help='Number of epochs to decay learning rate')
    parser.add_argument('--model', default='resnet', type=str, help='model',
                        choices=['resnet34', 'densenet121', 'vgg11', 'vgg16', 'resnet18'])
    # parser.add_argument('--optim', default='sgd', type=str, help='optimizer',
    #                     choices=['sgd', 'adam', 'adamw', 'adabelief', 'yogi', 'msvag', 'radam', 'fromage', 'adabound',
    #                              'dadam', 'deadam', 'eadam', 'nadam'])
    parser.add_argument('--optim', default='sgd', type=str, help='optimizer')
    parser.add_argument('--run', default=0, type=int, help='number of runs')
    parser.add_argument('--lr', default=0.1, type=float, help='learning rate')
    parser.add_argument('--lr-gamma', default=0.1, type=float, help='learning rate')
    parser.add_argument('--final_lr', default=0.1, type=float,
                        help='final learning rate of AdaBound')
    parser.add_argument('--gamma', default=1e-3, type=float,
                        help='convergence speed term of AdaBound')

    parser.add_argument('--eps', default=1e-8, type=float, help='eps for var adam')

    parser.add_argument('--momentum', default=0.9, type=float, help='momentum term')
    parser.add_argument('--beta1', default=0.9, type=float, help='Adam coefficients beta_1')
    parser.add_argument('--beta2', default=0.999, type=float, help='Adam coefficients beta_2')
    parser.add_argument('--resume', '-r', action='store_true', help='resume from checkpoint')
    parser.add_argument('--batchsize', type=int, default=128, help='batch size')
    parser.add_argument('--weight_decay', default=5e-4, type=float,
                        help='weight decay for optimizers')
    parser.add_argument('--reset', action='store_true',
                        help='whether reset optimizer at learning rate decay')
    parser.add_argument('--dataset', default='cifar10', type=str, help='dataset')
    return parser


def build_dataset(args):
    print('==> Preparing data..')
    transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])

    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])
    if args.dataset == 'cifar10':
        trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True,
                                                transform=transform_train)
        testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=True,
                                               transform=transform_test)
    elif args.dataset == 'cifar100':
        trainset = torchvision.datasets.CIFAR100(root='./data', train=True, download=True,
                                                transform=transform_train)
        testset = torchvision.datasets.CIFAR100(root='./data', train=False, download=True,
                                               transform=transform_test)

    train_loader = torch.utils.data.DataLoader(trainset, batch_size=args.batchsize, shuffle=True,
                                                   num_workers=2)
    test_loader = torch.utils.data.DataLoader(testset, batch_size=args.batchsize, shuffle=False, num_workers=2)

    # classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

    return train_loader, test_loader


def get_ckpt_name(model='resnet', optimizer='sgd', lr=0.1, final_lr=0.1, momentum=0.9,
                  beta1=0.9, beta2=0.999, gamma=1e-3, eps=1e-8, weight_decay=5e-4,
                  reset=False, run=0, weight_decouple=False, rectify=False, dataset='cifar10'):
    name = {
        'sgd': 'lr{}-momentum{}-wdecay{}-run{}-dataset{}'.format(lr, momentum, weight_decay, run, dataset),
        'adam': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run, dataset),
        'eadam': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run, dataset),
        'fromage': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run, dataset),
        'radam': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run, dataset),
        'adamw': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run, dataset),
        'adabelief': 'lr{}-betas{}-{}-eps{}-wdecay{}-run{}-dataset{}'.format(lr, beta1, beta2, eps, weight_decay, run, dataset),
        'adabound': 'lr{}-betas{}-{}-final_lr{}-gamma{}-wdecay{}-run{}-dataset{}'.format(lr, beta1, beta2, final_lr, gamma, weight_decay, run, dataset),
        'yogi': 'lr{}-betas{}-{}-eps{}-wdecay{}-run{}-dataset{}'.format(lr, beta1, beta2, eps, weight_decay, run, dataset),
        'msvag': 'lr{}-betas{}-{}-eps{}-wdecay{}-run{}-dataset{}'.format(lr, beta1, beta2, eps, weight_decay, run, dataset),
        'dadam': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run, dataset),
        'nadam': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run, dataset),
        'deadam': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run, dataset),
        'ada1': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run,dataset),
        'ada2': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run,dataset),
        'ada3': 'lr{}-betas{}-{}-wdecay{}-eps{}-run{}-dataset{}'.format(lr, beta1, beta2, weight_decay, eps, run,dataset),
    }[optimizer]
    return '{}-{}-{}-reset{}'.format(model, optimizer, name, str(reset))


def load_checkpoint(ckpt_name):
    print('==> Resuming from checkpoint..')
    path = os.path.join('checkpoint', ckpt_name)
    assert os.path.isdir('checkpoint'), 'Error: no checkpoint directory found!'
    assert os.path.exists(path), 'Error: checkpoint {} not found'.format(ckpt_name)
    return torch.load(path)


def build_model(args, device, ckpt=None):
    print('==> Building model..')
    net = {
        'resnet34': resnet.ResNet34,
        'densenet121': densenet.DenseNet121,
        'vgg11': vgg.vgg11,
        'vgg16': vgg.vgg16,
        'resnet18': resnet.ResNet18,
    }[args.model]()
    net = net.to(device)
    if device == 'cuda':
        net = torch.nn.DataParallel(net)
        cudnn.benchmark = True

    if ckpt:
        net.load_state_dict(ckpt['net'])

    return net


def create_optimizer(args, model_params):
    args.optim = args.optim.lower()
    if args.optim == 'sgd':
        return optim.SGD(model_params, args.lr, momentum=args.momentum,
                         weight_decay=args.weight_decay)
    elif args.optim == 'adam':
        return Adam(model_params, args.lr, betas=(args.beta1, args.beta2),
                    weight_decay=args.weight_decay, eps=args.eps)
    elif args.optim == 'ada1':
        return Ada1(model_params, args.lr, betas=(args.beta1, args.beta2),
                    weight_decay=args.weight_decay, eps=args.eps)
    elif args.optim == 'ada2':
        return Ada2(model_params, args.lr, betas=(args.beta1, args.beta2),
                    weight_decay=args.weight_decay, eps=args.eps)
    elif args.optim == 'Ada3':
        return Ada3(model_params, args.lr, betas=(args.beta1, args.beta2),
                    weight_decay=args.weight_decay, eps=args.eps)
    elif args.optim == 'eadam':
        return EAdam.EAdam(model_params, args.lr, betas=(args.beta1, args.beta2),
                    weight_decay=args.weight_decay, eps=args.eps)
    # elif args.optim == 'fromage':
    #     return Fromage(model_params, args.lr)
    elif args.optim == 'radam':
        return RAdam.RAdam(model_params, args.lr, betas=(args.beta1, args.beta2),
                     weight_decay=args.weight_decay, eps=args.eps)
    # elif args.optim == 'adamw':
    #     return AdamW(model_params, args.lr, betas=(args.beta1, args.beta2),
    #                  weight_decay=args.weight_decay, eps=args.eps)
    elif args.optim == 'adabelief':
        return AdaBelief.AdaBelief(model_params, args.lr, betas=(args.beta1, args.beta2),
                         weight_decay=args.weight_decay, eps=args.eps)
    # elif args.optim == 'yogi':
    #     return Yogi(model_params, args.lr, betas=(args.beta1, args.beta2),
    #                 weight_decay=args.weight_decay)
    # elif args.optim == 'msvag':
    #     return MSVAG(model_params, args.lr, betas=(args.beta1, args.beta2),
    #                  weight_decay=args.weight_decay)
    # elif args.optim == 'adabound':
    #     return AdaBound(model_params, args.lr, betas=(args.beta1, args.beta2),
    #                     final_lr=args.final_lr, gamma=args.gamma,
    #                     weight_decay=args.weight_decay)
    else:
        print('Optimizer not found')


def train(net, epoch, device, data_loader, optimizer, criterion, args):
    print('\nEpoch: %d' % epoch)
    net.train()
    train_loss = 0
    correct = 0
    total = 0
    for batch_idx, (inputs, targets) in enumerate(data_loader):
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = net(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        train_loss += loss.item()
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()

    accuracy = 100. * correct / total
    # print('train acc %.3f' % accuracy)

    return accuracy


def test(net, device, data_loader, criterion):
    net.eval()
    test_loss = 0
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_idx, (inputs, targets) in enumerate(data_loader):
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = net(inputs)
            loss = criterion(outputs, targets)

            test_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

    accuracy = 100. * correct / total
    # print(' test acc %.3f' % accuracy)

    return accuracy


def adjust_learning_rate(optimizer, epoch, step_size=150, gamma=0.1, reset=False):
    for param_group in optimizer.param_groups:
        if epoch % step_size == 0 and epoch > 0:
            param_group['lr'] *= gamma

    if epoch % step_size == 0 and epoch > 0 and reset:
        optimizer.reset()


def main():
    parser = get_parser()
    args = parser.parse_args()

    train_loader, test_loader = build_dataset(args)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    ckpt_name = get_ckpt_name(model=args.model, optimizer=args.optim, lr=args.lr,
                              final_lr=args.final_lr, momentum=args.momentum,
                              beta1=args.beta1, beta2=args.beta2, gamma=args.gamma,
                              eps=args.eps,
                              reset=args.reset, run=args.run,
                              weight_decay=args.weight_decay,
                              dataset=args.dataset,)
    print('ckpt_name:',ckpt_name)
    print(args)
    if args.resume:
        ckpt = load_checkpoint(ckpt_name)
        best_acc = ckpt['acc']
        start_epoch = ckpt['epoch']

        curve = os.path.join('curve', ckpt_name)
        curve = torch.load(curve)
        train_accuracies = curve['train_acc']
        test_accuracies = curve['test_acc']
    else:
        ckpt = None
        best_acc = 0
        start_epoch = -1
        train_accuracies = []
        test_accuracies = []

    net = build_model(args, device, ckpt=ckpt)
    criterion = nn.CrossEntropyLoss()
    optimizer = create_optimizer(args, net.parameters())
    # scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=args.decay_epoch, gamma=0.1,
    #                                      last_epoch=start_epoch)

    for epoch in range(start_epoch + 1, args.total_epoch):
        start = time.time()
        # scheduler.step()
        adjust_learning_rate(optimizer, epoch, step_size=args.decay_epoch, gamma=args.lr_gamma, reset=args.reset)
        train_acc = train(net, epoch, device, train_loader, optimizer, criterion, args)
        test_acc = test(net, device, test_loader, criterion)
        end = time.time()
        print('Epoch: {} | Train Acc: {}% | Test Acc: {}% | Time {}s'.format(epoch, train_acc, test_acc, end - start))
        # print('Time: {}'.format(end - start))

        # Save checkpoint.
        # if test_acc > best_acc:
        #     print('Saving..')
        #     state = {
        #         'net': net.state_dict(),
        #         'acc': test_acc,
        #         'epoch': epoch,
        #     }
        #     if not os.path.isdir('checkpoint'):
        #         os.mkdir('checkpoint')
        #     torch.save(state, os.path.join('checkpoint', ckpt_name))
        #     best_acc = test_acc

        train_accuracies.append(train_acc)
        test_accuracies.append(test_acc)
        if not os.path.isdir(os.path.join('curve',args.dataset,args.model)):
            os.makedirs(os.path.join('curve',args.dataset,args.model))
        torch.save({'train_acc': train_accuracies, 'test_acc': test_accuracies},
                   os.path.join('curve',args.dataset,args.model,ckpt_name))
        # if not os.path.isdir('curve'):
        #     os.mkdir('curve')
        # torch.save({'train_acc': train_accuracies, 'test_acc': test_accuracies},
        #            os.path.join('curve', ckpt_name))


if __name__ == '__main__':
    main()