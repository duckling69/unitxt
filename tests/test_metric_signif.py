import numpy as np

import unittest
from src.unitxt.random_utils import *
from src.unitxt.metric_paired_significance import PairedDifferenceTest

np.set_printoptions(precision=10)


def rbernoulli_vec(pvec, rng):
    # binary variable with probability of 1 being given by a vector pvec (which determines the length)
    pvec = np.clip(pvec, 0.0, 1.0)
    return np.array([rng.choices(population=[0, 1], weights=[1-pp, pp], k=1)[0] for pp in pvec])

def rbeta(alpha, beta, rng, n):
    n = int(max(n, 1))
    return np.array([rng.betavariate(alpha=alpha, beta=beta) for _ in range(n)])

def rnorm(mu, sigma, rng, n):
    n = int(max(n, 1))
    return np.array([rng.normalvariate(mu=mu, sigma=sigma) for _ in range(n)])

def rmvnorm(mu, cmat, rng, n):
    # multivariate normal from univariate, since no existing function in Random
    # see https://rinterested.github.io/statistics/multivariate_normal_draws.html
    assert len(mu) == cmat.shape[0]
    d = cmat.shape[0]
    # generate n * d independent standard normal dras
    Z = np.vstack([rnorm(mu=0, sigma=1, rng=rng, n=n) for _ in range(d)])
    # cholesky decomposition (LL^T = cmat)
    L = np.linalg.cholesky(cmat)
    # add mu row-wise
    return mu + np.transpose(np.matmul(L, Z))


class TestMetricSignifDifference(unittest.TestCase):
    @classmethod
    def setUpClass(cls, nmodels=4, nobs=50):
        cls.nmodels = max(2, int(nmodels))
        cls.nobs = max(3, int(nobs))
        cls.rseed = "4"

    def gen_continuous_data(self, same_distr=True):
        # assume we have a dataset with nobs observations
        # generate a matrix of size (nmodels, nobs) representing the results of nmodels results on the same nobs observations
        # same_distr means they follow the same distribution
        # covariance matrix to generate observations that are paired.  Each have correlation 0.7 and variance 1
        cmat = np.empty((self.nmodels, self.nmodels))
        cmat.fill(0.7)
        np.fill_diagonal(cmat, 1)

        rng = get_sub_default_random_generator(sub_seed=self.rseed)
        # different mean for every observation, and are correlated due to pairing
        mu = rnorm(mu=5, sigma=1, rng=rng, n=self.nobs)

        # multivariate normal
        model_measurement = np.transpose(np.vstack([rmvnorm(mu=np.array([mm]*self.nmodels), cmat=cmat, n=1, rng=rng)[0,:] for mm in mu]))

        if not same_distr:
            # make the last two sample have a higher mean
            model_measurement[-1, :] = model_measurement[-1, :] + 2
            if self.nmodels > 2:
                model_measurement[-2, :] = model_measurement[-2, :] + 1

        # add some skew
        model_measurement = np.square(model_measurement)
        return tuple([xx for xx in model_measurement])

    
    def gen_binary_data(self, same_distr=True, nmodels=None):
        # generate only binary data
        nmodels = self.nmodels if nmodels is None else max(2, int(nmodels))
        rng = get_sub_default_random_generator(sub_seed=self.rseed)
        if same_distr:
            # generate random probabilities for each observation and then binary
            # do this so observation pairs are more correlated than otherwise if used the same p for all
            p = rbeta(alpha=2, beta=5, rng=rng, n=self.nobs)
            return [rbernoulli_vec(pvec=p, rng=rng) for _ in range(nmodels)]
        else:
            p = np.vstack([rbeta(alpha=2, beta=5, rng=rng, n=self.nobs) for _ in range(nmodels - 1)] + [rbeta(alpha=5, beta=2, rng=rng, n=self.nobs)])
            return [rbernoulli_vec(pvec=pp, rng=rng) for pp in p]

    
    def _test_signif(self, expected_pvalues_list: list, expected_effect_sizes, same_distr=True, continuous=True):

        model_res = self.gen_continuous_data(same_distr) if continuous else self.gen_binary_data(same_distr=same_distr)
        tester = PairedDifferenceTest(nmodels=self.nmodels)

        # use default paired t-test
        res_twosided = tester.signif_pair_diff(samples_list=model_res, alternative='two-sided')
        for observed, expected in zip(res_twosided.pvalues, expected_pvalues_list[0]):
            self.assertAlmostEqual(first=observed, second=expected)
        # the effect sizes are the same in the one and two-sided case, and only the non-permutation case
        for observed, expected in zip(res_twosided.effect_sizes, expected_effect_sizes):
            self.assertAlmostEqual(first=observed, second=expected)

        res_onesided = tester.signif_pair_diff(samples_list=model_res, alternative='less')
        for observed, expected in zip(res_onesided.pvalues, expected_pvalues_list[1]):
            self.assertAlmostEqual(first=observed, second=expected)

        # permutation results should be very similar to t-test but not identical, and should vary a bit each run due to permutation randomness
        res_twosided = tester.signif_pair_diff(samples_list=model_res, alternative='two-sided', permute=True, random_state=int(self.rseed))
        for observed, expected in zip(res_twosided.pvalues, expected_pvalues_list[2]):
            self.assertAlmostEqual(first=observed, second=expected)

        res_onesided = tester.signif_pair_diff(samples_list=model_res, alternative='less', permute=True, random_state=int(self.rseed))
        for observed, expected in zip(res_onesided.pvalues, expected_pvalues_list[3]):
            self.assertAlmostEqual(first=observed, second=expected)

    def test_signif_same_distr_continuous(self):
        self._test_signif(expected_pvalues_list=[np.array([0.9895803029, 0.9961379384, 0.9961379384, 0.9961379384, 0.9961379384, 0.9961379384]),
                                                 np.array([0.9561053206, 0.9561053206, 0.9561053206, 0.9516411082, 0.9516411082, 0.9516411082]),
                                                 np.array([0.9888580218, 0.995026807, 0.995026807, 0.995026807, 0.995026807, 0.995026807]),
                                                 np.array([0.9550338964, 0.9550338964, 0.9550338964, 0.9524978682, 0.9524978682, 0.9524978682])],
                          expected_effect_sizes=np.array([ 0.2363223971, 0.1607737558, 0.1429445904, -0.0605006595, -0.0993183451]))

    def test_signif_diff_distr_continuous(self):
        # here the last one or two samples (models) have higher mean, so the 'less' alternative should be appropriate
        self._test_signif(expected_pvalues_list=[np.array([5.3264971085e-01, 5.2011437584e-09, 3.7798272112e-19, 1.1837543364e-10, 1.1248121326e-19, 1.8367825057e-13]),
                                                 np.array([7.3367514457e-01, 2.6005718809e-09, 1.8899136056e-19, 5.9187716820e-11, 5.6240606632e-20, 9.1839125286e-14]),
                                                 np.array([0.5274, 0.0011994002, 0.0011994002, 0.0011994002, 0.0011994002, 0.0011994002]),
                                                 np.array([7.3640000e-01, 5.9985002e-04, 5.9985002e-04, 5.9985002e-04, 5.9985002e-04, 5.9985002e-04])],
                          expected_effect_sizes=np.array([0.2363223971, -2.7312549788, -5.609456644, -3.1778374839, -5.8056079522, -3.9294197371]),
                          same_distr=False)

    def test_signif_same_distr_binary(self):
        # use ordinary t-test or permutation on binary values; have more than 2 samples so don't use McNemar
        self._test_signif(expected_pvalues_list=[np.array([0.9596776367, 0.9591282452, 0.9591282452, 0.9591282452, 0.8251525806, 0.9596776367]),
                                                 np.array([0.7400657497, 0.7400657497, 0.7400657497, 0.7400657497, 0.5546027515, 0.7400657497]),
                                                 np.array([0.99999804, 0.9934324192, 0.9934324192, 0.9934324192, 0.948378191, 1.]),
                                                 np.array([0.8513710128, 0.8513710128, 0.8513710128, 0.8513710128, 0.7276678217, 0.8513710128])],
                          expected_effect_sizes=np.array([0.0961866125, -0.1995634093, -0.2723195343, -0.2574435301, -0.435721617, -0.0903444948]),
                          same_distr=True, continuous=False)

    def test_signif_diff_distr_binary(self):
        # use ordinary t-test or permutation on binary values; have more than 2 samples so don't use McNemar
        # here the last one or two samples (models) have higher mean, so the 'less' alternative should be appropriate
        self._test_signif(expected_pvalues_list=[np.array([0.965426988, 0.965426988, 0.1034291099, 1., 0.0337032272, 0.0121357763]),
                                                 np.array([0.875, 0.875, 0.0527729664, 0.875, 0.0169671602, 0.0060833233]),
                                                 np.array([0.9968750569, 0.9968750569, 0.1605192154, 1., 0.0576239336, 0.0202273841]),
                                                 np.array([0.9305227804, 0.9305227804, 0.0828912316, 0.9305227804, 0.0291539477, 0.0101567481])],
                          expected_effect_sizes=np.array([0.1409103279, 0.1590304389, -0.8578412784, 0., -1.0621120379, -1.225742824]),
                          same_distr=False, continuous=False)

    def test_signif_mcnemar_binary(self):

        # use Mcnemar's test, not t-test, only on two model samples
        tester = PairedDifferenceTest(nmodels=2)

        # random generation of paired binary data
        binary_same = self.gen_binary_data(same_distr=True, nmodels=tester.nmodels)
        res = tester.signif_pair_diff(samples_list=binary_same)
        self.assertAlmostEqual(first=res.pvalues[0], second=1.0)
        self.assertAlmostEqual(first=res.effect_sizes[0], second=0.033333333333333326)

        binary_diff = self.gen_binary_data(same_distr=False, nmodels=tester.nmodels)
        res = tester.signif_pair_diff(samples_list=binary_diff)
        self.assertAlmostEqual(first=res.pvalues[0], second= 3.6729034036397934e-08)
        self.assertAlmostEqual(first=res.effect_sizes[0], second=0.44285714285714284)

        # handle some corner cases where the samples do not result in a 2x2 contingency table automatically
        # contingency table is 1x1
        samples_list = [np.ones(shape=100), np.ones(shape=100)]
        res_1x1 = tester.signif_pair_diff(samples_list=samples_list)
        # p-value is 1 meaning there is no difference since both have same values exactly, with no variability
        self.assertAlmostEqual(first=res_1x1.pvalues[0], second=1.0)
        self.assertAlmostEqual(first=res_1x1.effect_sizes[0], second=0.0)

        # also 1x1 but different values 0 and 1
        samples_list = [np.ones(shape=100), np.zeros(shape=100)]
        res_1x1 = tester.signif_pair_diff(samples_list=samples_list)
        # p-value is essentially 0 because there is a complete difference and no variability
        self.assertAlmostEqual(first=res_1x1.pvalues[0], second=1.5777218104420236e-30)
        self.assertAlmostEqual(first=res_1x1.effect_sizes[0], second=0.49502487562189057)

        # contingency table is 1x2
        samples_list = [np.ones(shape=100), np.repeat(a=[0, 1], repeats=[47, 53])]
        res_1x2 = tester.signif_pair_diff(samples_list=samples_list)
        self.assertAlmostEqual(first=res_1x2.pvalues[0], second=1.4210854715202004e-14)
        self.assertAlmostEqual(first=res_1x2.effect_sizes[0], second=0.4894736842105263)

        # contingency table is 2x1
        samples_list = [np.repeat(a=[0, 1], repeats=[49, 51]), np.zeros(shape=100)]
        res_2x1 = tester.signif_pair_diff(samples_list=samples_list)
        self.assertAlmostEqual(first=res_2x1.pvalues[0], second=8.881784197001252e-16)
        self.assertAlmostEqual(first=res_2x1.effect_sizes[0], second= 0.49029126213592233)

        # contingency table is 2x2 but with one combination missing, which needs a continuity correction
        samples_list = [np.repeat(a=[0,1], repeats=[50,50]), np.repeat(a=[0,1], repeats=[40,60])]
        res_2x2 = tester.signif_pair_diff(samples_list=samples_list)
        self.assertAlmostEqual(first=res_2x2.pvalues[0], second=0.001953125)
        self.assertAlmostEqual(first=res_2x2.effect_sizes[0], second=0.45238095238095233)

