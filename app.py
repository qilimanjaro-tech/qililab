from dataclasses import fields
from unicodedata import category

from flask import Flask, request, render_template
from qililab.experiment.run_experiment import run_experiment
from qililab import PLATFORM_MANAGER_DB
from qililab.platform import Platform
from qililab.typings import Category

app = Flask(__name__)

platform: Platform = PLATFORM_MANAGER_DB.build(platform_name="platform_0")

selected_platform = "platform_0"
selected_gate = "I"
selected_category = "signal_generator"
selected_id = 0
platform_list = ["platform_0", "unknown_platform"]
qili_category_list = ["signal_generator", "qubit_instrument", "resonator", "qubit", "mixer"]
gate_list = ["I", "X", "Y"]
id_list = [0, 1]

def load_categories(platform_name: str):
    if platform_name == "platform_0":
        category_list = qili_category_list
    else:
        category_list = []

    return category_list

def load_parameters(category: str, id_: int):
    element, _ = platform.get_element(category=Category(category), id_=id_)
    if element is None:
        parameter_list = []
    else:
        parameter_list = [name for name, value in element.settings.__dict__.items() if isinstance(value, (int, float)) and name != "id_"]

    return parameter_list

@app.route('/', methods=['GET'])
def my_form():
    parameter_list = load_parameters(category=selected_category, id_=selected_id)
    category_list = load_categories(platform_name=selected_platform)
    return render_template('index.html', platforms=platform_list, categories=category_list, gates=gate_list, ids=id_list,
    selected_platform=selected_platform, selected_gate=selected_gate, selected_category=selected_category, selected_id=selected_id,
    parameters=parameter_list)

@app.route("/set_platform", methods=['GET', 'POST'])
def set_platform():
    global selected_platform
    selected_platform = request.form.get('platforms')
    return my_form()


@app.route("/set_category" , methods=['GET', 'POST'])
def set_category():
    global selected_category, selected_id
    selected_category = request.form.get('categories')
    selected_id = int(request.form.get('ids'))
    return my_form()

@app.route('/run', methods=['GET', 'POST'])
def run():
    gate = request.form['gates']
    parameter = request.form['parameters']
    start = request.form['start']
    stop = request.form['stop']
    num = request.form['num']
    run_experiment(gate=gate, category=selected_category, id_=selected_id, parameter=parameter, start=float(start), stop=float(stop), num=int(num))
    return my_form()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
