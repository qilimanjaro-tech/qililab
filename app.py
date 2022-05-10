from flask import Flask, request, render_template
from qililab.experiment.run_experiment import run_experiment


app = Flask(__name__)

@app.route('/')
def my_form():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def my_form_post():
    gate = request.form['gate']
    category = request.form['category']
    id_ = request.form['id']
    parameter = request.form['parameter']
    start = request.form['start']
    stop = request.form['stop']
    num = request.form['num']
    run_experiment(gate=gate, category=category, id_=int(id_), parameter=parameter, start=float(start), stop=float(stop), num=int(num))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
