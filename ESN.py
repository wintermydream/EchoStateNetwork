'''
————————————————
Link：https://blog.csdn.net/comli_cn/article/details/109394553
'''

import pickle
import numpy as np
import matplotlib.pyplot as plt


class ESN():
    def __init__(self, data, N=2000, rho=1, sparsity=3, T_train=2000, T_predict=1000, T_discard=200, eta=1e-4, seed=2050):
        self.data = data
        self.N = N  # reservoir size 库的大小
        self.rho = rho  # spectral radius 谱半径
        self.sparsity = sparsity  # average degree 平均度       sparsity：稀疏性
        self.T_train = T_train  # training steps
        self.T_predict = T_predict  # prediction steps
        self.T_discard = T_discard  # discard first T_discard steps  discard：丢弃
        self.eta = eta  # regularization constant 正则化常数
        self.seed = seed  # random seed

    def initialize(self):
        """
        对连接权矩阵W_IR和W_res进行初始化
        其中W_IR(N*1)是从输入到库的连接权矩阵，W_res(N*N)是从库到输出的连接权矩阵
        """
        if self.seed > 0:
            np.random.seed(self.seed)
        # 生成形状为N * 1的，元素为[-1, 1]之间的随机值的矩阵
        self.W_IR = np.random.rand(self.N, 1) * 2 - 1  # [-1, 1] uniform
        # 生成形状为N * N的，元素为[0, 1]之间的随机值的矩阵
        W_res = np.random.rand(self.N, self.N)
        # 将W_res中大于self.sparsity / self.N的元素置0
        W_res[W_res > self.sparsity / self.N] = 0\
        # np.linalg.eigvals(W_res)求出W_res的特征值，W_res矩阵除以自身模最大的特征值的模
        W_res /= np.max(np.abs(np.linalg.eigvals(W_res)))
        # 在乘以谱半径
        W_res *= self.rho  # set spectral radius = rho
        self.W_res = W_res

    def train(self):
        u = self.data[:, :self.T_train]  # traning data T_train = 2000
        assert u.shape == (1, self.T_train)
        r = np.zeros((self.N, self.T_train + 1))  # initialize reservoir state r(N*(T_train + 1))
        for t in range(self.T_train):
            # @是Python3.5之后加入的矩阵乘法运算符
            r[:, t+1] = np.tanh(self.W_res @ r[:, t] + self.W_IR @ u[:, t])
        # disgard first T_discard steps  r丢弃前T_discard步变成r_p
        self.r_p = r[:, self.T_discard+1:]  # length=T_train-T_discard
        v = self.data[:, self.T_discard+1:self.T_train+1]  # target
        self.W_RO = v @ self.r_p.T @ np.linalg.pinv(
            self.r_p @ self.r_p.T + self.eta * np.identity(self.N))
        train_error = np.sum((self.W_RO @ self.r_p - v) ** 2)
        print('Training error: %.4g' % train_error)

    def predict(self):
        u_pred = np.zeros((1, self.T_predict))  # u_pred是形状为(1, self.T_predict)的全零矩阵
        r_pred = np.zeros((self.N, self.T_predict))  # r_pred是形状为(N, self.T_predict)的全零矩阵
        r_pred[:, 0] = self.r_p[:, -1]  # warm start 热启动
        for step in range(self.T_predict - 1):
            u_pred[:, step] = self.W_RO @ r_pred[:, step]
            r_pred[:, step + 1] = np.tanh(self.W_res @
                                          r_pred[:, step] + self.W_IR @ u_pred[:, step])
        u_pred[:, -1] = self.W_RO @ r_pred[:, -1]
        self.pred = u_pred

    def plot_predict(self):
        ground_truth = self.data[:,
                                 self.T_train: self.T_train + self.T_predict]
        plt.figure(figsize=(12, 4))
        plt.plot(self.pred.T, 'r', label='predict', alpha=0.6)
        plt.plot(ground_truth.T, 'b', label='True', alpha=0.6)
        plt.show()

    def calc_error(self):
        ground_truth = self.data[:,
                                 self.T_train: self.T_train + self.T_predict]
        rmse_list = []
        for step in range(1, self.T_predict+1):
            error = np.sqrt(
                np.mean((self.pred[:, :step] - ground_truth[:, :step]) ** 2))
            rmse_list.append(error)
        return rmse_list


if __name__ == "__main__":
    # http://minds.jacobs-university.de/mantas/code
    data = np.load('mackey_glass_t17.npy')  # data.shape = (10000,)
    data = np.reshape(data, (1, data.shape[0]))  # data.shape = (1, 10000)
    print(data.shape)
    esn = ESN(data)
    esn.initialize()
    esn.train()
    esn.predict()
    esn.plot_predict()