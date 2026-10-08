"""Exact FIFO reset attribution, or the historical local window for trained learners."""
import numpy as np


def effects(accuracy, fifo_accuracy, resets, batch_size, memory=None):
    if memory is None:
        # Trained learners never converge to a FIFO context. Preserve the original descriptive
        # ten-batch statistic; do not call it a full effect or assert an exact decomposition.
        width = 10
    else:
        width = (int(memory)+int(batch_size)-1)//int(batch_size)-1
    values = []
    for i, t in enumerate(resets):
        end = min(t+width, resets[i+1] if i+1 < len(resets) else len(accuracy), len(accuracy))
        values.append(100*np.nansum(accuracy[t:end]-fifo_accuracy[t:end]))
    if memory is not None:
        np.testing.assert_allclose(sum(values), 100*np.nansum(accuracy-fifo_accuracy), atol=1e-8,
                                   err_msg='Reset effects do not sum to total FIFO difference')
    return values
