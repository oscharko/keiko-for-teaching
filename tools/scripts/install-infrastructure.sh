#!/bin/bash
# Installation script for Keiko for Teaching Infrastructure
# This script installs all infrastructure components including monitoring, secrets management, and service mesh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    print_error "helm is not installed. Please install helm first."
    exit 1
fi

print_info "Starting infrastructure installation..."

# 1. Install Secrets Store CSI Driver
print_info "Installing Secrets Store CSI Driver..."
helm repo add secrets-store-csi-driver https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
helm repo update
helm upgrade --install csi-secrets-store secrets-store-csi-driver/secrets-store-csi-driver \
  --namespace kube-system \
  --set syncSecret.enabled=true \
  --set enableSecretRotation=true \
  --set rotationPollInterval=2m \
  --wait

# 2. Install Azure Key Vault Provider for Secrets Store CSI Driver
print_info "Installing Azure Key Vault Provider..."
helm repo add csi-secrets-store-provider-azure https://azure.github.io/secrets-store-csi-driver-provider-azure/charts
helm repo update
helm upgrade --install azure-csi-provider csi-secrets-store-provider-azure/csi-secrets-store-provider-azure \
  --namespace kube-system \
  --wait

# 3. Install External Secrets Operator
print_info "Installing External Secrets Operator..."
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
helm upgrade --install external-secrets external-secrets/external-secrets \
  --namespace external-secrets-system \
  --create-namespace \
  --set installCRDs=true \
  --wait

# 4. Create monitoring namespace
print_info "Creating monitoring namespace..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# 5. Install Prometheus
print_info "Installing Prometheus..."
kubectl apply -f ../../infra/kubernetes/base/monitoring/prometheus-deployment.yaml

# 6. Install Grafana
print_info "Installing Grafana..."
kubectl apply -f ../../infra/kubernetes/base/monitoring/grafana-deployment.yaml

# 7. Install Loki
print_info "Installing Loki..."
kubectl apply -f ../../infra/kubernetes/base/monitoring/loki-deployment.yaml

# 8. Install Promtail
print_info "Installing Promtail..."
kubectl apply -f ../../infra/kubernetes/base/monitoring/promtail-config.yaml

# 9. Install OpenTelemetry Collector
print_info "Installing OpenTelemetry Collector..."
kubectl apply -f ../../infra/kubernetes/base/monitoring/opentelemetry-deployment.yaml

# 10. Wait for monitoring components to be ready
print_info "Waiting for monitoring components to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=loki -n monitoring --timeout=300s

print_info "Monitoring stack installed successfully!"

# 11. Optional: Install Istio
read -p "Do you want to install Istio service mesh? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installing Istio..."
    
    # Check if istioctl is installed
    if ! command -v istioctl &> /dev/null; then
        print_warning "istioctl is not installed. Downloading Istio..."
        curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.1 sh -
        cd istio-1.20.1
        export PATH=$PWD/bin:$PATH
        cd ..
    fi
    
    # Install Istio
    istioctl install -f ../../infra/kubernetes/base/service-mesh/istio-installation.yaml -y
    
    # Apply mTLS configuration
    print_info "Applying mTLS configuration..."
    kubectl apply -f ../../infra/kubernetes/base/service-mesh/mtls-config.yaml
    
    # Apply traffic management configuration
    print_info "Applying traffic management configuration..."
    kubectl apply -f ../../infra/kubernetes/base/service-mesh/traffic-management.yaml
    
    # Enable sidecar injection for namespaces
    print_info "Enabling sidecar injection for namespaces..."
    kubectl label namespace keiko-teaching istio-injection=enabled --overwrite
    kubectl label namespace monitoring istio-injection=enabled --overwrite
    
    print_info "Istio service mesh installed successfully!"
else
    print_info "Skipping Istio installation."
fi

# 12. Display installation summary
print_info "Installation complete!"
echo ""
echo "Installed components:"
echo "  ✓ Secrets Store CSI Driver"
echo "  ✓ Azure Key Vault Provider"
echo "  ✓ External Secrets Operator"
echo "  ✓ Prometheus"
echo "  ✓ Grafana"
echo "  ✓ Loki"
echo "  ✓ Promtail"
echo "  ✓ OpenTelemetry Collector"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  ✓ Istio Service Mesh"
fi
echo ""
print_info "Next steps:"
echo "  1. Configure Azure Key Vault secrets"
echo "  2. Apply SecretProviderClass and ExternalSecret resources"
echo "  3. Access Grafana: kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "  4. Access Prometheus: kubectl port-forward -n monitoring svc/prometheus 9090:9090"

