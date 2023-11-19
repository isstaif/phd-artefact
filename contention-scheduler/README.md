
**Patch**

Commit information:
```
commit 4b0986a3613c92f4ec1bdc7f60ec66fea135991f (grafted, HEAD -> controlled-cfs, tag: v5.18)
Author: Linus Torvalds <torvalds@linux-foundation.org>
Date:   Sun May 22 09:52:31 2022 -1000

    Linux 5.18
```

Patch information:
```
 kernel/sched/core.c  |  56 ++++++++
 kernel/sched/fair.c  | 245 +++++++++++++++++++++++++++++---
 kernel/sched/sched.h |   5 +
 3 files changed, 286 insertions(+), 20 deletions(-)
```

To apply the patch:
```
git clone https://github.com/torvalds/linux.git --branch v5.18 --depth 1
cd linux
cp phd-artefact/contention-scheduler/cfs-cr.patch phd-artefact/contention-scheduler/src/.config 
git apply cfs-cr.patch
```

**Building only a portion of the kernel**

Dependencies to compile the kernel:
```
sudo apt install git build-essential kernel-package fakeroot libncurses5-dev libssl-dev ccache bison flex
sudo apt install libelf-dev
sudo apt install zstd
```

Compiling the kernel:

```
make kernel/sched
make M=kernel/sched
make -100 2> make_stderr.txt
sudo make modules_install -j100
sudo make install -j100
sudo nano /etc/initramfs-tools/initramfs.conf #MODULES=dep
sudo update-initramfs -c -k 5.18.0+
```

