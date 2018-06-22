import gzip
import os
import pickle
import time
import urllib
from os.path import abspath, dirname, join

import fire
import numpy as np
from sklearn import datasets
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE as SKLTSNE
from MulticoreTSNE import MulticoreTSNE
from sklearn.model_selection import train_test_split

from tsne.callbacks import ErrorLogger
from tsne.tsne import TSNE, TSNEEmbedding
import matplotlib.pyplot as plt

FILE_DIR = dirname(abspath(__file__))
DATA_DIR = join(FILE_DIR, 'data')

np.set_printoptions(precision=4, suppress=True)
np.random.seed(42)


def plot(x: np.ndarray, y: np.ndarray, show: bool = True, **kwargs) -> None:
    for yi in np.unique(y):
        mask = y == yi
        plt.plot(x[mask, 0], x[mask, 1], 'o', label=str(yi),
                 alpha=kwargs.get('alpha', 0.6), ms=kwargs.get('ms', 1))
    plt.legend()
    if show:
        plt.show()


def plot1d(x: np.ndarray, y: np.ndarray, show: bool = True, **kwargs) -> None:
    for yi in np.unique(y):
        mask = y == yi
        jitter = np.random.randn(mask.shape[0])
        plt.plot(x, jitter, 'o', label=str(yi),
                 alpha=kwargs.get('alpha', 0.6), ms=kwargs.get('ms', 1))
    plt.legend()
    if show:
        plt.show()


def get_mnist(n_samples=None):
    if not os.path.exists('data/mnist.pkl.gz'):
        urllib.request.urlretrieve(
            'http://deeplearning.net/data/mnist/mnist.pkl.gz', 'data/mnist.pkl.gz')

    with gzip.open('data/mnist.pkl.gz', 'rb') as f:
        train, val, test = pickle.load(f, encoding='latin1')
    _train = np.asarray(train[0], dtype=np.float64)
    _val = np.asarray(val[0], dtype=np.float64)
    _test = np.asarray(test[0], dtype=np.float64)
    x = np.vstack((_train, _val, _test))
    y = np.hstack((train[1], val[1], test[1]))

    if n_samples is not None:
        indices = np.random.choice(list(range(x.shape[0])), 20000, replace=False)
        x, y = x[indices], y[indices]

    return x, y


def get_mouse_60k():
    with open(join(DATA_DIR, 'sc-mouse-60k-1k.pkl'), 'rb') as f:
        x = pickle.load(f)
    x = x.astype(np.float32).toarray()
    import json
    with open(join(DATA_DIR, 'sc-mouse-60k-1k-y.txt'), 'rb') as f:
        y = np.array(json.load(f), dtype=int)

    return x, y


def tmp():
    from tsne.tsne import TSNE

    iris = datasets.load_iris()
    x = iris['data']
    y = iris['target']

    tsne = TSNE(
        perplexity=30, learning_rate=100, early_exaggeration=12,
        n_jobs=4, theta=0.5, initialization='pca', metric='euclidean',
        n_components=2, n_iter=750, early_exaggeration_iter=250, neighbors='exact',
        negative_gradient_method='bh', min_num_intervals=10, ints_in_interval=2,
        late_exaggeration_iter=0, late_exaggeration=4, callbacks=ErrorLogger(),
    )
    embedding = tsne.fit(x)
    plot(embedding, y)


def run():
    x, y = get_mouse_60k()

    angle = 0.5
    perplexity = 30
    ee = 12
    lr = 100
    threads = 4
    metric = 'euclidean'

    print(x.shape)

    start = time.time()
    tsne = TSNE(
        perplexity=perplexity, learning_rate=lr, early_exaggeration=ee,
        n_jobs=threads, theta=angle, initialization='random', metric=metric,
        n_components=2, n_iter=750, early_exaggeration_iter=250, neighbors='approx',
        negative_gradient_method='fft', min_num_intervals=10, ints_in_interval=2,
        late_exaggeration_iter=0, late_exaggeration=2., callbacks=ErrorLogger(),
    )
    # x = PCA(n_components=50).fit_transform(x)
    embedding = tsne.fit(x)
    print('-' * 80)
    print('tsne', time.time() - start)
    plt.title('tsne')
    plot(embedding, y)

    x = np.ascontiguousarray(x.astype(np.float64))
    from fitsne import FItSNE
    start = time.time()
    embedding = FItSNE(
        x, 2, perplexity=perplexity, stop_lying_iter=250, ann_not_vptree=True,
        early_exag_coeff=ee, nthreads=threads, theta=angle,
    )
    print('-' * 80)
    print('fft interp %.4f' % (time.time() - start))
    plt.title('fft interp')
    plot(embedding, y)
    plt.show()
    return

    init = PCA(n_components=2).fit_transform(x)
    start = time.time()
    embedding = MulticoreTSNE(
        early_exaggeration=ee, learning_rate=lr, perplexity=perplexity,
        n_jobs=threads, cheat_metric=False, angle=angle, init=init,
        metric=metric, verbose=True
    ).fit_transform(x)
    print('-' * 80)
    print('mctsne', time.time() - start)
    plt.title('mctsne')
    plot(embedding, y)
    plt.show()

    start = time.time()
    embedding = SKLTSNE(
        early_exaggeration=ee, learning_rate=lr, angle=angle,
        perplexity=perplexity, init='pca', metric=metric,
    ).fit_transform(x)
    print('-' * 80)
    print('sklearn', time.time() - start)
    plt.title('sklearn')
    plot(embedding, y)
    plt.show()


def transform(n_jobs=4, grad='bh', neighbors='approx'):
    x, y = get_mnist(20000)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.75, random_state=42)

    tsne = TSNE(
        perplexity=30, learning_rate=100, early_exaggeration=12,
        n_jobs=n_jobs, theta=0.5, initialization='pca', metric='euclidean',
        n_components=2, n_iter=750, early_exaggeration_iter=250, neighbors=neighbors,
        negative_gradient_method=grad, min_num_intervals=10, ints_in_interval=2,
        late_exaggeration_iter=0, late_exaggeration=4,
    )
    start = time.time()
    embedding = tsne.fit(x_train)
    print('tsne train', time.time() - start)

    plt.subplot(121)
    plot(embedding, y_train, show=False, ms=3)

    start = time.time()
    partial_embedding = embedding.get_partial_embedding_for(
        x_test, perplexity=20, initialization='random')
    partial_embedding.optimize(200, exaggeration=4, inplace=True, momentum=0.4)
    print('tsne trasnsform', time.time() - start)

    plt.subplot(122)
    plot(embedding, y_train, show=False, ms=3, alpha=0.25)
    plt.gca().set_color_cycle(None)
    plot(partial_embedding, y_test, show=False, ms=3, alpha=0.8)

    plt.show()


if __name__ == '__main__':
    fire.Fire()
