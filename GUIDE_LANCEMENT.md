# 🚀 GUIDE DE LANCEMENT - APPLICATION AGRICOLE & ÉLEVAGE

## 🎯 Lancement Rapide (3 minutes)

### Étape 1 : Vérification des prérequis

```bash
# Vérifier Docker
docker --version
# Requis: Docker 20.10+

# Vérifier Docker Compose
docker-compose --version
# Requis: Docker Compose 2.0+

# Vérifier les ressources
docker info | grep "Total Memory"
# Requis: 8 GB minimum
```

### Étape 2 : Configuration

```bash
# Naviguer vers le projet
cd c:\LLM_agents_class\application_agricole

# Copier la configuration
cp .env.example .env

# La configuration par défaut fonctionne pour le développement
# Pour la production, éditer .env et changer les mots de passe
```

### Étape 3 : Démarrage

```bash
# Build et démarrage de TOUS les services (peut prendre 2-3 minutes)
docker-compose up --build -d

# OU avec Make
make build
make up
```

### Étape 4 : Vérification

```bash
# Voir l'état des services
docker-compose ps

# Tous les services doivent afficher "Up" et "healthy"
# Si certains sont "starting", attendre 20-30 secondes

# Test de santé
curl http://localhost/health
# Réponse attendue: "healthy"
```

### Étape 5 : Premier test

```bash
# Se connecter avec l'admin par défaut
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@2025"}'

# Vous devriez recevoir un access_token et refresh_token
```

## ✅ C'est tout! L'application est lancée

Accédez à :
- **API Gateway** : http://localhost
- **Documentation API** : http://localhost/docs
- **RabbitMQ Management** : http://localhost:15672 (agricole_rabbit / voir .env)
- **MinIO Console** : http://localhost:9001 (minio_admin / voir .env)

---

## 📖 Prochaines étapes

### 1. Explorer la documentation interactive

Ouvrez http://localhost/docs dans votre navigateur pour :
- Voir tous les endpoints disponibles
- Tester les APIs directement depuis le navigateur
- Voir les schémas de données

### 2. Créer vos premiers utilisateurs

```bash
# Récupérer le token admin (remplacer <ACCESS_TOKEN> ci-dessous)
TOKEN="<ACCESS_TOKEN_ICI>"

# Créer un gestionnaire
curl -X POST http://localhost/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "gestionnaire",
    "email": "gestionnaire@example.com",
    "password": "Gestionnaire@2025",
    "full_name": "Jean Gestionnaire",
    "role_ids": []
  }'
```

### 3. Créer votre première ferme

```bash
curl -X POST http://localhost/api/v1/farms \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "FERME001",
    "name": "Ma Première Ferme",
    "location": "Région Centre",
    "total_area": 10.0,
    "owner_name": "Propriétaire Test"
  }'
```

### 4. Créer des produits

```bash
curl -X POST http://localhost/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "MAIS001",
    "name": "Maïs",
    "product_type": "recolte",
    "unit": "kg",
    "min_stock_level": 100
  }'
```

### 5. Utiliser les scripts automatisés

```bash
# Initialiser des données de démonstration
bash scripts/init-default-data.sh

# Tester tous les endpoints
bash scripts/test-api.sh
```

---

## 🔑 Identifiants par défaut

### Utilisateur Administrateur
- **Username** : `admin`
- **Password** : `Admin@2025`
- **Rôle** : Administrateur (accès complet)

### RabbitMQ Management
- **URL** : http://localhost:15672
- **Username** : `agricole_rabbit`
- **Password** : Voir fichier `.env` (ligne `RABBITMQ_DEFAULT_PASS`)

### MinIO Console
- **URL** : http://localhost:9001
- **Username** : `minio_admin`
- **Password** : Voir fichier `.env` (ligne `MINIO_ROOT_PASSWORD`)

---

## 📊 Services disponibles

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| API Gateway | 80 | Point d'entrée unique | http://localhost/health |
| Identity | 8001 | Auth/Users/RBAC | http://localhost:8001/health |
| Farm | 8002 | Fermes/Parcelles | http://localhost:8002/health |
| Inventory | 8003 | Stock | http://localhost:8003/health |
| Sales | 8004 | Ventes | http://localhost:8004/health |
| Accounting | 8005 | Comptabilité/TVA | http://localhost:8005/health |
| Reporting | 8006 | Rapports PDF/Excel | http://localhost:8006/health |
| BFF Mobile | 8010 | Backend Mobile | http://localhost:8010/health |
| BFF Web | 8011 | Backend Web | http://localhost:8011/health |
| PostgreSQL | 5433 | Base de données | - |
| RabbitMQ | 5672 | Message broker | - |
| RabbitMQ Mgmt | 15672 | Interface RabbitMQ | http://localhost:15672 |
| Redis | 6380 | Cache | - |
| MinIO | 9000 | Stockage S3 | - |
| MinIO Console | 9001 | Interface MinIO | http://localhost:9001 |

---

## 📚 Documentation disponible

1. **[README.md](README.md)** - Documentation complète du projet
2. **[QUICKSTART.md](QUICKSTART.md)** - Démarrage rapide 5 minutes
3. **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)** - Architecture détaillée
4. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Guide de déploiement
5. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Résumé du projet
6. **[FILES_CREATED.md](FILES_CREATED.md)** - Liste des fichiers
7. **[CLAUDE.md](CLAUDE.md)** - Spécification d'architecture
8. **Ce fichier** - Guide de lancement

---

## 🛠️ Commandes utiles

### Gestion des services

```bash
# Voir l'état
docker-compose ps
# ou
make ps

# Voir les logs
docker-compose logs -f
# ou
make logs-f

# Redémarrer
docker-compose restart
# ou
make restart

# Arrêter
docker-compose down
# ou
make down

# Nettoyer (⚠️ SUPPRIME LES DONNÉES)
docker-compose down -v
# ou
make clean
```

### Logs d'un service spécifique

```bash
docker-compose logs -f identity-service
docker-compose logs -f inventory-service
docker-compose logs -f sales-service
```

### Accès aux bases de données

```bash
# PostgreSQL
docker exec -it agricole_postgres psql -U agricole_user -d identity_db

# Lister les bases
\l

# Se connecter à une base
\c inventory_db

# Lister les tables
\dt

# Quitter
\q
```

### Accès Redis

```bash
docker exec -it agricole_redis redis-cli -a <REDIS_PASSWORD>

# Voir toutes les clés
KEYS *

# Quitter
exit
```

---

## 🐛 Résolution de problèmes

### Les services ne démarrent pas

**Cause** : Ports déjà utilisés ou ressources insuffisantes

**Solution** :
```bash
# Vérifier les ports
netstat -ano | findstr ":80 :5432 :5672"

# Vérifier les ressources Docker
docker info

# Augmenter la mémoire Docker Desktop
# Settings → Resources → Memory: 8 GB minimum
```

### "Connection refused"

**Cause** : Services encore en cours de démarrage

**Solution** : Attendre 20-30 secondes
```bash
# Suivre les logs
docker-compose logs -f

# Vérifier que tous sont "Up"
docker-compose ps
```

### PostgreSQL ne démarre pas

**Cause** : Problème de permissions ou volume corrompu

**Solution** :
```bash
# Reset complet
docker-compose down -v
docker-compose up -d postgres
# Attendre 10 secondes
docker-compose logs postgres
```

### Token JWT expiré

**Cause** : Token a une durée de vie de 30 minutes

**Solution** : Se reconnecter
```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@2025"}'
```

---

## 🎓 Exemples d'utilisation

### Workflow complet : Créer une vente

```bash
# 1. S'authentifier
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@2025"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 2. Créer un client
CUSTOMER=$(curl -s -X POST http://localhost/api/v1/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "CLI001", "name": "Client Test", "classification": "retail"}')

CUSTOMER_ID=$(echo $CUSTOMER | grep -o '"id":"[^"]*' | cut -d'"' -f4)

# 3. Créer un produit
PRODUCT=$(curl -s -X POST http://localhost/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "PROD001", "name": "Produit Test", "product_type": "recolte", "unit": "kg", "unit_price": 100000}')

PRODUCT_ID=$(echo $PRODUCT | grep -o '"id":"[^"]*' | cut -d'"' -f4)

# 4. Ajouter du stock
curl -X POST http://localhost/api/v1/stock-movements \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"product_id\": \"$PRODUCT_ID\", \"movement_type\": \"entree\", \"quantity\": 100}"

# 5. Créer une vente
curl -X POST http://localhost/api/v1/sales \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_id\": \"$CUSTOMER_ID\",
    \"lines\": [{
      \"product_id\": \"$PRODUCT_ID\",
      \"quantity\": 10,
      \"unit_price\": 100000,
      \"tax_rate\": 19.25
    }],
    \"payment_method\": \"cash\"
  }"

# 6. Vérifier le stock
curl http://localhost/api/v1/stock-levels \
  -H "Authorization: Bearer $TOKEN"
```

### Générer un rapport

```bash
# Dashboard
curl http://localhost/w/dashboard \
  -H "Authorization: Bearer $TOKEN"

# Générer un rapport PDF
curl -X POST http://localhost/w/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "sales_summary",
    "format": "pdf",
    "filters": {}
  }'
```

---

## 🎉 Félicitations!

Votre application de gestion agricole et d'élevage est maintenant opérationnelle avec :

- ✅ 8 microservices fonctionnels
- ✅ API Gateway sécurisée
- ✅ Authentication JWT
- ✅ Base de données multi-services
- ✅ Message broker pour événements
- ✅ Stockage pour rapports PDF/Excel
- ✅ Documentation complète

**Bon développement! 🚜🌾**

---

**Pour toute question, consultez la documentation dans les fichiers .md du projet.**
