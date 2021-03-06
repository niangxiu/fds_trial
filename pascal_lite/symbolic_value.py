###############################################################################
#                                                                              #
#   sa2d_decomp_value.py copyright(c) Qiqi Wang 2015 (qiqi.wang@gmail.com)     #
#                                                                              #
################################################################################

import os
import sys
import time
import collections
import copy as copymodule
from subprocess import Popen, PIPE
from io import BytesIO

import numpy as np

def _is_like_sa_value(a):
    '''
    Check attributes of symbolic array value
    '''
    if hasattr(a, 'owner'):
        return a.owner is None or hasattr(a.owner, 'inputs')
    else:
        return False

# ============================================================================ #
#                             symbolic array value                             #
# ============================================================================ #

class symbolic_array_value(object):
    def __init__(self, shape=(), owner=None, field=None, is_distributed=True):
        self.shape = np.empty(shape).shape
        self.owner = owner
        self.field = field
        self.is_distributed = is_distributed

    def __repr__(self):
        name = 'value of shape {0}'.format(self.shape)
        if self.is_distributed:
            name = 'distributed-' + name
        if self.owner:
            return 'Dependent {0} generated by {1}'.format(name, self.owner)
        else:
            return 'Independent {0}'.format(name)

    # --------------------------- properties ------------------------------ #

    @property
    def ndim(self):
        return len(self.shape)

    @property
    def size(self):
        return int(np.prod(self.shape))

    def __len__(self):
        return 1 if not self.shape else self.shape[0]


class builtin:
    ZERO = symbolic_array_value()
    RANDOM = []

def random_value(shape=()):
    new_random_value = symbolic_array_value(shape)
    builtin.RANDOM.append(new_random_value)
    return new_random_value


# ============================================================================ #
#                             computational graph                              #
# ============================================================================ #

def discover_operations_and_inputs(output_values):
    discovered_input_values = []
    discovered_operations = []
    def discover_values_from(v):
        if not hasattr(v, 'owner'):
            return
        if v.owner is None:
            if v not in discovered_input_values:
                discovered_input_values.append(v)
        elif v.owner not in discovered_operations:
            discovered_operations.append(v.owner)
            for v_inp in v.owner.inputs:
                discover_values_from(v_inp)
    for v in output_values:
        discover_values_from(v)
    return discovered_operations, discovered_input_values

def sort_operations(unsorted_operations):
    sorted_operations = []
    def is_computable(v):
        return (not _is_like_sa_value(v) or
                v.owner is None or
                v.owner in sorted_operations)
    while len(unsorted_operations):
        removed_any = False
        for op in unsorted_operations:
            if all([is_computable(inp) for inp in op.inputs]):
                unsorted_operations.remove(op)
                sorted_operations.append(op)
                removed_any = True
        assert removed_any
    return sorted_operations

def forgettable_values(sorted_operations):
    values_used_total = collections.defaultdict(int)
    for op in sorted_operations:
        for inp in op.inputs:
            if _is_like_sa_value(inp):
                values_used_total[inp] += 1
    values_used = collections.defaultdict(int)
    remove_values = collections.defaultdict(set)
    for i in range(len(sorted_operations)):
        op = sorted_operations[i]
        for inp in op.inputs:
            if _is_like_sa_value(inp):
                values_used[inp] += 1
                if values_used[inp] == values_used_total[inp]:
                    remove_values[op].add(inp)
    return remove_values

class ComputationalGraph(object):
    '''
    Immutable compact stage
    '''
    def __init__(self, output_values):
        unsorted_operations, self.input_values \
            = discover_operations_and_inputs(output_values)
        self.sorted_operations = sort_operations(unsorted_operations)
        assert(all(v.owner in self.sorted_operations for v in output_values))
        assert unsorted_operations == []
        self.output_values = copymodule.copy(output_values)

    def __call__(self, input_map):
        if hasattr(input_map, '__call__'):
            actual_inputs = [input_map(v) for v in self.input_values]
        elif hasattr(input_map, '__getitem__'):
            actual_inputs = [input_map[v] for v in self.input_values]
        # _act attributes are assigned to inputs
        values_assigned_act = set()
        for v, v_act in zip(self.input_values, actual_inputs):
            assert not hasattr(v, '_act')
            v._act = v_act
            values_assigned_act.add(v)
        # _act attributes are computed to each value
        def _act(v):
            if _is_like_sa_value(v):
                return v._act
            elif isinstance(v, np.ndarray):
                return v.reshape(v.shape + (1,))
            else:
                return v
        remove_act_values = forgettable_values(self.sorted_operations)
        for op in self.sorted_operations:
            assert not any(hasattr(outp, '_act') for outp in op.outputs)
            inputs_act = [_act(inp) for inp in op.inputs]
            outputs_act = op.perform(inputs_act)
            for inp in remove_act_values[op]:
                if hasattr(inp, '_act') and inp not in self.output_values:
                    del inp._act
                    values_assigned_act.remove(inp)
            for outp, outp_act in zip(op.outputs, outputs_act):
                outp._act = outp_act
                values_assigned_act.add(outp)
        # _act attributes are extracted from outputs then deleted from all
        actual_outputs = tuple(v._act for v in self.output_values)
        for v in values_assigned_act:
            del v._act
        return actual_outputs

################################################################################
################################################################################
################################################################################
