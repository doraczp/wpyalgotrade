import numpy as np
import statsmodels.api as sm
import scipy.stats as scs
import scipy.optimize as sco

'''covmat = np.array([[  1.73019764e-04,   1.96415734e-04,  -6.23099140e-07,   3.22378426e-05,
    2.26049595e-05],
 [  1.96415734e-04,   2.59079720e-04,  -9.05826908e-07,   3.38044200e-05,
    2.74546780e-05],
 [ -6.23099140e-07,  -9.05826908e-07,   1.31737200e-06,  -3.08375625e-07,
   -1.74458446e-06],
 [  3.22378426e-05,   3.38044200e-05,  -3.08375625e-07 ,  1.18344687e-04,
    1.24065482e-05],
 [  2.26049595e-05,   2.74546780e-05,  -1.74458446e-06 ,  1.24065482e-05,
    2.88583915e-04]])'''

covmat = np.array([[  1.75810173e-04,   1.99068832e-04,  -5.00780329e-07,  3.00757349e-05,
    2.43291615e-05],
 [  1.99068832e-04,   2.62421961e-04,  -5.98038308e-07,   3.28722268e-05,
    3.02739106e-05],
 [ -5.00780329e-07,  -5.98038308e-07,   1.32625594e-06,   7.36010131e-07,
   -8.93382713e-07],
 [  3.00757349e-05,   3.28722268e-05,   7.36010131e-07,   1.46650063e-04,
    3.49056569e-07],
 [  2.43291615e-05,   3.02739106e-05,  -8.93382713e-07,   3.49056569e-07,
    3.50815413e-04]])

budget = [1.0/5.0 for i in range(5)]

def minRisk(weight):
    w = np.array(weight)
    sigma = np.dot(w.T, np.dot(covmat, w))
    rci = np.dot(covmat, w) / sigma
    return np.sum((w * rci - np.array(budget) * sigma) ** 2)

cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
# bnds = tuple((0, 1) for x in range(5))
org = np.array([1.0 / 5 for i in range(5)])
opts = sco.minimize(minRisk, org, constraints=cons)

print opts
