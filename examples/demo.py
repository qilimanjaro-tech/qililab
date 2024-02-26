import qililab as ql

platform = ql.build_platform(runcard="/home/fedonman/projects/qililab/examples/runcards/galadriel.yml")
print(platform.buses)
