import numpy

from chainer import cuda
from chainer import function
from chainer.utils import type_check


class Accuracy(function.Function):

    def __init__(self, ignore_label=None):
        self.ignore_label = ignore_label

    def check_type_forward(self, in_types):
        type_check.expect(in_types.size() == 2)
        x_type, t_type = in_types

        type_check.expect(
            x_type.dtype == numpy.float32,
            x_type.ndim >= 2,
            t_type.dtype == numpy.int32,
            t_type.ndim == 1,
            t_type.shape[0] == x_type.shape[0],
        )
        for i in range(2, x_type.ndim.eval()):
            type_check.expect(x_type.shape[i] == 1)

    def forward(self, inputs):
        xp = cuda.get_array_module(*inputs)
        y, t = inputs
        y = y.reshape(len(y), -1)  # flatten

        if self.ignore_label is not None:
            mask = (t == self.ignore_label)
            ignore_cnt = mask.sum()

            # will always be true when the true label is ignore_label
            # TODO(henry0312)
            #   If cupy.where returns indexes, we could make the code better.
            #   Also, we would need Advanced Indexing.
            pred = xp.where(mask, self.ignore_label, y.argmax(axis=1))
            count = (pred == t).sum() - ignore_cnt
            total = len(t) - ignore_cnt

            if total == 0:
                return xp.asarray(0.0, dtype='f'),
            else:
                return xp.asarray(float(count) / total, dtype='f'),
        else:
            pred = y.argmax(axis=1)
            return xp.asarray((pred == t).mean(dtype='f')),


def accuracy(y, t, ignore_label=None):
    """Computes muticlass classification accuracy of the minibatch.

    Args:
        y (Variable): Variable holding a matrix whose (i, j)-th element
            indicates the score of the class j at the i-th example.
        t (Variable): Variable holding an int32 vector of ground truth labels.
        ignore_label (int or None): Skip calculating accuracy
            if the ture label is ``ignore_label``.

    Returns:
        Variable: A variable holding a scalar array of the accuracy.

    .. note:: This function is non-differentiable.

    """
    return Accuracy(ignore_label=ignore_label)(y, t)