# hpc-traffic-lights

Parallel traffic light optimization using SLURM job arrays on PLGrid HPC infrastructure.

This project was prepared for the **Large Scale Computing** course. The main goal is to use traffic light management as a realistic computational use case for demonstrating HPC concepts such as batch processing, SLURM job arrays, parallel execution, resource usage analysis, and result aggregation.

The project does not aim to build a production-ready smart city traffic control system. Instead, it provides a scalable prototype in which many traffic light configurations are evaluated in parallel on a computing cluster.

---

## Project idea

Large cities contain many intersections, traffic lights, sensors, and vehicles. Optimizing traffic light schedules can be computationally expensive because each candidate configuration has to be evaluated in a traffic simulation.

In this project, each traffic light configuration is treated as an independent experiment. This makes the workload suitable for **embarrassingly parallel execution** using **SLURM array jobs**.

The general workflow is:

```text
generate traffic light configurations
        |
        v
run many independent simulations in parallel
        |
        v
collect simulation metrics
        |
        v
aggregate results
        |
        v
select the best configuration
        |
        v
visualize and analyze the results
