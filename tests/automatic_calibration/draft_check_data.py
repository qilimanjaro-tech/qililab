from qililab.automatic_calibration.calibration_utils.calibration_utils import get_raw_data, get_iq_from_raw, plot_iq, plot_fit
import numpy as np

results = "./tests/automatic_calibration/rabi.yml"
data_raw = get_raw_data(results)
index=0
i = np.array([item["qblox_raw_results"][index]["bins"]["integration"]["path0"] for item in data_raw["results"]])
q = np.array([item["qblox_raw_results"][index]["bins"]["integration"]["path1"] for item in data_raw["results"]])
sweep_values = np.array(data_raw["loops"][0]['values'])
print(sweep_values)
print(len(i)-len(q))
print(len(i))
print(len(sweep_values))


def is_within_threshold(a, b, threshold):
    return b - threshold <= a <= b + threshold


'''
In check_data I can compare the results in each of the randomly chosen points to the results in the same point in the full calibration. 
'''
tolerance = 0
random_points = [0.0166667, 0.0333333] # these are points chosen randomly from the sweep interval used in rabi.yml



for point in random_points:
    # TODO: Run experiment in the point
    check_data_experiment_results = {}
    check_data_experiment_results_i = check_data_experiment_results["results"][0]["qblox_raw_results"][index]["bins"]["integration"]["path0"]
    check_data_experiment_results_q = check_data_experiment_results["results"][0]["qblox_raw_results"][index]["bins"]["integration"]["path1"]
    
    # Find corresponding results from full calibration results
    point_index = data_raw["loops"][0]['values'].index(point) #add exception if point is not in array
    point_result_i = data_raw["results"][point_index]["qblox_raw_results"][index]["bins"]["integration"]["path0"]
    point_result_q = data_raw["results"][point_index]["qblox_raw_results"][index]["bins"]["integration"]["path1"]
    
    # Compare results
    if is_within_threshold(point_result_i, check_data_experiment_results_i, tolerance) and is_within_threshold(point_result_q, check_data_experiment_results_q, tolerance):
        # results are compatible
        pass

# TODO: figure out how to look for bad data