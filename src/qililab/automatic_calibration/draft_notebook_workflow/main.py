"""Autocalibration example script to run"""
import os

from notebook_workflow import NbWorkFlow

# CHANGE OS DIRECTORY TO THE ONE OF THIS FILE:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


# EXECUTE NOTEBOOKS
# Create a Notebook workflow object, which creates a stream object to save the logger outputs of the notebooks:
nb_workflow = NbWorkFlow()

# 1st notebook:
params = nb_workflow.execute_notebook("first.ipynb", nb_workflow.create_notebook_datetime_path("results/first.ipynb"))
print(params)

# 2n notebook that depends on the 1st:
params = nb_workflow.execute_notebook(
    "second.ipynb", nb_workflow.create_notebook_datetime_path("results/second/second"), params
)
print(params)

# 3rd notebook that depends on the 2nd:
params = nb_workflow.execute_notebook(
    "third.ipynb", nb_workflow.create_notebook_datetime_path("results/third/3rd.ipynb"), params
)
print(params)
