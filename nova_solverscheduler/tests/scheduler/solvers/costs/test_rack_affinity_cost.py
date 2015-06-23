# Copyright (c) 2014 Cisco Systems, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Test case for solver scheduler rack affinity cost."""

import mock

from nova import context
from nova import db
from nova.network import model as network_model
from nova import test
from nova_solverscheduler.scheduler.solvers import costs
from nova_solverscheduler.scheduler.solvers.costs import rack_affinity_cost
from nova_solverscheduler.tests.scheduler import solver_scheduler_fakes \
        as fakes


@mock.patch('nova.db.aggregate_host_get_by_metadata_key')
class TestTenantRackAffinityCost(test.NoDBTestCase):
    USES_DB = True

    def setUp(self):
        super(TestTenantRackAffinityCost, self).setUp()
        self.context = context.RequestContext('fake_usr', 'fake_proj')
        self.host_manager = fakes.FakeSolverSchedulerHostManager()
        self.cost_handler = costs.CostHandler()
        self.cost_classes = self.cost_handler.get_matching_classes(
                ['nova_solverscheduler.scheduler.solvers.costs.'
                'rack_affinity_cost.TenantRackAffinityCost'])

    def _get_fake_hosts(self):
        host1 = fakes.FakeSolverSchedulerHostState('host1', 'node1',
                {'projects': [self.context.project_id]})
        host2 = fakes.FakeSolverSchedulerHostState('host2', 'node2',
                {'Projects': []})
        host3 = fakes.FakeSolverSchedulerHostState('host3', 'node3',
                {'projects': [self.context.project_id]})
        host4 = fakes.FakeSolverSchedulerHostState('host4', 'node4',
                {'projects': []})
        host5 = fakes.FakeSolverSchedulerHostState('host5', 'node5',
                {'projects': []})
        host6 = fakes.FakeSolverSchedulerHostState('host6', 'node6',
                {'projects': []})
        return [host1, host2, host3, host4, host5, host6]

    def test_cost_multiplier(self, agg_mock):
        self.flags(tenant_rack_affinity_cost_multiplier=0.5,
                group='solver_scheduler')
        self.assertEqual(0.5,
                rack_affinity_cost.TenantRackAffinityCost().cost_multiplier())

    def test_get_extended_cost_matrix_normal(self, agg_mock):
        fake_hosts = self._get_fake_hosts()
        fake_cost = self.cost_classes[0]()
        fake_filter_properties = {
            'context': self.context,
            'project_id': self.context.project_id,
            'num_instances': 3
        }
        agg_mock.return_value = {
            'host1': set(['rack1']),
            'host2': set(['rack1']),
            'host3': set(['rack2']),
            'host4': set(['rack2']),
            'host5': set(['rack3']),
            'host6': set(['rack3'])
        }
        expected_x_cost_mat = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [1, 1, 1, 1]]
        x_cost_mat = fake_cost.get_extended_cost_matrix(fake_hosts,
                                                    fake_filter_properties)
        self.assertEqual(expected_x_cost_mat, x_cost_mat)

    def test_get_extended_cost_matrix_cross_rack_host_1(self, agg_mock):
        fake_hosts = self._get_fake_hosts()
        fake_cost = self.cost_classes[0]()
        fake_filter_properties = {
            'context': self.context,
            'project_id': self.context.project_id,
            'num_instances': 3
        }
        agg_mock.return_value = {
            'host1': set(['rack1']),
            'host2': set(['rack1']),
            'host3': set(['rack2']),
            'host4': set(['rack2']),
            'host5': set(['rack3', 'rack1']),
            'host6': set(['rack3'])
        }
        expected_x_cost_mat = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [1, 1, 1, 1]]
        x_cost_mat = fake_cost.get_extended_cost_matrix(fake_hosts,
                                                    fake_filter_properties)
        self.assertEqual(expected_x_cost_mat, x_cost_mat)

    def test_get_extended_cost_matrix_cross_rack_host_2(self, agg_mock):
        fake_hosts = self._get_fake_hosts()
        fake_cost = self.cost_classes[0]()
        fake_filter_properties = {
            'context': self.context,
            'project_id': self.context.project_id,
            'num_instances': 3
        }
        agg_mock.return_value = {
            'host1': set(['rack1', 'rack3']),
            'host2': set(['rack1']),
            'host3': set(['rack2']),
            'host4': set(['rack2']),
            'host5': set(['rack3']),
            'host6': set(['rack3'])
        }
        expected_x_cost_mat = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]]
        x_cost_mat = fake_cost.get_extended_cost_matrix(fake_hosts,
                                                    fake_filter_properties)
        self.assertEqual(expected_x_cost_mat, x_cost_mat)

    def test_get_extended_cost_matrix_incomplete_rack_config(self, agg_mock):
        fake_hosts = self._get_fake_hosts()
        fake_cost = self.cost_classes[0]()
        fake_filter_properties = {
            'context': self.context,
            'project_id': self.context.project_id,
            'num_instances': 3
        }
        agg_mock.return_value = {
            'host1': set(['rack1']),
            'host2': set(['rack1']),
            'host4': set(['rack2']),
            'host6': set(['rack3'])
        }
        expected_x_cost_mat = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [1, 1, 1, 1],
            [1, 1, 1, 1]]
        x_cost_mat = fake_cost.get_extended_cost_matrix(fake_hosts,
                                                    fake_filter_properties)
        self.assertEqual(expected_x_cost_mat, x_cost_mat)


@mock.patch('nova.db.aggregate_host_get_by_metadata_key')
class TestRackNetworkAffinityCost(test.NoDBTestCase):
    USES_DB = True

    def setUp(self):
        super(TestRackNetworkAffinityCost, self).setUp()
        self.context = context.RequestContext('fake_usr', 'fake_proj')
        self.host_manager = fakes.FakeSolverSchedulerHostManager()
        self.cost_handler = costs.CostHandler()
        self.cost_classes = self.cost_handler.get_matching_classes(
                ['nova_solverscheduler.scheduler.solvers.costs.'
                'rack_affinity_cost.RackNetworkAffinityCost'])

    def _get_fake_hosts(self):
        host1 = fakes.FakeSolverSchedulerHostState('host1', 'node1',
                {'projects': [self.context.project_id]})
        host2 = fakes.FakeSolverSchedulerHostState('host2', 'node2',
                {'Projects': []})
        host3 = fakes.FakeSolverSchedulerHostState('host3', 'node3',
                {'projects': [self.context.project_id]})
        host4 = fakes.FakeSolverSchedulerHostState('host4', 'node4',
                {'projects': []})
        host5 = fakes.FakeSolverSchedulerHostState('host5', 'node5',
                {'projects': []})
        host6 = fakes.FakeSolverSchedulerHostState('host6', 'node6',
                {'projects': []})
        return [host1, host2, host3, host4, host5, host6]

    def _setup_instances(self):
        instance1 = fakes.FakeInstance(context=self.context,
                                        params={'host': 'host1'})
        instance2 = fakes.FakeInstance(context=self.context,
                                        params={'host': 'host3'})
        instance1_uuid = instance1.uuid
        instance2_uuid = instance2.uuid
        nwinfo1 = network_model.NetworkInfo.hydrate(
                [{'network': {'id': 'net1'}}])
        nwinfo2 = network_model.NetworkInfo.hydrate(
                [{'network': {'id': 'net2'}}])
        db.instance_info_cache_update(self.context, instance1_uuid,
                {'network_info': nwinfo1.json()})
        db.instance_info_cache_update(self.context, instance2_uuid,
                {'network_info': nwinfo2.json()})

    def test_cost_multiplier(self, agg_mock):
        self.flags(rack_network_affinity_cost_multiplier=0.5,
                group='solver_scheduler')
        self.assertEqual(0.5,
                rack_affinity_cost.RackNetworkAffinityCost().cost_multiplier())

    def test_get_extended_cost_matrix_one_requested_network(self, agg_mock):
        fake_hosts = self._get_fake_hosts()
        self._setup_instances()
        fake_cost = self.cost_classes[0]()
        fake_filter_properties = {
            'context': self.context,
            'project_id': self.context.project_id,
            'num_instances': 3,
            'request_spec': {'requested_networks': [{'network_id': 'net1'}]}
        }
        agg_mock.return_value = {
            'host1': set(['rack1']),
            'host2': set(['rack1']),
            'host3': set(['rack2']),
            'host4': set(['rack2']),
            'host5': set(['rack3']),
            'host6': set(['rack3'])
        }
        expected_x_cost_mat = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [1, 1, 1, 1],
            [1, 1, 1, 1],
            [1, 1, 1, 1]]
        x_cost_mat = fake_cost.get_extended_cost_matrix(fake_hosts,
                                                    fake_filter_properties)
        self.assertEqual(expected_x_cost_mat, x_cost_mat)

    def test_get_extended_cost_matrix_multi_requested_networks(self, agg_mock):
        fake_hosts = self._get_fake_hosts()
        self._setup_instances()
        fake_cost = self.cost_classes[0]()
        fake_filter_properties = {
            'context': self.context,
            'project_id': self.context.project_id,
            'num_instances': 3,
            'request_spec': {'requested_networks': [{'network_id': 'net1'},
                                                    {'network_id': 'net2'}]}
        }
        agg_mock.return_value = {
            'host1': set(['rack1']),
            'host2': set(['rack1']),
            'host3': set(['rack2']),
            'host4': set(['rack2']),
            'host5': set(['rack3']),
            'host6': set(['rack3'])
        }
        expected_x_cost_mat = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [1, 1, 1, 1]]
        x_cost_mat = fake_cost.get_extended_cost_matrix(fake_hosts,
                                                    fake_filter_properties)
        self.assertEqual(expected_x_cost_mat, x_cost_mat)

    def test_get_extended_cost_matrix_no_requested_network(self, agg_mock):
        fake_hosts = self._get_fake_hosts()
        self._setup_instances()
        fake_cost = self.cost_classes[0]()
        fake_filter_properties = {
            'context': self.context,
            'project_id': self.context.project_id,
            'num_instances': 3,
            'request_spec': {'requested_networks': []}
        }
        agg_mock.return_value = {
            'host1': set(['rack1']),
            'host2': set(['rack1']),
            'host3': set(['rack2']),
            'host4': set(['rack2']),
            'host5': set(['rack3']),
            'host6': set(['rack3'])
        }
        expected_x_cost_mat = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]]
        x_cost_mat = fake_cost.get_extended_cost_matrix(fake_hosts,
                                                    fake_filter_properties)
        self.assertEqual(expected_x_cost_mat, x_cost_mat)

    def test_get_extended_cost_matrix_incomplete_rack_config(self, agg_mock):
        fake_hosts = self._get_fake_hosts()
        self._setup_instances()
        fake_cost = self.cost_classes[0]()
        fake_filter_properties = {
            'context': self.context,
            'project_id': self.context.project_id,
            'num_instances': 3,
            'request_spec': {'requested_networks': [{'network_id': 'net1'},
                                                    {'network_id': 'net2'}]}
        }
        agg_mock.return_value = {
            'host1': set(['rack1']),
            'host2': set(['rack1']),
            'host4': set(['rack2']),
            'host6': set(['rack3'])
        }
        expected_x_cost_mat = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [1, 1, 1, 1],
            [1, 1, 1, 1]]
        x_cost_mat = fake_cost.get_extended_cost_matrix(fake_hosts,
                                                    fake_filter_properties)
        self.assertEqual(expected_x_cost_mat, x_cost_mat)

    def test_get_extended_cost_matrix_with_hint_and_inst_prop(self, agg_mock):
        fake_hosts = self._get_fake_hosts()
        self._setup_instances()
        fake_cost = self.cost_classes[0]()
        fake_filter_properties = {
            'context': self.context,
            'project_id': self.context.project_id,
            'num_instances': 3,
            'scheduler_hints': {'affinity_networks': ['net1']},
            'request_spec': {'requested_networks': [],
                            'instance_properties': {'info_cache':
                            {'network_info': [{'network': {'id': 'net2'}}]}}}
        }
        agg_mock.return_value = {
            'host1': set(['rack1']),
            'host2': set(['rack1']),
            'host3': set(['rack2']),
            'host4': set(['rack2']),
            'host5': set(['rack3']),
            'host6': set(['rack3'])
        }
        expected_x_cost_mat = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [1, 1, 1, 1]]
        x_cost_mat = fake_cost.get_extended_cost_matrix(fake_hosts,
                                                    fake_filter_properties)
        self.assertEqual(expected_x_cost_mat, x_cost_mat)
