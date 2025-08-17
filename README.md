# k3s-quotehub

**k3s-quotehub** is a minimal Kubernetes lab on DigitalOcean using [k3s](https://k3s.io/). It runs a Flask API (Gunicorn) behind Nginx, showing hands-on Kubernetes basics: deployments, services, namespaces, image builds, and cloud setup.

---

## 🔧 Tech Stack

| Layer         | Tech                             |
|--------------|----------------------------------|
| Kubernetes    | k3s on DigitalOcean              |
| Backend       | Python Flask + Gunicorn          |
| Frontend      | Nginx (static + reverse proxy)   |
| Images        | Docker, pushed to GitHub Container Registry |
| Access        | kubectl + k3sup                  |

---

## 🛠️ Key Commands

### Provision VMs
```bash
doctl compute droplet create k3s-master --region fra1 --size s-1vcpu-1gb --image ubuntu-22-04-x64 --ssh-keys <fingerprint> --tag-names k3s-cluster
doctl compute droplet create k3s-worker-{1,2} --region fra1 --size s-1vcpu-1gb --image ubuntu-22-04-x64 --ssh-keys <fingerprint> --tag-names k3s-cluster
```

### Install k3s
```bash
k3sup install --ip <master-ip> --user root
k3sup join --ip <worker-ip> --server-ip <master-ip> --user root
```

### Set Default Namespace
```bash
kubectl config set-context --current --namespace=quotehub
```

### Export GitHub Environment Variables
```bash
export GITHUB_TOKEN=ghp_your_token_here
export GITHUB_USERNAME=your_github_username
```

### Build & Push Images
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# Build and tag for GitHub Container Registry
docker build -t ghcr.io/$GITHUB_USERNAME/quote-api:v1 ./api
docker push ghcr.io/$GITHUB_USERNAME/quote-api:v1
docker build -t ghcr.io/$GITHUB_USERNAME/nginx-web:v1 ./nginx
docker push ghcr.io/$GITHUB_USERNAME/nginx-web:v1
```

### Create GitHub Container Registry Secret
```bash
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=$GITHUB_USERNAME \
  --docker-password=$GITHUB_TOKEN \
  --docker-email=your-email@example.com
```

### Deploy to Cluster
```bash
# Export env vars from .env (required for envsubst in YAMLs)
export $(cat .env | xargs)
for f in k8s/*.yaml; do envsubst < "$f" | kubectl apply -f -; done
```

### Check App
```bash
kubectl get pods -n quotehub -o wide
curl http://<node-ip>:32080
curl http://<node-ip>:32080/api/quote
```

---

## 📁 Structure

```
api/     # Flask API
nginx/   # Nginx config + static
k8s/     # Kubernetes manifests
```

---

## 🚧 Real-World Issues Solved & Lessons Learned

This project wasn't just a clean deploy — it involved realistic debugging and configuration problems that mirror production scenarios. Here's what I encountered and resolved:

* **Image Pull Failures (`InvalidImageName`, `ImagePullBackOff`)**
  → Resolved by properly tagging and pushing images to Docker Hub, and ensuring `envsubst` was used correctly in deployment templates.

* **Cluster Connection Timeouts (`TLS handshake timeout`)**
  → Diagnosed master node memory exhaustion; fixed with swap file configuration on low-memory DigitalOcean droplets.

* **Pods not starting or disappearing**
  → Investigated `k3s-agent` logs, verified systemd status, and ensured consistent cluster state after resets.

* **Broken Nginx → API proxying (`404 Not Found`)**
  → Root-cause: trailing slash in `proxy_pass` stripping `/api` path. Solved by editing Nginx config.

* **Environment variable substitution issues with `envsubst`**
  → Used environment variables to keep sensitive information like credentials and registry details out of version control, ensuring secure deployment practices.

* **Validated intra-cluster DNS and service discovery**
  → Used `kubectl exec` with `curl` inside Nginx pods to confirm backend API worked independently of ingress issues.

* **GitHub Container Registry authentication issues (Pods couldn't pull images due to missing login)**
  → Fixed by creating a GitHub Container Registry secret with `kubectl create secret docker-registry` and referencing it in the deployment YAML to allow authenticated image pulls.
