"""Check horizon-dependent exact attribution, including effects after batch ten."""
import numpy as np
from reset_effects import effects

for memory in (500, 1000, 2000, 1050):
    width = (memory+99)//100-1
    base = np.full(60,.5); actual=base.copy(); resets=np.array([3,12,40])
    for i,t in enumerate(resets):
        end=min(t+width,resets[i+1] if i+1<len(resets) else len(base))
        actual[t:end] += .1*(i+1)
    result=effects(actual,base,resets,100,memory)
    np.testing.assert_allclose(sum(result),100*(actual-base).sum())

base=np.full(40,.5); actual=base.copy(); actual[16]=.8
assert effects(actual,base,np.array([2]),100,2000)[0] > 29.9
try:
    effects(actual,base,np.array([2]),100,1000)
except AssertionError:
    pass
else:
    raise AssertionError('Out-of-horizon difference must fail exact accounting')
assert effects(actual,base,np.array([2]),100,None) == [0.0]
# A zero effect built from float batch accuracies must be exactly zero (no 1e-17 residue).
base=np.array([.5,.37,.29,.71,.5,.5]); actual=base.copy(); actual[1]+=.01; actual[2]-=.01
assert effects(actual,base,np.array([1]),100,500) == [0.0]
print('PASS: exact attribution for 500/1000/2000/non-multiple budgets; detects truncation; trained local window explicit; exact zero effects')
