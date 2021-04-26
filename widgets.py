import json
import re
import os
from sqlite3 import connect

import jsonschema

import jschemas


class Widget:

    _required_properties = {
        "name",
        "num_of_parts",
        "created_date",
        "updated_date"
    }

    def __init__(self, name, num_of_parts, created_date, updated_date, **kwargs):
        self._validate_name(name)
        self._validate_num_of_parts(num_of_parts)
        self._validate_created_date(created_date)
        self._validate_updated_date(updated_date)
        self._validate_kwargs(kwargs)
        self._widget_data = {
            "name": name,
            "num_of_parts": num_of_parts,
            "created_date": created_date,
            "updated_date": updated_date,
            **kwargs
        }

    @classmethod
    def from_json_obj(cls, json_obj):
        cls._validate_json_obj(json_obj)
        return cls(
            name=json_obj['name'],
            num_of_parts=json_obj['num_of_parts'],
            created_date=json_obj['created_date'],
            updated_date=json_obj['updated_date'],
            **dict((e, json_obj[e]) for e in json_obj if e not in cls._required_properties)
        )

    @classmethod
    def from_json_str(cls, json_str):
        json_obj = json.loads(json_str)
        cls._validate_json_obj(json_obj)
        return cls(
            name=json_obj['name'],
            num_of_parts=json_obj['num_of_parts'],
            created_date=json_obj['created_date'],
            updated_date=json_obj['updated_date'],
            **dict((e, json_obj[e]) for e in json_obj if e not in cls._required_properties)
        )

    def to_json_obj(self):
        return json.loads(json.dumps(self._widget_data))  # defensive copy

    def to_json_str(self):
        return json.dumps(self._widget_data)

    def __getitem__(self, key):
        if type(key) is not str:
            raise TypeError('property names should only be str, not %s' % type(key))
        try:
            return self._widget_data[key]
        except KeyError as ex:
            raise KeyError('property name %s does not exist for Widget' % ex)

    def __iter__(self):
        return (k for k in self._widget_data)

    def __contains__(self, item):
        return item in self._widget_data

    def __eq__(self, other):
        have_same_keys = set(self._widget_data.keys()) == set(other._widget_data.keys())
        return have_same_keys and all(
            self._widget_data[k] == other._widget_data[k]
            for k in self._widget_data
        )

    def __repr__(self):
        return 'Widget(%s)' % ', '.join(
            k + '=' + repr(self._widget_data[k])
            for k in self._widget_data
        )

    def _validate_name(self, name):
        if type(name) is not str:
            raise TypeError('name must be str, not %s' % type(name))
        if not len(name) <= 64:
            raise ValueError('name length must be less than or equal to 64 characters, not %s' % len(name))

    def _validate_num_of_parts(self, num_of_parts):
        if type(num_of_parts) is not int:
            raise TypeError('num_of_parts must be int, not %s' % type(num_of_parts))

    def _validate_created_date(self, created_date):
        if type(created_date) is not str:
            raise TypeError('created_date must be str, not %s' % type(created_date))
        if re.match(r'\d{4}-\d{2}-\d{2}', created_date) is None:
            raise ValueError('created_date (%s) does not match YYYY-MM-DD format', created_date)

    def _validate_updated_date(self, updated_date):
        if type(updated_date) is not str:
            raise TypeError('updated_date must be str, not %s' % type(updated_date))
        if re.match(r'\d{4}-\d{2}-\d{2}', updated_date) is None:
            raise ValueError('updated_date (%s) does not match YYYY-MM-DD format', updated_date)

    def _validate_kwargs(self, kwarg_dict):
        try:
            json.dumps(kwarg_dict)
        except Exception:
            raise ValueError('every extra widget property must be serializable to json')

    @classmethod
    def _validate_json_obj(cls, json_obj):
        jsonschema.validate(instance=json_obj, schema=jschemas.widget_schema)


class WidgetStore:

    _cond_spec_schema = jschemas.cond_spec_schema

    def __init__(self):
        self.connect_str = os.getenv('CONNECT_STR')
        self.conn = connect(self.connect_str)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS widgets (
                Name TEXT PRIMARY KEY,
                NumOfParts INTEGER NOT NULL,
                CreatedDate TEXT NOT NULL,
                UpdatedDate TEXT NOT NULL,
                FlexProperties BLOB
            );
        """)

    def close(self):
        self.conn.close()

    def get_widget_by_name(self, name):
        try:
            curs = self.conn.execute("""
                SELECT *
                FROM widgets
                WHERE Name = ?
            """, (name,))
            result = curs.fetchone()
        except Exception as ex:
            curs.close()
            raise ex
        else:
            if result is None:
                raise LookupError('widget with given name is not in store')
            return self._row_to_widget(result)

    def get_all_widgets(self):
        try:
            curs = self.conn.execute("""
                SELECT *
                FROM widgets
            """)
            return list(map(self._row_to_widget, curs))
        except Exception as ex:
            curs.close()
            raise ex

    def put_widget(self, widget):
        row = self._widget_to_row(widget)
        with self.conn:
            self.conn.execute("""
                UPDATE widgets
                SET Name = ?, NumOfParts = ?, CreatedDate = ?, UpdatedDate = ?, FlexProperties = ?
                WHERE Name = ?
            """, row + (row[0],))
            self.conn.execute("""
                INSERT OR IGNORE INTO widgets
                VALUES (?, ?, ?, ?, ?);
            """, row)

    def get_widgets_by_cond_spec(self, cond_spec):
        self._validate_cond_spec(cond_spec)
        predicate2sqlop = {
            'isnull': 'IS NULL',
            'not isnull': 'IS NOT NULL',
            'eq': '= ?',
            'ne': '!= ?',
            'le': '<= ?',
            'ge': '>= ?',
            'lt': '< ?',
            'gt': '> ?',
            'like': 'LIKE ?',
            'not like': 'NOT LIKE ?',
            'between': 'BETEWEEN ? AND ?',
            'not between': 'NOT BETWEEN ? AND ?'
        }
        variables2dbcolumns = {
            'name': 'Name',
            'num_of_parts': 'NumOfParts',
            'created_date': 'CreatedDate',
            'updated_date': 'UpdatedDate'
        }
        parameterized_sql_conditions = []
        actual_values_for_parameters = []
        for cond in cond_spec:
            if cond["variable"] not in variables2dbcolumns:
                raise ValueError('%s is not an allowed variable' % cond['variable'])
            parameterized_sql_conditions.append(
                variables2dbcolumns[cond['variable']] + ' ' + predicate2sqlop[cond['predicate']]
            )
            actual_values_for_parameters.extend(cond['constants'])
        parameterized_sql_where_clause = ' AND '.join(parameterized_sql_conditions)
        try:
            if len(parameterized_sql_conditions) == 0:
                curs = self.conn.execute("""
                    SELECT *
                    FROM widgets
                """)
            else:
                curs = self.conn.execute(
                    """
                    SELECT *
                    FROM widgets
                    WHERE  """ + parameterized_sql_where_clause,  # nosec, strict whitelist used
                    actual_values_for_parameters
                )
            return list(map(self._row_to_widget, curs))
        except Exception as ex:
            curs.close()
            raise ex

    def delete_widgets_by_cond_spec(self, cond_spec):
        self._validate_cond_spec(cond_spec)
        predicate2sqlop = {
            'isnull': 'IS NULL',
            'not isnull': 'IS NOT NULL',
            'eq': '= ?',
            'ne': '!= ?',
            'le': '<= ?',
            'ge': '>= ?',
            'lt': '< ?',
            'gt': '> ?',
            'like': 'LIKE ?',
            'not like': 'NOT LIKE ?',
            'between': 'BETEWEEN ? AND ?',
            'not between': 'NOT BETWEEN ? AND ?'
        }
        variables2dbcolumns = {
            'name': 'Name',
            'num_of_parts': 'NumOfParts',
            'created_date': 'CreatedDate',
            'updated_date': 'UpdatedDate'
        }
        parameterized_sql_conditions = []
        actual_values_for_parameters = []
        for cond in cond_spec:
            if cond["variable"] not in variables2dbcolumns:
                raise ValueError('%s is not an allowed variable' % cond['variable'])
            parameterized_sql_conditions.append(
                variables2dbcolumns[cond['variable']] + ' ' + predicate2sqlop[cond['predicate']]
            )
            actual_values_for_parameters.extend(cond['constants'])
        parameterized_sql_where_clause = ' AND '.join(parameterized_sql_conditions)
        try:
            if len(parameterized_sql_conditions) == 0:
                curs = self.conn.execute("""
                    DELETE FROM widgets
                """)
                self.conn.commit()
            else:
                curs = self.conn.execute(
                    """
                    DELETE FROM widgets
                    WHERE """ + parameterized_sql_where_clause,  # nosec, strict whitelist used
                    actual_values_for_parameters
                )
                self.conn.commit()
        except Exception as ex:
            curs.close()
            raise ex

    def put_widgets(self, widgets):
        with self.conn:
            for widget in widgets:
                row = self._widget_to_row(widget)
                self.conn.execute("""
                    UPDATE widgets
                    SET Name = ?, NumOfParts = ?, CreatedDate = ?, UpdatedDate = ?, FlexProperties = ?
                    WHERE Name = ?;
                """, row + (row[0],))
                self.conn.execute("""
                    INSERT OR IGNORE INTO widgets
                    VALUES (?, ?, ?, ?, ?);
                """, row)

    def delete_widget_by_name(self, name):
        curs = self.conn.execute("""
            DELETE FROM widgets
            WHERE Name = ?;
        """, (name,))
        self.conn.commit()
        if curs.rowcount < 1:
            raise LookupError('widget with given name is not in store')

    def delete_all_widgets(self):
        with self.conn:
            self.conn.execute("""
                DELETE FROM widgets;
            """)

    def _row_to_widget(self, row):
        return Widget(
            name=row[0],
            num_of_parts=row[1],
            created_date=row[2],
            updated_date=row[3],
            **json.loads(
                str(row[4], encoding='utf-8')
                if row[4] is not None
                else '{}'
            )
        )

    def _widget_to_row(self, widget):
        return (
            widget['name'],
            widget['num_of_parts'],
            widget['created_date'],
            widget['updated_date'],
            bytes(
                json.dumps({
                    e: widget[e]
                    for e in widget
                    if e not in Widget._required_properties
                }),
                encoding='utf-8'
            )
        )

    def _validate_cond_spec(self, cond_spec):
        jsonschema.validate(instance=cond_spec, schema=self._cond_spec_schema)
