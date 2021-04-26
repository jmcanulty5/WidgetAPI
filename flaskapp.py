import os
import sys
from datetime import datetime

from flask import Flask
from flask import request
from flask import abort
from flask import jsonify
from flask import g
from flask import Response
import jsonschema

from widgets import WidgetStore
from widgets import Widget

if os.getenv('CONNECT_STR', None) is None:
    print('must define CONNECT_STR env variable before starting server')
    sys.exit()

app = Flask(__name__)


def get_widget_store():
    widget_store = getattr(g, '_widget_store', None)
    if widget_store is None:
        widget_store = g._database = WidgetStore()
    return widget_store


@app.teardown_appcontext
def teardown_widget_store(exception):
    widget_store = getattr(g, '_widget_store', None)
    if widget_store is not None:
        widget_store.close()


@app.route('/widgets', methods=['GET'])
def get_widgets():
    try:
        widgets = get_widget_store().get_all_widgets()
        return jsonify([
            widget.to_json_obj()
            for widget in widgets
        ])
    except Exception:
        app.logger.exception('Unexpected exception')
        abort(500)


@app.route('/widgets', methods=['PUT'])
def put_widgets():
    try:
        new_widget_json_objs = request.get_json()
        for new_widget_json_obj in new_widget_json_objs:
            new_widget_json_obj.update({
                "updated_date": datetime.today().strftime("%Y-%m-%d"),
                "created_date": datetime.today().strftime("%Y-%m-%d")
            })
        new_widgets = [Widget.from_json_obj(w) for w in new_widget_json_objs]
        get_widget_store().delete_all_widgets()
        get_widget_store().put_widgets(new_widgets)
        return jsonify(new_widget_json_objs), 200
    except jsonschema.exceptions.ValidationError as ve:
        return (
            jsonify({
                "error class": "invalid widget representation",
                "uri": request.path,
                "cause": ve.message
            }),
            400
        )
    except Exception:
        app.logger.exception('Unexpected exception')
        abort(500)


@app.route('/widgets', methods=['DELETE'])
def delete_widgets():
    try:
        get_widget_store().delete_all_widgets()
        res = Response(status=204)
        del res.headers['Content-Type']
        return res
    except Exception:
        app.logger.exception('Unexpected exception')
        abort(500)


@app.route('/widgets/query', methods=['POST'])
def query_widgets():
    try:
        cond_spec = request.get_json()
        widgets = get_widget_store().get_widgets_by_cond_spec(cond_spec)
        return jsonify([
            widget.to_json_obj()
            for widget in widgets
        ])
    except jsonschema.exceptions.ValidationError as ve:
        return (
            jsonify({
                "error class": "invalid conditions specifications",
                "uri": request.path,
                "cause": ve.message
            }),
            400
        )
    except Exception:
        app.logger.exception('Unexpected exception')
        abort(500)


@app.route('/widgets/add', methods=['POST'])
def add_widgets():
    try:
        new_widget_json_objs = request.get_json()
        for new_widget_json_obj in new_widget_json_objs:
            new_widget_json_obj.update({
                "updated_date": datetime.today().strftime("%Y-%m-%d"),
                "created_date": datetime.today().strftime("%Y-%m-%d")
            })
        new_widgets = [Widget.from_json_obj(w) for w in new_widget_json_objs]
        get_widget_store().put_widgets(new_widgets)
        return jsonify(new_widget_json_objs), 200
    except jsonschema.exceptions.ValidationError as ve:
        return (
            jsonify({
                "error class": "invalid widget representation",
                "uri": request.path,
                "cause": ve.message
            }),
            400
        )
    except Exception:
        app.logger.exception('Unexpected exception')
        abort(500)


@app.route('/widgets/delete', methods=['POST'])
def bulk_delete_widgets():
    try:
        cond_spec = request.get_json()
        get_widget_store().delete_widgets_by_cond_spec(cond_spec)
        res = Response(status=204)
        del res.headers['Content-Type']
        return res
    except jsonschema.exceptions.ValidationError as ve:
        return (
            jsonify({
                "error class": "invalid conditions specifications",
                "uri": request.path,
                "cause": ve.message
            }),
            400
        )
    except Exception:
        app.logger.exception('Unexpected exception')
        abort(500)


@app.route('/widgets/<widget_name>', methods=['GET'])
def get_widget(widget_name):
    try:
        widget = get_widget_store().get_widget_by_name(widget_name)
        return jsonify(widget.to_json_obj())
    except LookupError:
        return (
            jsonify({
                "error class": "widget does not exist",
                "uri": request.path
            }),
            404
        )
    except Exception:
        app.logger.exception('Unexpected exception')
        abort(500)


@app.route('/widgets/<widget_name>', methods=['PUT'])
def put_widget(widget_name):
    try:
        try:  # if this succeeds, the widget already exists and is getting updated
            if not request.is_json:
                raise ValueError('request body was not parseable json')
            old_widget = get_widget_store().get_widget_by_name(widget_name)
            new_widget_json_obj = request.get_json()
            new_widget_json_obj.update({
                "updated_date": datetime.today().strftime("%Y-%m-%d"),
                "created_date": old_widget["Created date"]
            })
            new_widget = Widget.from_json_obj(new_widget_json_obj)
            get_widget_store().put_widget(new_widget)
            return jsonify(new_widget_json_obj), 200
        except LookupError:  # if we're here, a new widget is getting created
            new_widget_json_obj = request.get_json()
            new_widget_json_obj.update({
                "created_date": datetime.today().strftime("%Y-%m-%d"),
                "updated_date": datetime.today().strftime("%Y-%m-%d")
            })
            new_widget = Widget.from_json_obj(new_widget_json_obj)
            get_widget_store().put_widget(new_widget)
            return jsonify(new_widget_json_obj), 201
    except jsonschema.exceptions.ValidationError as ve:
        return (
            jsonify({
                "error class": "invalid widget representation",
                "uri": request.path,
                "cause": ve.message
            }),
            400
        )
    except Exception:
        app.logger.exception('Unexpected exception')
        abort(500)


@app.route('/widgets/<widget_name>', methods=['DELETE'])
def delete_widget(widget_name):
    try:
        get_widget_store().delete_widget_by_name(widget_name)
        res = Response(status=204)
        del res.headers['Content-Type']
        return res
    except LookupError:
        return (
            jsonify({
                "error class": "widget does not exist",
                "uri": request.path
            }),
            404
        )
    except Exception:
        app.logger.exception('Unexpected exception')
        abort(500)


@app.errorhandler(500)
def handle_internal_server_errors(e):
    return jsonify({"error class": "internal server error"}), 500
