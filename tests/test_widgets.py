import unittest
import unittest.mock
import json
import os

import jsonschema

from widgets import Widget
from widgets import WidgetStore


class TestWidget(unittest.TestCase):

    def setUp(self):
        self.sample_widget = Widget(
            name='sample',
            num_of_parts=5,
            created_date='2012-06-14',
            updated_date='2021-04-25',
            an_extra_prop=55555,
            a_complex_extra_prop={
                'stuff': [
                    4.1,
                    'eggs',
                    [3, 'spam']
                ]
            }
        )

    def test_construction_with_good_args(self):
        self.assertEqual(type(self.sample_widget), Widget)

    def test_construction_bad_args(self):
        with self.assertRaises(TypeError, msg='constructor should be called with all required args'):
            Widget(
                name=10,
                created_date='2012-06-14',
                updated_date='2021-04-25'
            )
        with self.assertRaises(TypeError, msg='name should be type str'):
            Widget(
                name=10,
                num_of_parts=5,
                created_date='2012-06-14',
                updated_date='2021-04-25'
            )
        with self.assertRaises(ValueError, msg='name should be 64 chars or less'):
            Widget(
                name='sampleeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
                num_of_parts=5,
                created_date='2012-06-14',
                updated_date='2021-04-25'
            )
        with self.assertRaises(TypeError, msg='num_of_parts should be type int'):
            Widget(
                name='sample',
                num_of_parts='5',
                created_date='2012-06-14',
                updated_date='2021-04-25'
            )
        with self.assertRaises(TypeError, msg='created_date should be type str'):
            Widget(
                name='sample',
                num_of_parts=5,
                created_date=0,
                updated_date='2021-04-25'
            )
        with self.assertRaises(TypeError, msg='updated_date should be type str'):
            Widget(
                name=10,
                num_of_parts=5,
                created_date='2012-06-14',
                updated_date=20210425
            )
        with self.assertRaises(ValueError, msg='created_date must abide YYYY-MM-DD format'):
            Widget(
                name='sample',
                num_of_parts=5,
                created_date='2012-6-14',
                updated_date='2021-04-25'
            )
        with self.assertRaises(ValueError, msg='updated_date must abide YYYY-MM-DD format'):
            Widget(
                name='sample',
                num_of_parts=5,
                created_date='2012-06-14',
                updated_date='04-25-2021'
            )
        with self.assertRaises(ValueError, msg='every extra widget property must be serializable to json'):
            Widget(
                name='sample',
                num_of_parts=5,
                created_date='2012-06-14',
                updated_date='2021-04-25',
                a_complex_extra_prop={
                    'stuff': [
                        set([1, 2, 3]),  # json doens't have set type
                        'eggs',
                        [3, 'spam']
                    ]
                }
            )

    def test_widget_repr(self):
        self.assertEqual(
            repr(self.sample_widget),
            "Widget(name='sample', num_of_parts=5, created_date='2012-06-14', updated_date='2021-04-25', an_extra_prop=55555, a_complex_extra_prop={'stuff': [4.1, 'eggs', [3, 'spam']]})"  # noqa, repr test
        )

    def test_widget_eq(self):
        equal_widget = Widget(
            name='sample',
            num_of_parts=5,
            created_date='2012-06-14',
            updated_date='2021-04-25',
            an_extra_prop=55555,
            a_complex_extra_prop={
                'stuff': [
                    4.1,
                    'eggs',
                    [3, 'spam']
                ]
            }
        )
        non_equal_widget = Widget(
            name='cheese',
            num_of_parts=7,
            created_date='2021-04-14',
            updated_date='2021-04-14',
        )
        self.assertEqual(self.sample_widget, equal_widget)
        self.assertNotEqual(self.sample_widget, non_equal_widget)

    def test_widget_contains(self):
        self.assertIn('name', self.sample_widget)
        self.assertNotIn('ham', self.sample_widget)

    def test_widget_iter(self):
        expected_keys = {
            'name',
            'num_of_parts',
            'created_date',
            'updated_date',
            'an_extra_prop',
            'a_complex_extra_prop'
        }
        for key in self.sample_widget:
            self.assertIn(key, expected_keys)

    def test_widget_getitem(self):
        self.assertEqual(self.sample_widget['name'], 'sample')
        self.assertEqual(self.sample_widget['num_of_parts'], 5)
        self.assertEqual(self.sample_widget['an_extra_prop'], 55555)
        self.assertEqual(self.sample_widget['a_complex_extra_prop']['stuff'][0], 4.1)
        with self.assertRaises(TypeError):
            self.sample_widget[5]
        with self.assertRaises(KeyError):
            self.sample_widget['non_existant_prop']

    def test_widget_public_immutability(self):
        with self.assertRaises(TypeError):
            self.sample_widget["name"] = 'new_name'

    def test_widget_from_json_obj(self):
        with self.assertRaises(jsonschema.exceptions.ValidationError, msg='invalid should fail'):
            Widget.from_json_obj({
                "Name": 5,
                "Creted": "dfgdfggdf"
            })
        sample_widget_json_rep = {
            "name": "sample",
            "num_of_parts": 5,
            "created_date": "2012-06-14",
            "updated_date": "2021-04-25",
            "an_extra_prop": 55555,
            "a_complex_extra_prop": {
                "stuff": [
                    4.1,
                    "eggs",
                    [3, "spam"]
                ]
            }
        }
        self.assertEqual(Widget.from_json_obj(sample_widget_json_rep), self.sample_widget)

    def test_widget_from_json_str(self):
        sample_widget_json_str = json.dumps({
            "name": "sample",
            "num_of_parts": 5,
            "created_date": "2012-06-14",
            "updated_date": "2021-04-25",
            "an_extra_prop": 55555,
            "a_complex_extra_prop": {
                "stuff": [
                    4.1,
                    "eggs",
                    [3, "spam"]
                ]
            }
        })
        self.assertEqual(Widget.from_json_str(sample_widget_json_str), self.sample_widget)

    def test_widget_to_json_obj(self):
        sample_widget_json_rep = {
            "name": "sample",
            "num_of_parts": 5,
            "created_date": "2012-06-14",
            "updated_date": "2021-04-25",
            "an_extra_prop": 55555,
            "a_complex_extra_prop": {
                "stuff": [
                    4.1,
                    "eggs",
                    [3, "spam"]
                ]
            }
        }
        self.assertEqual(self.sample_widget.to_json_obj(), sample_widget_json_rep)

    def test_widget_to_json_str(self):
        sample_widget_json_str = json.dumps({
            "name": "sample",
            "num_of_parts": 5,
            "created_date": "2012-06-14",
            "updated_date": "2021-04-25",
            "an_extra_prop": 55555,
            "a_complex_extra_prop": {
                "stuff": [
                    4.1,
                    "eggs",
                    [3, "spam"]
                ]
            }
        })
        self.assertEqual(self.sample_widget.to_json_str(), sample_widget_json_str)


class TestWidgetStore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.env_patcher = unittest.mock.patch.dict(os.environ, {'CONNECT_STR': ':memory:'})
        cls.env_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.env_patcher.stop()

    def setUp(self):
        self.widget_store = WidgetStore()
        self.sample_widget_1 = Widget(
            name='sample1',
            num_of_parts=5,
            created_date='2012-06-14',
            updated_date='2021-04-25',
            an_extra_prop=55555,
            a_complex_extra_prop={
                'stuff': [
                    4.1,
                    'eggs',
                    [3, 'spam']
                ]
            }
        )
        self.sample_widget_2 = Widget(
            name='sample2',
            num_of_parts=10,
            created_date='2017-07-04',
            updated_date='2021-04-25'
        )

    def test_put_widget_get_widget_delete_widget(self):
        self.widget_store.put_widget(self.sample_widget_1)
        self.assertEqual(
            self.widget_store.get_widget_by_name('sample1'),
            self.sample_widget_1
        )
        self.widget_store.delete_widget_by_name('sample1')
        with self.assertRaises(LookupError):
            self.widget_store.get_widget_by_name('sample1')

    def test_put_widgets_get_widgets_delete_widgets(self):
        widget_group = [
            self.sample_widget_1,
            self.sample_widget_2
        ]
        self.widget_store.put_widgets(widget_group)
        for widget in self.widget_store.get_all_widgets():
            self.assertIn(widget, widget_group)
        for widget in widget_group:
            self.assertIn(widget, self.widget_store.get_all_widgets())
        self.widget_store.delete_all_widgets()
        self.assertEqual(len(self.widget_store.get_all_widgets()), 0)

    def test_get_widgets_by_cond_spec(self):
        widget_group = [
            self.sample_widget_1,
            self.sample_widget_2
        ]
        self.widget_store.put_widgets(widget_group)
        cond_spec = [
            {
                "predicate": "gt",
                "variable": "created_date",
                "constants": ["2015-01-01"]
            }
        ]
        self.assertIn(
            self.sample_widget_2,
            self.widget_store.get_widgets_by_cond_spec(cond_spec)
        )

    def test_get_widgets_by_cond_spec_bad_spec(self):
        bad_cond_spec = [
            {
                "predicate": "like",
                "variable": 5,
                "constants": [{}, {}, {}]
            }
        ]
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            self.widget_store.get_widgets_by_cond_spec(bad_cond_spec)

    def test_delete_widgets_by_cond_spec(self):
        widget_group = [
            self.sample_widget_1,
            self.sample_widget_2
        ]
        self.widget_store.put_widgets(widget_group)
        cond_spec = [
            {
                "predicate": "gt",
                "variable": "created_date",
                "constants": ["2015-01-01"]
            }
        ]
        self.widget_store.delete_widgets_by_cond_spec(cond_spec)
        self.assertNotIn(
            self.sample_widget_2,
            self.widget_store.get_all_widgets()
        )

    def test_delete_widgets_by_cond_spec_bad_spec(self):
        bad_cond_spec = [
            {
                "predicate": "like",
                "variable": 5,
                "constants": [{}, {}, {}]
            }
        ]
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            self.widget_store.delete_widgets_by_cond_spec(bad_cond_spec)
