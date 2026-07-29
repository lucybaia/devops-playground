# Monitoring

Prometheus and Grafana are installed via Helm in the Kubernetes cluster.

## Install

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --set grafana.adminPassword=admin
```

## Access

```bash
# Grafana (http://localhost:3001, admin/admin)
kubectl port-forward svc/monitoring-grafana -n monitoring 3001:80

# Prometheus (http://localhost:9090)
kubectl port-forward svc/prometheus-operated -n monitoring 9090:9090
```

## Custom metrics

The API exposes `/metrics` via `prometheus-client`. The ServiceMonitor is at `k8s/base/api/servicemonitor.yaml`.