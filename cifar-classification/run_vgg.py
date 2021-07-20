run = 0
cuda_device = 1
model = 'vgg16'
import os
for i in range(0,3):
    # # ada1
    # cmd = 'CUDA_VISIBLE_DEVICES=' + str(cuda_device) + ' python -u main.py --dataset cifar100 --model ' + model + ' --optim ada1 --lr 1e-3 --beta1 0.9 --beta2 0.999 --eps 1e-8 --run ' + str(i) + ' > ./logs/cifar100/vgg16/ada1_run' + str(i) + '.log 2>&1'
    # os.system(cmd)

    # cmd = 'CUDA_VISIBLE_DEVICES=' + str(cuda_device) + ' python -u main.py --dataset cifar100 --model ' + model + ' --optim ada2 --lr 1e-3 --beta1 0.9 --beta2 0.999 --eps 1e-8 --run ' + str(i) + ' > ./logs/cifar100/vgg16/ada2_run' + str(i) + '.log 2>&1'
    # os.system(cmd)
    # # ada3
    # cmd = 'CUDA_VISIBLE_DEVICES=' + str(cuda_device) + ' python -u main.py --dataset cifar100 --model ' + model + ' --optim ada3 --lr 1e-3 --beta1 0.9 --beta2 0.999 --eps 1e-8 --run ' + str(i) + ' > ./logs/cifar100/ada3_run' + str(i) + '.log 2>&1'
    # os.system(cmd)
    # # ada4
    # cmd = 'CUDA_VISIBLE_DEVICES=' + str(cuda_device) + ' python -u main.py --dataset cifar100 --model ' + model + ' --optim ada4 --lr 1e-3 --beta1 0.9 --beta2 0.999 --eps 1e-8 --run ' + str(i) + ' > ./logs/cifar100/ada4_run' + str(i) + '.log 2>&1'
    # os.system(cmd)
    # adam
    # cmd = 'CUDA_VISIBLE_DEVICES=' + str(cuda_device) + ' python -u main.py --dataset cifar100 --model ' + model + ' --optim adam --lr 1e-4 --beta1 0.9 --beta2 0.999 --eps 1e-8 --run ' + str(i) + ' > ./logs/cifar100/vgg16/adam_run' + str(i) + '.log 2>&1'
    # os.system(cmd)
    # # adabelief
    # cmd = 'CUDA_VISIBLE_DEVICES=' + str(cuda_device) + ' python -u main.py --dataset cifar100 --model ' + model + ' --optim adabelief --lr 1e-3 --beta1 0.9 --beta2 0.999 --eps 1e-8 --run ' + str(i) + ' > ./logs/cifar100/vgg16/adabelief_run' + str(i) + '.log 2>&1'
    # os.system(cmd)
    # sgd
    cmd = 'CUDA_VISIBLE_DEVICES=' + str(cuda_device) + ' python -u main.py --dataset cifar100 --model ' + model + ' --optim sgd --lr 0.01 --momentum 0.9 --eps 1e-8 --run ' + str(i) + ' > ./logs/cifar100/vgg16/sgd_run001' + str(i) + '.log 2>&1'
    os.system(cmd)