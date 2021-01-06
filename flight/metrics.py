#!/usr/bin/env python
###############################################################################
# metrics.py - File containing additonal distance metrics for use with UMAP
###############################################################################
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the                #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program. If not, see <http://www.gnu.org/licenses/>.        #
#                                                                             #
###############################################################################
__author__ = "Rhys Newell"
__copyright__ = "Copyright 2020"
__credits__ = ["Rhys Newell"]
__license__ = "GPL3"
__maintainer__ = "Rhys Newell"
__email__ = "rhys.newell near hdr.qut.edu.au"
__status__ = "Development"

###############################################################################
# System imports
import sys
import argparse
import logging
import os
import shutil
import datetime

# Function imports
import numba
import numpy as np
import math

###############################################################################                                                                                                                      [44/1010]
################################ - Functions - ################################

@numba.njit()
def tnf(a, b, n_samples):
    cov_mat = np.cov(a[n_samples:], b[n_samples:])
    cov = cov_mat[0, 1]
    a_sd = np.sqrt(cov_mat[0,0])
    b_sd = np.sqrt(cov_mat[1,1])
    rho = cov / (a_sd * b_sd)
    rho += 1
    rho = 2 - rho
    return rho
    # L2 norm is equivalent to euclidean distance
    # euc_dist = np.linalg.norm(a[n_samples:] - b[n_samples:])

    # return euc_dist


@numba.njit()
def snv_corr(a, b, n_samples):
    snv1 = a[n_samples:n_samples * 2]
    snv2 = b[n_samples:n_samples * 2]
    if len(set(snv1)) == 1 and len(set(snv2)) == 1:
        return 1
    else:
        covariance_mat = np.cov(snv1, snv2, rowvar=True)
        covariance = covariance_mat[0, 1]
        var_a = covariance_mat[0, 0]
        var_b = covariance_mat[1, 1]
        vlr = -2 * covariance + var_a + var_b
        rho = 1 - vlr / (var_a + var_b)
        rho += 1
        rho = 2 - rho
        return rho

@numba.njit()
def sv_corr(a, b, n_samples):
    sv1 = a[n_samples*2:n_samples*3]
    sv2 = b[n_samples*2:n_samples*3]
    # check if all values where just 0 originally
    if len(set(sv1)) == 1 and len(set(sv2)) == 1:
        return 1
    else:
        covariance_mat = np.cov(sv1, sv2, rowvar=True)
        covariance = covariance_mat[0, 1]
        var_a = covariance_mat[0, 0]
        var_b = covariance_mat[1, 1]
        vlr = -2 * covariance + var_a + var_b
        rho = 1 - vlr / (var_a + var_b)
        rho += 1
        rho = 2 - rho
        return rho

@numba.njit()
def euclidean(a, b, n_samples):
    # Since these compositonal arrays are CLR transformed
    # This is the equivalent to the aitchinson distance but we calculat the l2 norm
    euc_dist = np.linalg.norm(a[:n_samples] - b[:n_samples])

    return euc_dist

@numba.njit()
def snv_euclidean(a, b, n_samples):
    # Since these compositonal arrays are CLR transformed
    # This is the equivalent to the aitchinson distance but we calculat the l2 norm
    # check if all values where just 0 originally
    snv1 = a[n_samples:n_samples * 2]
    snv2 = b[n_samples:n_samples * 2]
    if len(set(snv1)) == 1 and len(set(snv2)) == 1:
        return 1
    else:
        euc_dist = np.linalg.norm(snv1 - snv2)
        return euc_dist


@numba.njit()
def sv_euclidean(a, b, n_samples):
    # Since these compositonal arrays are CLR transformed
    # This is the equivalent to the aitchinson distance but we calculat the l2 norm
    sv1 = a[n_samples * 2:n_samples * 3]
    sv2 = b[n_samples * 2:n_samples * 3]
    if len(set(sv1)) == 1 and len(set(sv2)) == 1:
        return 1
    else:
        euc_dist = np.linalg.norm(sv1 - sv2)
        return euc_dist

@numba.njit()
def rho(a, b, n_samples):
    # This is a transformed, inversed version of rho. Normal those -1 <= rho <= 1
    # transformed rho: 0 <= rho <= 2, where 0 is perfect concordance
    covariance_mat = np.cov(a[:n_samples], b[:n_samples], rowvar=True)
    covariance = covariance_mat[0, 1]
    var_a = covariance_mat[0, 0]
    var_b = covariance_mat[1, 1]
    vlr = -2 * covariance + var_a + var_b
    rho = 1 - vlr / (var_a + var_b)
    rho += 1
    rho = 2 - rho
    # Since these compositonal arrays are CLR transformed
    # This is the equivalent to the aitchinson distance but we calculat the l2 norm
    euc_dist = np.linalg.norm(a[:n_samples] - b[:n_samples])

    dist = min(euc_dist, rho)
    
    return dist


@numba.njit()
def rho_tnf(a, b, n_samples):
    # This is a transformed, inversed version of rho. Normal those -1 <= rho <= 1
    # transformed rho: 0 <= rho <= 2, where 0 is perfect concordance
    w = n_samples / (n_samples + 1) # weighting by number of samples same as in metabat2
    l = min(a[0], b[0]) / (max(a[0], b[0]) + 1)
    
    covariance_mat = np.cov(a[1:], b[1:], rowvar=True)
    covariance = covariance_mat[0, 1]
    var_a = covariance_mat[0, 0]
    var_b = covariance_mat[1, 1]
    vlr = -2 * covariance + var_a + var_b
    rho = 1 - vlr / (var_a + var_b)
    rho += 1
    rho = (2 - rho)
    
    return rho


@numba.njit()
def concordance(a, b, n_samples):
    # This is a transformed, inversed version of rho. Normal those -1 <= rho <= 1
    # transformed rho: 0 <= rho <= 2, where 0 is perfect concordance
    covariance_mat = np.cov(a[:n_samples], b[:n_samples], rowvar=True)
    covariance = covariance_mat[0, 1]
    var_a = covariance_mat[0, 0]
    var_b = covariance_mat[1, 1]
    vlr = -2 * covariance + var_a + var_b
    rho = 1 - vlr / (var_a + var_b)

    return rho

@numba.njit()
def phi(a, b, n_samples):
    covariance_mat = np.cov(a, b, rowvar=True)
    covariance = covariance_mat[0, 1]
    var_a = covariance_mat[0, 0]
    var_b = covariance_mat[1, 1]
    phi = 1 + (var_a / var_b) - 2 * np.sqrt(var_a / var_b) * covariance / np.sqrt(var_a * var_b)

    return phi

@numba.njit()
def phi_dist(a, b, n_samples):
    covariance_mat = np.cov(a, b, rowvar=True)
    covariance = covariance_mat[0, 1]
    var_a = covariance_mat[0, 0]
    var_b = covariance_mat[1, 1]
    phi_dist = abs(math.log(var_a / var_b)) + math.log(2) - math.log(covariance / np.sqrt(var_a * var_b) + 1)

    return phi_dist

@numba.njit()
def aggregate_tnf(a, b, n_samples):
    w = n_samples / (n_samples + 1) # weighting by number of samples same as in metabat2
    l = min(a[0], b[0]) / (max(a[0], b[0]) + 1)

    tnf_dist = tnf(a[1:], b[1:], n_samples)
    if n_samples < 3:  
        aitchinson = euclidean(a[1:], b[1:], n_samples)  
        agg = (tnf_dist) * (aitchinson)
    else:
        rho_d = rho(a[1:], b[1:], n_samples)
        agg = (tnf_dist) * rho_d
    

    return agg

@numba.njit()
def aggregate_variant_tnf(a, b, n_samples):
    w = n_samples / (n_samples + 1) # weighting by number of samples same as in metabat2
    # Need to weigh by differences in contig size. TNF becomes less reliable as contigs diverge in size
    l = min(a[0], b[0]) / (max(a[0], b[0]) + 1)

    tnf_dist = tnf(a[1:], b[1:], n_samples)
    aitchinson = euclidean(a[1:], b[1:], n_samples)

    if n_samples >= 3:
        snv = snv_corr(a[1:], b[1:], n_samples)
        sv = sv_corr(a[1:], b[1:], n_samples)
        agg = (tnf_dist) * (aitchinson) * snv * sv
        return agg
    else:

        # Weighted average of these metrics. Weighted by w
        agg = (tnf_dist) * (aitchinson)

        return agg

@numba.njit()
def tnf_dist(a, b, n_samples):
    # w = n_samples / (n_samples + 1)  # weighting by number of samples same as in metabat2
    # Need to weigh by differences in contig size. TNF becomes less reliable as contigs diverge in size
    # l = min(a[0], b[0]) / (max(a[0], b[0]) + 1)

    covariance_mat = np.cov(a[1+n_samples:], b[1+n_samples:], rowvar=True)
    covariance = covariance_mat[0, 1]
    var_a = covariance_mat[0, 0]
    var_b = covariance_mat[1, 1]
    vlr = -2 * covariance + var_a + var_b
    rho = 1 - vlr / (var_a + var_b)
    rho += 1
    rho = 2 - rho

    return rho



@numba.njit()
def aggregate(a, b, n_samples):
    w = n_samples / (n_samples + 1) # weighting by number of samples same as in metabat2
    # tnf_dist = tnf(a, b, n_samples)
    aitchinson = euclidean(a, b, n_samples)
    rho_val = rho(a, b, n_samples)
    agg = aitchinson * rho_val

    return agg