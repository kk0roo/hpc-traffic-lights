# Dashboard - TO DO
A minimal, optional static dashboard for showing final plots and the best
configuration

## Run locally with Docker

```bash
docker build -t hpc-traffic-lights-dashboard dashboard/
docker run --rm -p 8080:80 hpc-traffic-lights-dashboard
# open http://localhost:8080
```

## Run on local Kubernetes (Minikube)

```bash
minikube start
eval $(minikube docker-env)
docker build -t hpc-traffic-lights-dashboard:latest dashboard/
kubectl apply -f dashboard/k8s-deployment.yaml
minikube service hpc-traffic-lights-dashboard
```

## Files

- `index.html` — placeholder page (future: embed plots from `results/plots/`).
- `Dockerfile` — serves `index.html` with `httpd:2.4`.
- `k8s-deployment.yaml` — Deployment + NodePort Service for Minikube.

