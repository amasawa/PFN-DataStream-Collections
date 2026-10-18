Problems found:

- **B6 (experts added/pruned counts):** The diff does not count adds and prunes correctly. `learn` records `max(0, n1 - n0)` and `max(0, n0 - n1)`, which is the net change in the enabled-expert count across one `check_and_handle_drift` call. If one call both enables a drift expert and prunes a redundant one, the two cancel or partly cancel, so `added` and `pruned` are undercounted. The real counts need to come from the add and prune events, or from comparing the sets of enabled indices before and after.

- **B4 (ADAPT-Z `z.grad`):** The diff replaces `self.zp.grad[:x.shape[0]].mean(0)` with `self.zp.grad.mean(0)`, but the forward pass still uses the slice `self.zp[:x.shape[0]]`. If `zp` has more rows than the current batch, the extra rows get zero gradient and dilute the mean. The diff does not show `zp`'s size, so this is only safe if it always equals the batch size. Since the accumulation is now deliberate, the safe form is a mean over the rows actually used.

- **A5 (trigger counter identity):** The new asserts read `fsnet_.SamePadConv._counted`. That attribute exists only after `_count_triggers()` has run, and the diff does not show the call order. If it has not run, the assert raises `AttributeError` instead of giving a clear failure. The same applies in `OneNetCls`, where the diff does not show `fsnet_` being imported in that scope.

- **B2 (`torch.no_grad()` around drift handling):** The change is as decided. But `check_and_handle_drift` pre-trains the new drift expert, which needs gradients. If the official code does not re-enable grad inside that call, the pre-training no longer updates anything. It could also raise an error on backward. The diff gives no evidence that this was checked.

Beyond the findings, the only extra change that alters outputs is the new `added` and `pruned` fields in the `.npz`, which are asked for by B6. The computation is otherwise unchanged.
