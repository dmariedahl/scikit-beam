from skbeam.core.accumulators.binned_statistic import (RadialBinnedStatistic,
                                                       BinnedStatistic1D)
from nose.tools import assert_raises
from numpy.testing import assert_array_equal, assert_array_almost_equal
import numpy as np
import scipy.stats

stats_list = [('mean', np.mean), ('median', np.median), ('count', len),
              ('sum', np.sum), ('std', np.std)]


class TestRadialBinnedStatistic(object):
    oscillation_rate = 10.0

    def setup(self):

        # Create test image - a sinc function.
        # Integrating in phi will produce sin(x)

        rowsize, colsize = (90, 102)

        rowarr = np.arange(rowsize)
        colarr = np.arange(colsize)
        rowgrid, colgrid = np.meshgrid(rowarr, colarr, indexing='ij')
        self.rgrid = np.sqrt(rowgrid**2 + colgrid**2)

        self.image = np.sinc(self.rgrid / self.oscillation_rate)

    def testRadialBinnedStatistic(self):

        mykwargs = [{'origin': (0, 0),
                     'range': (10, 90)},
                    {'origin': (0, 0)}]
        bins, shape = 100, self.image.shape
        mask_ones = np.ones_like(self.image)
        mask_random = np.random.randint(2, size=self.image.shape)
        for kwargs in mykwargs:
            for stat, stat_func in stats_list:

                if stat is 'sum':
                    # in this case we can compare our masked
                    # result to binned_statistic
                    mask = mask_random
                else:
                    mask = mask_ones

                radbinstat = RadialBinnedStatistic(shape, bins,
                                                   statistic=stat,
                                                   mask=mask,
                                                   **kwargs)
                radbinstat_f = RadialBinnedStatistic(shape, bins,
                                                     statistic=stat_func,
                                                     mask=mask,
                                                     **kwargs)
                binned = radbinstat(self.image)
                binned_f = radbinstat_f(self.image)

                assert_array_almost_equal(binned_f, binned)
                # can't check equality if we use normalization with
                # current testing strategy, but at least check code runs

                range = kwargs.get('range', None)
                ref, edges, _ = scipy.stats.binned_statistic(
                    x=self.rgrid.ravel(),
                    values=(self.image*mask).ravel(),
                    statistic=stat,
                    range=range,
                    bins=bins,
                )

                assert_array_equal(ref, binned)
                assert_array_equal(edges, radbinstat.bin_edges[0])
                assert_array_equal(edges, radbinstat_f.bin_edges[0])
        # test exception when BinnedStatistic is given array of incorrect shape
        with assert_raises(ValueError):
            radbinstat(self.image[:10, :10])

        # test exception when RadialBinnedStatistic is given 1D array
        with assert_raises(ValueError):
            RadialBinnedStatistic(self.image.shape, 10,
                                  mask=np.array([1, 2, 3, 4]))


def test_BinnedStatistics1D():
    x = np.linspace(0, 2*np.pi, 100)
    values = np.sin(x * 5)

    for stat, stat_f in stats_list:
        bs = BinnedStatistic1D(x, statistic=stat, bins=10)
        bs_f = BinnedStatistic1D(x, statistic=stat_f, bins=10)

        ref, edges, _ = scipy.stats.binned_statistic(x, values,
                                                     statistic=stat, bins=10)

        assert_array_equal(bs(values), ref)
        assert_array_almost_equal(bs_f(values), ref)
        assert_array_equal(edges, bs.bin_edges[0])
        assert_array_equal(edges, bs_f.bin_edges[0])
