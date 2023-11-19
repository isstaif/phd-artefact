import time
import subprocess
import os
import csv
import pandas as pd
import re
import json

from multiprocessing import Process
import argparse

from flask import Flask, request
app = Flask(__name__)

parser = argparse.ArgumentParser(description='Optional app description')
parser.add_argument('--ip_address', type=str, default="192.168.14.13",
                    help='A required integer positional argument')
parser.add_argument('--port', type=str, default="5000",
                    help='A required integer positional argument')
args = parser.parse_args()
print(args)

def load_cgroups():

    # fetching cgroup information
    cmd1 = "crictl --runtime-endpoint=/run/containerd/containerd.sock pods --namespace default -q > pods_ids"
    cmd2 = "crictl --runtime-endpoint=/run/containerd/containerd.sock pods --namespace default  | grep -v NAMESPACE | awk '{print   $6}' > pods_names"
    cmd3 = "cat pods_ids | xargs crictl --runtime-endpoint=/run/containerd/containerd.sock  inspectp | grep cgroup_parent > pods_cgroups"
    process = subprocess.Popen(
        [cmd1, cmd2, cmd3], stdout=subprocess.PIPE, shell=True)

    # loading cgroup information
    f = open(f'/home/aati2/pods_names')
    pods = f.read().strip().split('\n')
    f = open(f'/home/aati2/pods_cgroups')
    cgroups_raw = f.read().strip().split('\n')
    assert(len(pods) == len(cgroups_raw))
    ksvcs = [re.findall('(.*)-00001-deployment-.*', pod)[0] for pod in pods]
    cgroups = [re.findall('.*kubepods-burstable.slice/(.*)\"', cgroup)[0] for cgroup in cgroups_raw]
    return ksvcs, cgroups

ksvcs, cgroups = load_cgroups()

def get_snapshot():
    data = []
    for index, cgroup in enumerate(cgroups):
        f = open(
            f'/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/{cgroup}/cpuacct.usage')
        usage = f.read().strip()
        f = open(
            f'/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/{cgroup}/cpu.stat')
        wait_sum = f.read().split('\n')[3].split(' ')[1]
        # print(usage,wait_sum)
        data.append({'ksvc': ksvcs[index], 'usage': int(
            usage), 'wait_sum': int(wait_sum)})
    return data


def autoscale_pod(ksvc_name):
    print('scaling', ksvc_name)
    # cmd = f"/home/aati2/scale_pod.sh {ksvc_name}"
    # my_env = os.environ.copy()
    # my_env["KUBECONFIG"] = "/home/aati2/.kube/config"
    # process = subprocess.Popen(
    #     [cmd], stdout=subprocess.PIPE, shell=True, env=my_env)
    # output, error = process.communicate()
    # print(cmd)
    # print(output, error)
    # result.append((pod, output, error)) 

def cordon_node(cordon=True):
    print('cordon', cordon)

    # if cordon:
    #     cmd = f"kubectl cordon node"
    # else:
    #     cmd = f"kubectl uncordon node"

    # my_env = os.environ.copy()
    # my_env["KUBECONFIG"] = "/home/aati2/.kube/config"
    # process = subprocess.Popen(
    #     [cmd], stdout=subprocess.PIPE, shell=True, env=my_env)
    # output, error = process.communicate()
    # print(cmd)
    # print(output, error)
    # result.append((pod, output, error))          


def overload_loop(
    duration=100,
    contention_metric_window=5,
    overload_threshold=2000,
    scaling_threshold=100,
    cooldown_period=15):

    snapshots = []
    cooldown_counter = 0

    for tick in range(duration):

        # collect a snapshot of cgroup metrics
        tmp = pd.DataFrame(get_snapshot())
        snapshot = pd.DataFrame(
            [tmp['wait_sum'].values/1000000], columns=tmp['ksvc'].values)
        snapshots.append(snapshot)

        # process metrics
        dfmeasurements = pd.concat(snapshots)
        dfdiff = (dfmeasurements.shift(0) - dfmeasurements.shift(1))
        dfmetrics = dfdiff.rolling(contention_metric_window).mean()
        # dfdiff.sum(axis=1).plot(figsize=(15, 5), xlim=(0, 100))
        # dfmetrics.sum(axis=1).plot(figsize=(15,5),xlim=(0,100))
        # plt.show()

        # overload control loop
        if cooldown_counter == 0:

            # most recent sum of contention across all pods
            node_contention = dfmetrics.iloc[-1].sum()
            if node_contention > overload_threshold:

                cordon_node(True)
                cooldown_counter = cooldown_period

                # most 15 pods suffering from contention
                to_be_scaled = dfmetrics.iloc[-1].sort_values(ascending=False)[:15]
                print("to be considered for scaling", len(to_be_scaled), to_be_scaled.index)
                for ksvc,pod_contention in to_be_scaled.items(): 
                    if (pod_contention > scaling_threshold):
                        autoscale_pod(ksvc)
        else:            
            if cooldown_counter == 1:                 
                cordon_node(False)
            cooldown_counter = cooldown_counter - 1
            print('cooldown', cooldown_counter) 


        time.sleep(1)   

    if cooldown_counter > 0: cordon_node(False)


@app.route('/overload_loop')
def get_activate():

    duration = int(request.args.to_dict()['duration'])
    contention_metric_window = int(request.args.to_dict()['contention_metric_window'])
    overload_threshold = int(request.args.to_dict()['overload_threshold'])
    scaling_threshold = int(request.args.to_dict()['scaling_threshold'])
    cooldown_period = int(request.args.to_dict()['cooldown_period'])

    overload_loop(duration, contention_metric_window, overload_threshold, scaling_threshold,cooldown_period)
    return "Done"


@app.route('/overload_metrics')
def get_slowdown():

    data = []
    for index, cgroup in enumerate(cgroups):
        f = open(
            f'/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/{cgroup}/cpuacct.usage')
        usage = f.read().strip()
        f = open(
            f'/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/{cgroup}/cpu.stat')
        wait_sum = f.read().split('\n')[3].split(' ')[1]
        # print(usage,wait_sum)
        data.append({'ksvc': ksvcs[index], 'usage': int(
            usage), 'wait_sum': int(wait_sum)})
    return json.dumps(data)


@app.route('/pod_status')
def get_pod_status():

    my_env = os.environ.copy()
    my_env["KUBECONFIG"] = "/home/aati2/.kube/config"

    cmd1 = "kubectl get pods -o wide  | grep Running | grep  406 | wc -l"
    process = subprocess.Popen(
        [cmd1], stdout=subprocess.PIPE, shell=True, env=my_env)
    output1, error = process.communicate()

    cmd2 = "kubectl get pods -o wide  | grep Running | grep -v 406 | wc -l"
    process = subprocess.Popen(
        [cmd2], stdout=subprocess.PIPE, shell=True, env=my_env)
    output2, error = process.communicate()

    cmd = "kubectl get pods -o wide  | grep Running | grep (-v) 406 | wc -l"
    return cmd + ":" + str(output1) + "," + str(output2)

# @app.route('/overload_metrics_internal')
# def get_slowdown_internal():

#     data = []
#     for index,(cgroup,user_cgroup,proxy_cgroup) in enumerate(cgroups_internal):
#         f = open(f'/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/{cgroup}/{user_cgroup}/cpu.stat')
#         wait_sum1 = f.read().split('\n')[3].split(' ')[1]

#         f = open(f'/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/{cgroup}/{proxy_cgroup}/cpu.stat')
#         wait_sum2 = f.read().split('\n')[3].split(' ')[1]

#         data.append({'pod':index+1, 'wait_sum_user':int(wait_sum1), 'wait_sum_proxy':int(wait_sum2)})
#     return json.dumps(data)


@app.route('/nr_switches')
def get_nr_switches():
    cmd = f"sudo cat /sys/kernel/debug/sched/debug | grep nr_switches"
    process = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output, error

@app.route('/setup_patch')
def setup_patch():
    script = request.args.to_dict()['script']
    ema = request.args.to_dict()['ema']
    cmd = f"/home/aati2/{script} {ema}"
    process = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output, error

@app.route('/schedstat')
def get_schedstat():
    cmd = f"cat /proc/schedstat  | grep cpu"
    process = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output, error

@app.route('/schedstat_domains')
def get_schedstat_domains():
    cmd = f"cat /proc/schedstat  | grep domain0"
    process = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output, error

# @app.route('/function_profile_enabled')
# def function_profile_enabled():
#     enabled = request.args.to_dict()['enabled']
#     cmd = f"echo {enabled} | sudo tee -a /sys/kernel/debug/tracing/function_profile_enabled"
#     process = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
#     output, error = process.communicate()
#     return output,error

# @app.route('/get_sched_debug')
# def get_sched_debug():

#     for i in range(300):
#         cmd = f"cat /proc/sched_debug > /home/aati2/sched_debug-{i}"
#         print(cmd)
#         p = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
#         time.sleep(1)
#     #    commands.append(p)


app.run(host=args.ip_address, port=args.port, processes=200, threaded=False)
