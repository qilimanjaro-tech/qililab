from flask import Flask, jsonify, render_template, request

from qililab import PLATFORM_MANAGER_DB
from qililab.experiment.run_experiment import run_experiment
from qililab.platform import Platform
from qililab.typings import Category

app = Flask(__name__)

platform: Platform = PLATFORM_MANAGER_DB.build(platform_name="platform_0")

SELECTED_PLATFORM = "platform_0"
SELECTED_GATE = "I"
SELECTED_CATEGORY = "signal_generator"
SELECTED_ID = 0
platform_list = ["platform_0", "unknown_platform"]
qili_category_list = ["signal_generator", "qubit_instrument", "resonator", "qubit", "mixer"]
gate_list = ["I", "X", "Y", "RX", "RY"]
id_list = [0, 1]


def load_categories(platform_name: str):
    return qili_category_list if platform_name == "platform_0" else []


def load_parameters(category: str, id_: int):
    element, _ = platform.get_element(category=Category(category), id_=id_)
    if element is None:
        parameter_list = []
    else:
        parameter_list = [
            name
            for name, value in element.settings.__dict__.items()
            if isinstance(value, (int, float)) and name != "id_"
        ]

    return parameter_list, element.name.value


@app.route("/", methods=["GET"])
def my_form():
    parameter_list, name = load_parameters(category=SELECTED_CATEGORY, id_=SELECTED_ID)
    category_list = load_categories(platform_name=SELECTED_PLATFORM)
    return render_template(
        "dashboard.html",
        platforms=platform_list,
        categories=category_list,
        gates=gate_list,
        ids=id_list,
        selected_platform=SELECTED_PLATFORM,
        selected_gate=SELECTED_GATE,
        selected_category=SELECTED_CATEGORY,
        selected_id=SELECTED_ID,
        parameters=parameter_list,
        name=name,
    )


@app.route("/experiments", methods=["GET"])
def launch_experiments():
    parameter_list, name = load_parameters(category=SELECTED_CATEGORY, id_=SELECTED_ID)
    category_list = load_categories(platform_name=SELECTED_PLATFORM)
    return render_template(
        "experiments.html",
        platforms=platform_list,
        categories=category_list,
        gates=gate_list,
        ids=id_list,
        selected_platform=SELECTED_PLATFORM,
        selected_gate=SELECTED_GATE,
        selected_category=SELECTED_CATEGORY,
        selected_id=SELECTED_ID,
        parameters=parameter_list,
        name=name,
    )


@app.route("/set_platform", methods=["GET", "POST"])
def set_platform():
    global SELECTED_PLATFORM
    SELECTED_PLATFORM = request.form.get("platforms")
    return my_form()


@app.route("/set_category", methods=["GET", "POST"])
def set_category():
    global SELECTED_CATEGORY, SELECTED_ID
    data = request.get_json()
    SELECTED_CATEGORY = data["category"]
    SELECTED_ID = int(data["id"])
    parameter_list, name = load_parameters(category=SELECTED_CATEGORY, id_=SELECTED_ID)
    return {"parameters": parameter_list, "name": name}


@app.route("/run", methods=["GET", "POST"])
def run():
    data = request.get_json()
    gate = data["gate"]
    parameter = data["parameter"]
    start = data["start"]
    stop = data["stop"]
    num = data["num"]
    run_experiment(
        gate=gate,
        category=SELECTED_CATEGORY,
        id_=SELECTED_ID,
        parameter=parameter,
        start=float(start),
        stop=float(stop),
        num=int(num),
    )
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
