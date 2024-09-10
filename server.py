import flask
from flask import jsonify, request
from flask.views import MethodView
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from models import Session, Advertisement
from schema import CreateAdv, UpdateAdv


app = flask.Flask("app")


class HttpError(Exception):

    def __init__(self, status_code: int, error_msg: str | dict | list):
        self.status_code = status_code
        self.error_msg = error_msg


@app.errorhandler(HttpError)
def http_error_handler(err: HttpError):
    http_response = jsonify({"status": "error", "message": err.error_msg})
    http_response.status = err.status_code
    return http_response


def validate_json(json_data: dict, schema_cls: type[CreateAdv] | type[UpdateAdv]):
    try:
        return schema_cls(**json_data).dict(exclude_unset=True)
    except ValidationError as err:
        errors = err.errors()
        for error in errors:
            error.pop("ctx", None)
        raise HttpError(400, errors)


@app.before_request
def before_request():
    session = Session()
    request.session = session


@app.after_request
def after_request(http_response: flask.Response):
    request.session.close()
    return http_response


def add_adv(adv: Advertisement):
    try:
        request.session.add(adv)
        request.session.commit()
    except IntegrityError:
        raise HttpError(409, "advertisement already exists")
    return adv


def get_adv(adv_id: int):
    adv = request.session.get(Advertisement, adv_id)
    if adv is None:
        raise HttpError(404, "advertisement not found")
    return adv


class AdvView(MethodView):

    def get(self, adv_id: int):
        adv = get_adv(adv_id)
        return jsonify(adv.json)

    def post(self):
        json_data = validate_json(request.json, CreateAdv)
        adv = Advertisement(**json_data)
        adv = add_adv(adv)
        return jsonify({"id": adv.id})

    def patch(self, adv_id):
        json_data = validate_json(request.json, UpdateAdv)
        adv = get_adv(adv_id)
        for field, value in json_data.items():
            setattr(adv, field, value)
        adv = add_adv(adv)
        return adv.json

    def delete(self, adv_id):
        adv = get_adv(adv_id)
        request.session.delete(adv)
        request.session.commit()
        return jsonify({"status": "deleted"})


adv_view = AdvView.as_view("advertisement")

app.add_url_rule("/advertisement/", view_func=adv_view, methods=["POST"])
app.add_url_rule(
    "/advertisement/<int:adv_id>/", view_func=adv_view, methods=["GET", "PATCH", "DELETE"]
)

app.run()
