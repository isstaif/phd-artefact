
**Patch**

```
aati2@caelum-605:/local/scratch/linux$ git diff --stat
 kernel/sched/core.c  |  56 ++++++++
 kernel/sched/fair.c  | 245 +++++++++++++++++++++++++++++---
 kernel/sched/sched.h |   5 +
 3 files changed, 286 insertions(+), 20 deletions(-)
```

```
scp cfs-cr/setup* aati2@caelum-605.cl.cam.ac.uk:/home/aati2/
aati2@caelum-605:~$ chmod +x setup_patch_clean*
```

**Building only a portion of the kernel**

https://www.linuxtopia.org/online_books/linux_kernel/kernel_configuration/ch05s04.html

```
make kernel/sched
make M=kernel/sched
make -j1000 2> make_stderr.txt

sudo ls /boot/*0+*
#/boot/config-5.4.0+  /boot/initrd.img-5.4.0+  /boot/System.map-5.4.0+  /boot/vmlinuz-5.4.0+
	sudo rm /boot/*0+*
	
sudo make modules_install -j20
sudo make install -j20

#sudo nano /etc/initramfs-tools/initramfs.conf
sudo update-initramfs -c -k 5.18.0+
```

**Compiling 5.18.11**

```
commit 4b0986a3613c92f4ec1bdc7f60ec66fea135991f (grafted, HEAD -> controlled-cfs, tag: v5.18)
Author: Linus Torvalds <torvalds@linux-foundation.org>
Date:   Sun May 22 09:52:31 2022 -1000

    Linux 5.18
```

```python
sudo apt install git build-essential kernel-package fakeroot libncurses5-dev libssl-dev ccache bison flex
sudo apt install libelf-dev
sudo apt install zstd

```

Copy existing ubuntu settings ([URL](https://dev.to/wxyz/howto-compile-linux-kernel-on-ubuntu-applies-to-any-distro-44k7))

```python
cp /boot/config-$(uname -r) .config
```

Clear the pem from the config file or copy the file adopted
```
make menuconfig
```

```
make -j100 2> make_stderr.txt
sudo make modules_install -j20 2>> make_stderr.txt
sudo make install -j20
sudo update-initramfs -c -k 5.18.0+
```

Verify the version with `make kernelversion` ([URL](https://stackoverflow.com/questions/12151694/where-do-i-find-the-version-of-a-linux-kernel-source-tree))

And then set it in the grub loader ([URL](https://unix.stackexchange.com/questions/198003/set-default-kernel-in-grub)) by getting the menuentry_id_option

```
aati2@caelum-408:~$ grep submenu /boot/grub/grub.cfg
submenu 'Advanced options for Ubuntu' $menuentry_id_option 'gnulinux-advanced-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
aati2@caelum-408:~$ grep gnulinux /boot/grub/grub.cfg
menuentry 'Ubuntu' --class ubuntu --class gnu-linux --class gnu --class os $menuentry_id_option 'gnulinux-simple-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
submenu 'Advanced options for Ubuntu' $menuentry_id_option 'gnulinux-advanced-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
	menuentry 'Ubuntu, with Linux 5.4.0-109-generic' --class ubuntu --class gnu-linux --class gnu --class os $menuentry_id_option 'gnulinux-5.4.0-109-generic-advanced-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
	menuentry 'Ubuntu, with Linux 5.4.0-109-generic (recovery mode)' --class ubuntu --class gnu-linux --class gnu --class os $menuentry_id_option 'gnulinux-5.4.0-109-generic-recovery-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
	menuentry 'Ubuntu, with Linux 5.4.0-107-generic' --class ubuntu --class gnu-linux --class gnu --class os $menuentry_id_option 'gnulinux-5.4.0-107-generic-advanced-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
	menuentry 'Ubuntu, with Linux 5.4.0-107-generic (recovery mode)' --class ubuntu --class gnu-linux --class gnu --class os $menuentry_id_option 'gnulinux-5.4.0-107-generic-recovery-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
	menuentry 'Ubuntu, with Linux 5.4.0-100-generic' --class ubuntu --class gnu-linux --class gnu --class os $menuentry_id_option 'gnulinux-5.4.0-100-generic-advanced-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
	menuentry 'Ubuntu, with Linux 5.4.0-100-generic (recovery mode)' --class ubuntu --class gnu-linux --class gnu --class os $menuentry_id_option 'gnulinux-5.4.0-100-generic-recovery-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
	menuentry 'Ubuntu, with Linux 5.4.0' --class ubuntu --class gnu-linux --class gnu --class os $menuentry_id_option 'gnulinux-5.4.0-advanced-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
	menuentry 'Ubuntu, with Linux 5.4.0 (recovery mode)' --class ubuntu --class gnu-linux --class gnu --class os $menuentry_id_option 'gnulinux-5.4.0-recovery-e92f9e84-1fca-4cec-a6a0-7d4524fe4549' {
```

Updating the grub

```
#GRUB_DEFAULT=0
GRUB_DEFAULT="gnulinux-advanced-e92f9e84-1fca-4cec-a6a0-7d4524fe4549>gnulinux-5.4.0-advanced-e92f9e84-1fca-4cec-a6a0-7d4524fe4549"
```

```
aati2@caelum-408:/local/scratch/linux$ sudo nano /etc/default/grub
aati2@caelum-408:/local/scratch/linux$ sudo update-grub
Sourcing file `/etc/default/grub'
Sourcing file `/etc/default/grub.d/cl-caelum.cfg'
Sourcing file `/etc/default/grub.d/init-select.cfg'
Generating grub configuration file ...
Found linux image: /boot/vmlinuz-5.4.0-109-generic
Found initrd image: /boot/initrd.img-5.4.0-109-generic
Found linux image: /boot/vmlinuz-5.4.0-107-generic
Found initrd image: /boot/initrd.img-5.4.0-107-generic
Found linux image: /boot/vmlinuz-5.4.0-100-generic
Found initrd image: /boot/initrd.img-5.4.0-100-generic
**Found linux image: /boot/vmlinuz-5.4.0
Found initrd image: /boot/initrd.img-5.4.0**
done
```

```
uname -a
```


```bash
aati2@caelum-406:~$ curl -L https://www.kernel.org/finger_banner
The latest stable version of the Linux kernel is:             5.18.11
The latest mainline version of the Linux kernel is:           5.19-rc6
The latest stable 5.18 version of the Linux kernel is:        5.18.11
The latest stable 5.17 version of the Linux kernel is:        5.17.15 (EOL)
The latest longterm 5.15 version of the Linux kernel is:      5.15.54
The latest longterm 5.10 version of the Linux kernel is:      5.10.130
The latest longterm 5.4 version of the Linux kernel is:       5.4.205
The latest longterm 4.19 version of the Linux kernel is:      4.19.252
The latest longterm 4.14 version of the Linux kernel is:      4.14.288
The latest longterm 4.9 version of the Linux kernel is:       4.9.323
The latest linux-next version of the Linux kernel is:         next-20220713
```

```bash
git clone https://github.com/torvalds/linux.git --branch v5.18 --depth 1
```