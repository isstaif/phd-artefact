# phd-artefact

**Context**. Serverless computing is becoming an increasingly popular deployment model which allows developers to focus on application functionality while delegating server resource management to a service provider. This model is becoming increasingly considered in the context of edge computing as it avoids committing the limited server resources to tasks which might only use these resources occasionally. Serverless functions often experience extended periods of inactivity so a serverless platform that respects resource reservations may lead to wasted CPU resources. This problem can be exacerbated by the function concurrency feature, which requires users to reserve excess CPU resources to accommodate surges in incoming invocations. To address this, one potential approach is to overcommit cluster CPU resources, increasing the efficiency of serverless deployments at the cost of potentially increasing resource contention.

**Serverless workload characteristics**. Most functions have a low number of concurrent invocations. Yet it remains important to provision at least one CPU and plan for the peak concurrency due to the latency cost of concurrent cold starts. This issue is even more significant for high concurrency functions: a significant number of these have a high peak to average ratio (see FaaSNet and others). Statically provisioning a number of CPUs for these functions based on the peak demand can result in significant resource waste.

**Contention-resilience**:  We observe that by prioritising low concurrency functions during contention, this makes a cluster worker more resilient to contention. This policy also makes it more cost effective to enable concurrency without static allocation of CPU resources. Under high load, this policy allows to reduce the stress on CPU run queues and also enables higher concurrency to execute with less interruption. Under low load, this policy makes it safe for high concurrency functions to opportunistically utilise idle CPU cycles beyond allocated resources.

We propose a CPU resource management framework that enhances both the utilisation and responsiveness of serverless deployments while limiting the impact of increased CPU contention. We accomplish this through the use of contention-resilient CPU overcommitment mechanism that works in tandem with a vertical-first scaling approach. Overcommitment helps increase utilisation of cluster CPUs by enabling the cluster scheduler to pack more functions per cluster worker, and remains contention-resilient thanks to an enhanced kernel scheduler. During any potential overload, the proposed scheduler relaxes the fairness in a processor sharing policy to ensure that the majority of functions receive the CPU time they require without excessive interruption. The vertical-first approach also builds on this contention resilience to improve the responsiveness to request bursts. It helps to reduce the number of cold starts by limiting the initialisation of new function instances to when the CPU resources available for existing instances are exhausted.

**Design**. Our CPU resource management framework is designed as a worker server extension in a serverless cluster as well as an extension to a work-conserving kernel scheduler. The role of the scheduler extension is to robustly manage contention as CPU utilisation approaches high levels due to transient load spikes or cluster oversubscription. The worker extension controls CPU overcommitment and function scaling via two reactive mechanism that are driven by local processing of contention metrics:

- Contention-aware placement enables reactive CPU overcommitment by relaxing the constraints of static CPU resource reservations under low load and restricting placement when contention is observed. This mechanism can integrate with existing cluster scheduling techniques by removing the contended worker from the pool of scheduleable workers and rejoining this pool when contention is resolved.
- Contention-aware scaling is used to realise vertical-first scaling by enabling each application to be configured with its maximum concurrency. This mechanism detects contention on the granularity of each task and invokes horizontal scaling only when local worker CPU resources become exhausted due to colocated tasks.

https://lh7-us.googleusercontent.com/tuyjIerSkWcfvQ01sz3eFag2hKT3Qgga9BcCr4cD1NIvTnuIUyzxFO42fEtFJ-TWWnQ0fZxlv7wnFBrh56vEdJppL1RsLdxW37FM9E4Am5KVmsf428IVJWyRwmS2BULJhWFl2c0CRWRP1V6lFphNzBk

**Implementation**. We implement our framework to extend the functionality of Knative, a Kubernetes-based serverless framework deployed in a Linux cluster. We chose Knative because it supports generic container workloads where concurrency matters to reduce the impact of cold starts. We deploy our framework as a patch to the Linux kernel (CFS-LLF) and a cluster agent (CASP) that works alongside that of Kubernetes (Kublet) and can be easily ported to any framework that uses cgroups to manage function resources. The CFS-LLF patch adjusts CFS, the default Linux kernel and requires the administrator to identify the CPU run queue that is responsible for scheduling the cgroups that belong to the serverless functions. The CASP agent tracks new function instances initialised by Kubelet and uses their corresponding cgroups to process their kernel contention metrics. Based on these metrics, CASP implements reactive mechanisms to restrict placement and trigger scaling requests to the cluster scheduler. All function scheduling remains channelled through the Kubernetes control plane, which continues to play its role in creating network endpoints and directing incoming traffic through Knative Ingress Gateway's load balancer