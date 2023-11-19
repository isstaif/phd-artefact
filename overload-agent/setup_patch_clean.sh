sudo sysctl kernel.sched_energy_aware=1
sudo sysctl kernel.sched_schedstats=1
echo "-----"

sudo sysctl kernel.sched_disable_calc_group_shares=1
sudo sysctl kernel.sched_disable_vruntime_preemption=1
# sudo sysctl kernel.sched_slice_static_period=0
echo "-----"

echo "#sched_entity_before_policy == 0 entity_before(a,b)"
sudo sysctl kernel.sched_entity_before_policy=100
sudo sysctl kernel.sched_check_preempt_wakeup_latency_awareness=100
sudo sysctl kernel.sched_cpu_has_higher_load_task=100
echo "-----"

sudo sysctl kernel.sched_tg_load_avg_ema=1
sudo sysctl kernel.sched_tg_load_avg_ema_window=$1
echo "-----"

echo "setting default shares"
echo "/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/*/cpu.idle"
echo '0' | sudo tee -a /sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/*/cpu.idle
echo "/sys/fs/cgroup/cpu/*/cpu.shares"
echo "/sys/fs/cgroup/cpu/*/*/cpu.shares"
echo "/sys/fs/cgroup/cpu/*/*/*/cpu.shares"
echo "/sys/fs/cgroup/cpu/*/*/*/*/cpu.shares"
echo "/sys/fs/cgroup/cpu/*/*/*/*/cpu.shares"
echo '1024' | sudo tee -a /sys/fs/cgroup/cpu/*/cpu.shares
echo '1024' | sudo tee -a /sys/fs/cgroup/cpu/*/*/cpu.shares
echo '1024' | sudo tee -a /sys/fs/cgroup/cpu/*/*/*/cpu.shares
echo '1024' | sudo tee -a /sys/fs/cgroup/cpu/*/*/*/*/cpu.shares
echo "--------"

echo "resetting latency awawreness flags"
echo "/sys/fs/cgroup/cpu/cpu.latency_awareness"
echo "/sys/fs/cgroup/cpu/*/cpu.latency_awareness"
echo "/sys/fs/cgroup/cpu/*/*/cpu.latency_awareness"
echo "/sys/fs/cgroup/cpu/*/*/*/cpu.latency_awareness"
echo "/sys/fs/cgroup/cpu/*/*/*/*/cpu.latency_awareness"
echo '0' | sudo tee -a /sys/fs/cgroup/cpu/cpu.latency_awareness
echo '0' | sudo tee -a /sys/fs/cgroup/cpu/*/cpu.latency_awareness
echo '0' | sudo tee -a /sys/fs/cgroup/cpu/*/*/cpu.latency_awareness
echo '0' | sudo tee -a /sys/fs/cgroup/cpu/*/*/*/cpu.latency_awareness
echo '0' | sudo tee -a /sys/fs/cgroup/cpu/*/*/*/*/cpu.latency_awareness
echo "-----"

# echo "setting latency awawreness flags"
# echo "/sys/fs/cgroup/cpu/kubepods.slice/cpu.latency_awareness"
# echo "/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/cpu.latency_awareness"
echo "/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/*/cpu.latency_awareness"
# echo "/sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/*/*/cpu.latency_awareness"
# echo '1' | sudo tee -a /sys/fs/cgroup/cpu/kubepods.slice/cpu.latency_awareness
# echo '1' | sudo tee -a /sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/cpu.latency_awareness
echo '1' | sudo tee -a /sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/*/cpu.latency_awareness
# echo '1' | sudo tee -a /sys/fs/cgroup/cpu/kubepods.slice/kubepods-burstable.slice/*/*/cpu.latency_awareness
echo "--------"

echo "SCHED_RR"
echo "Resetting all to SCHED_OTHER"
systemd-cgls | grep 'bento\|queue\|pause' | grep -Eo '[[:digit:]]+' > allpids
while read pid; do sudo chrt -o -a -p 0 $pid; done < /home/aati2/allpids
sudo rm output
echo "Final SCHED setup"
systemd-cgls | grep 'bento\|queue\|pause' | grep -Eo '[[:digit:]]+' > allpids
echo "all pids"
cat /home/aati2/allpids | wc -l
echo "all under the default scheduling policy SCHED_OTHER"
while read pid; do sudo chrt -p $pid; done < /home/aati2/allpids | grep SCHED_OTHER | wc -l
echo "all under the default scheduling policy SCHED_RR"
while read pid; do sudo chrt -p $pid; done < /home/aati2/allpids | grep SCHED_RR | wc -l

