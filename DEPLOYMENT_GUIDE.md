# 🚢 GUIDE DE DÉPLOIEMENT

Guide complet pour déployer l'Application Agricole & Élevage en développement et production.

## 📋 Table des matières

1. [Développement Local](#développement-local)
2. [Commandes Docker Utiles](#commandes-docker-utiles)
3. [Configuration](#configuration)
4. [Déploiement Production](#déploiement-production)
5. [Monitoring](#monitoring)
6. [Backup & Restauration](#backup--restauration)
7. [Troubleshooting](#troubleshooting)

---

## 🖥️ Développement Local

### Prérequis

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **8 GB RAM** minimum (16 GB recommandé)
- **20 GB** espace disque libre

### Installation

```bash
# 1. Cloner le projet (si applicable)
cd c:\LLM_agents_class\application_agricole

# 2. Configuration
cp .env.example .env
# Éditer .env et personnaliser les mots de passe

# 3. Build
docker-compose build

# 4. Démarrage
docker-compose up -d

# 5. Vérification
docker-compose ps
curl http://localhost/health
```

### Commandes rapides (Makefile)

```bash
make setup      # Configuration initiale
make build      # Build des images
make up         # Démarrage des services
make down       # Arrêt des services
make restart    # Redémarrage
make logs       # Voir les logs
make logs-f     # Suivre les logs en temps réel
make ps         # Status des services
make clean      # Nettoyage complet (supprime les données!)
```

---

## 🐳 Commandes Docker Utiles

### Gestion des conteneurs

```bash
# Lister tous les conteneurs
docker-compose ps

# Lister avec détails
docker ps -a

# Démarrer tous les services
docker-compose up -d

# Arrêter tous les services
docker-compose down

# Arrêter + supprimer volumes (ATTENTION: perte de données)
docker-compose down -v

# Redémarrer un service spécifique
docker-compose restart identity-service

# Redémarrer tous les services
docker-compose restart
```

### Logs

```bash
# Tous les services
docker-compose logs

# Suivre les logs en temps réel
docker-compose logs -f

# Service spécifique
docker-compose logs identity-service
docker-compose logs -f inventory-service

# Dernières 100 lignes
docker-compose logs --tail=100

# Logs avec timestamps
docker-compose logs -t

# Filtrer par service
docker-compose logs identity-service sales-service
```

### Build et images

```bash
# Build toutes les images
docker-compose build

# Build sans cache
docker-compose build --no-cache

# Build un service spécifique
docker-compose build identity-service

# Build et redémarrer
docker-compose up -d --build

# Lister les images
docker images | grep agricole

# Supprimer images inutilisées
docker image prune -a
```

### Exec dans les conteneurs

```bash
# Shell interactif dans un service
docker-compose exec identity-service sh

# Exécuter une commande
docker-compose exec identity-service ls -la

# Shell PostgreSQL
docker-compose exec postgres psql -U agricole_user -d identity_db

# Redis CLI
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD}

# RabbitMQ status
docker-compose exec rabbitmq rabbitmqctl status
```

### Volumes et données

```bash
# Lister les volumes
docker volume ls

# Inspecter un volume
docker volume inspect application_agricole_postgres_data

# Supprimer un volume spécifique
docker volume rm application_agricole_postgres_data

# Supprimer volumes orphelins
docker volume prune
```

### Réseau

```bash
# Lister les réseaux
docker network ls

# Inspecter le réseau
docker network inspect application_agricole_agricole_network

# Voir les IPs des conteneurs
docker network inspect application_agricole_agricole_network | grep -A 3 "Name"
```

---

## ⚙️ Configuration

### Variables d'environnement (.env)

**Important** : Modifier les mots de passe par défaut en production!

```bash
# Copier le template
cp .env.example .env

# Éditer
nano .env  # ou vi, code, notepad++, etc.
```

**Variables critiques à modifier** :

```env
# JWT - CHANGER EN PRODUCTION
JWT_SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire-2025

# PostgreSQL
POSTGRES_PASSWORD=mot-de-passe-securise-postgres

# RabbitMQ
RABBITMQ_DEFAULT_PASS=mot-de-passe-securise-rabbitmq

# Redis
REDIS_PASSWORD=mot-de-passe-securise-redis

# MinIO
MINIO_ROOT_PASSWORD=mot-de-passe-securise-minio
```

### Ports personnalisés

Si les ports par défaut sont occupés :

```env
# Dans .env
GATEWAY_PORT=8080          # Au lieu de 80
POSTGRES_PORT=5434         # Au lieu de 5432
RABBITMQ_PORT=5673         # Au lieu de 5672
RABBITMQ_MANAGEMENT_PORT=15673  # Au lieu de 15672
```

### Ressources Docker

Modifier `docker-compose.yml` :

```yaml
services:
  identity-service:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## 🌐 Déploiement Production

### Option 1 : Docker Compose (Simple)

**Prérequis** :
- Serveur Linux (Ubuntu 22.04+ recommandé)
- Docker + Docker Compose installés
- Domaine configuré (ex: agricole.example.com)
- Certificat SSL (Let's Encrypt recommandé)

**Étapes** :

```bash
# 1. Sur le serveur
cd /opt
git clone <repo-url> application_agricole
cd application_agricole

# 2. Configuration production
cp .env.example .env
nano .env

# IMPORTANT: Changer TOUS les mots de passe
# ENVIRONMENT=production
# DEBUG=false

# 3. SSL/TLS (avec Let's Encrypt)
# Voir section SSL ci-dessous

# 4. Build et démarrage
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 5. Vérification
docker-compose ps
curl https://agricole.example.com/health
```

### Option 2 : Kubernetes (Recommandé pour scale)

**Prérequis** :
- Cluster Kubernetes (GKE, EKS, AKS, ou on-premise)
- kubectl configuré
- Helm 3

**Architecture K8s** :

```
├── Ingress Controller (Nginx/Traefik)
├── Services (LoadBalancer ou ClusterIP)
├── Deployments (1+ replicas par service)
├── ConfigMaps (configuration)
├── Secrets (mots de passe, JWT)
├── PersistentVolumeClaims (PostgreSQL, RabbitMQ, MinIO)
└── HorizontalPodAutoscaler (auto-scaling)
```

**Déploiement** :

```bash
# 1. Créer namespace
kubectl create namespace agricole-prod

# 2. Créer secrets
kubectl create secret generic db-secret \
  --from-literal=password=<postgres-password> \
  -n agricole-prod

kubectl create secret generic jwt-secret \
  --from-literal=key=<jwt-secret-key> \
  -n agricole-prod

# 3. Appliquer manifests
kubectl apply -f k8s/ -n agricole-prod

# 4. Vérifier
kubectl get pods -n agricole-prod
kubectl get svc -n agricole-prod
```

### Configuration SSL/TLS

#### Avec Let's Encrypt (gratuit)

```bash
# 1. Installer Certbot
sudo apt-get install certbot

# 2. Obtenir certificat
sudo certbot certonly --standalone \
  -d agricole.example.com \
  -d www.agricole.example.com

# 3. Configurer Nginx
# Éditer gateway/default.conf :

server {
    listen 443 ssl http2;
    server_name agricole.example.com;

    ssl_certificate /etc/letsencrypt/live/agricole.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agricole.example.com/privkey.pem;

    # SSL config moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... reste de la config
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name agricole.example.com;
    return 301 https://$server_name$request_uri;
}
```

#### Renouvellement auto

```bash
# Cron job pour renouvellement
sudo crontab -e

# Ajouter:
0 3 * * * certbot renew --quiet && docker-compose restart gateway
```

---

## 📊 Monitoring

### Health Checks

```bash
# Gateway
curl http://localhost/health

# Services individuels
curl http://localhost:8001/health  # Identity
curl http://localhost:8002/health  # Farm
curl http://localhost:8003/health  # Inventory
curl http://localhost:8004/health  # Sales
curl http://localhost:8005/health  # Accounting
curl http://localhost:8006/health  # Reporting
```

### Logs centralisés

**Option 1** : Logs dans Docker

```bash
# Voir tous les logs
docker-compose logs -f

# Exporter vers fichier
docker-compose logs > logs_$(date +%Y%m%d_%H%M%S).txt
```

**Option 2** : ELK Stack (Production)

```yaml
# Ajouter dans docker-compose.yml
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash/config:/usr/share/logstash/pipeline

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
```

### Métriques (Prometheus + Grafana)

À implémenter :

```yaml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

---

## 💾 Backup & Restauration

### Backup PostgreSQL

```bash
# Backup toutes les bases
docker-compose exec postgres pg_dumpall -U agricole_user > backup_all_$(date +%Y%m%d).sql

# Backup base spécifique
docker-compose exec postgres pg_dump -U agricole_user identity_db > backup_identity_$(date +%Y%m%d).sql

# Backup automatique (cron)
# Ajouter dans crontab:
0 2 * * * cd /opt/application_agricole && docker-compose exec -T postgres pg_dumpall -U agricole_user | gzip > /backups/postgres_$(date +\%Y\%m\%d).sql.gz
```

### Restauration PostgreSQL

```bash
# Restaurer toutes les bases
cat backup_all_20251231.sql | docker-compose exec -T postgres psql -U agricole_user

# Restaurer base spécifique
cat backup_identity_20251231.sql | docker-compose exec -T postgres psql -U agricole_user -d identity_db
```

### Backup MinIO (Rapports)

```bash
# Backup dossier MinIO
docker-compose exec minio mc mirror /data /backup

# Ou copier le volume
docker run --rm \
  -v application_agricole_minio_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/minio_$(date +%Y%m%d).tar.gz /data
```

### Backup RabbitMQ

```bash
# Exporter définitions
docker-compose exec rabbitmq rabbitmqadmin export backup_rabbitmq.json

# Importer
docker-compose exec rabbitmq rabbitmqadmin import backup_rabbitmq.json
```

---

## 🔧 Troubleshooting

### Services ne démarrent pas

```bash
# 1. Vérifier les logs
docker-compose logs

# 2. Vérifier les ressources
docker stats

# 3. Vérifier les ports
netstat -tulpn | grep -E '80|5432|5672|6379|9000'

# 4. Rebuild sans cache
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### PostgreSQL ne démarre pas

```bash
# Vérifier logs
docker-compose logs postgres

# Erreur de permissions
sudo chown -R 999:999 ./postgres_data/

# Reset complet
docker-compose down -v
docker-compose up -d postgres
```

### RabbitMQ erreurs

```bash
# Logs
docker-compose logs rabbitmq

# Reset
docker-compose down
docker volume rm application_agricole_rabbitmq_data
docker-compose up -d rabbitmq
```

### "Connection refused" sur API

```bash
# 1. Attendre 20-30 secondes (services en cours de démarrage)

# 2. Vérifier que tous les services sont UP
docker-compose ps

# 3. Vérifier health checks
curl http://localhost/health

# 4. Vérifier logs du service qui refuse
docker-compose logs identity-service
```

### Problèmes de mémoire

```bash
# Vérifier utilisation
docker stats

# Augmenter mémoire Docker Desktop
# Settings → Resources → Memory: 8 GB minimum

# Ou limiter par service dans docker-compose.yml
```

### Logs "too many open files"

```bash
# Linux: Augmenter limites
sudo sysctl -w fs.inotify.max_user_watches=524288
sudo sysctl -w fs.inotify.max_user_instances=512

# Permanent
echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.conf
```

---

## 📝 Checklist Déploiement Production

- [ ] Changer TOUS les mots de passe (.env)
- [ ] Générer JWT_SECRET_KEY aléatoire long
- [ ] Configurer SSL/TLS (Let's Encrypt)
- [ ] Configurer domaine DNS
- [ ] Configurer firewall (ufw/iptables)
- [ ] Activer backup automatique PostgreSQL
- [ ] Activer backup MinIO
- [ ] Configurer monitoring (Prometheus/Grafana)
- [ ] Configurer logs centralisés (ELK)
- [ ] Configurer alertes (erreurs, latence, disk)
- [ ] Tester restauration backup
- [ ] Documenter procédures d'urgence
- [ ] Configurer auto-scaling (si K8s)
- [ ] Tester DR (Disaster Recovery)

---

## 🆘 Support Urgence

### Redémarrage rapide

```bash
# Arrêt d'urgence
docker-compose down

# Redémarrage
docker-compose up -d

# Vérification
docker-compose ps
curl http://localhost/health
```

### Reset complet (perte de données!)

```bash
docker-compose down -v
docker system prune -a --volumes -f
docker-compose up --build -d
```

### Contacter support

1. Collecter logs: `docker-compose logs > logs.txt`
2. Collecter config: `docker-compose ps > status.txt`
3. Vérifier santé: `curl http://localhost/health`

---

**Version** : 1.0.0
**Dernière mise à jour** : 31 Décembre 2025
