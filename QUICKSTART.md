# 🚀 GUIDE DE DÉMARRAGE RAPIDE

Guide pas-à-pas pour lancer l'application Agricole & Élevage en 5 minutes.

## ⚡ Installation Express (3 commandes)

```bash
# 1. Copier la configuration
cp .env.example .env

# 2. Construire et démarrer
docker-compose up --build -d

# 3. Vérifier que tout fonctionne
docker-compose ps
```

C'est tout! L'application est maintenant accessible sur http://localhost

## 📋 Vérifications Post-Installation

### 1. Tous les services sont-ils démarrés ?

```bash
docker-compose ps
```

Vous devriez voir tous ces services avec l'état "Up" :
- `agricole_postgres`
- `agricole_rabbitmq`
- `agricole_redis`
- `agricole_minio`
- `agricole_identity_service`
- `agricole_farm_service`
- `agricole_inventory_service`
- `agricole_sales_service`
- `agricole_accounting_service`
- `agricole_reporting_service`
- `agricole_bff_mobile`
- `agricole_bff_web`
- `agricole_gateway`

### 2. L'API Gateway répond-il ?

```bash
curl http://localhost/health
```

Réponse attendue : `healthy`

### 3. Peut-on se connecter ?

```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "ADMIN_PASSWORD"}'
```

Si vous recevez un `access_token`, tout fonctionne! 🎉

## 🎯 Premiers pas avec l'API

### Étape 1 : S'authentifier

```bash
# Connexion
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "ADMIN_PASSWORD"}' \
  > login_response.json

# Extraire le token (sur Linux/Mac)
TOKEN=$(cat login_response.json | jq -r '.access_token')

# Ou copiez manuellement le access_token depuis login_response.json
```

### Étape 2 : Obtenir les informations utilisateur

```bash
curl http://localhost/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

### Étape 3 : Créer votre première ferme

```bash
curl -X POST http://localhost/api/v1/farms \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "FARM001",
    "name": "Ferme Modèle",
    "location": "Région Centre",
    "total_area": 10.5,
    "owner_name": "Jean Cultivateur",
    "owner_phone": "+225 01 02 03 04 05"
  }'
```

### Étape 4 : Créer un produit

```bash
curl -X POST http://localhost/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "PROD001",
    "name": "Maïs",
    "product_type": "recolte",
    "unit": "kg",
    "min_stock_level": 100,
    "unit_price": 50000
  }'
```

### Étape 5 : Ajouter du stock

```bash
# Remplacer <PRODUCT_UUID> par l'UUID retourné à l'étape 4
curl -X POST http://localhost/api/v1/stock-movements \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "<PRODUCT_UUID>",
    "movement_type": "entree",
    "quantity": 1000,
    "notes": "Stock initial",
    "location": "Entrepôt principal"
  }'
```

### Étape 6 : Voir le niveau de stock

```bash
curl http://localhost/api/v1/stock-levels \
  -H "Authorization: Bearer $TOKEN"
```

## 🖥️ Interfaces d'administration

### RabbitMQ Management Console
- URL : http://localhost:15672
- Username : `agricole_rabbit` (ou valeur dans .env)
- Password : voir fichier `.env`
- Utilisé pour : Monitorer les événements et queues

### MinIO Console
- URL : http://localhost:9001
- Username : `minio_admin` (ou valeur dans .env)
- Password : voir fichier `.env`
- Utilisé pour : Voir les rapports PDF/Excel générés

### API Documentation (Swagger)
- URL : http://localhost/docs
- Documentation interactive de toutes les APIs

## 🔧 Commandes utiles

### Voir les logs en temps réel

```bash
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f identity-service
docker-compose logs -f inventory-service
```

### Redémarrer un service

```bash
docker-compose restart identity-service
```

### Arrêter tout

```bash
docker-compose down
```

### Redémarrer tout

```bash
docker-compose down
docker-compose up -d
```

### Nettoyer complètement (⚠️ ATTENTION : supprime les données)

```bash
docker-compose down -v
```

## 📱 Tester l'API Mobile (BFF)

```bash
# Dashboard mobile
curl http://localhost/m/home \
  -H "Authorization: Bearer $TOKEN"

# Produits en rupture
curl http://localhost/m/inventory/low-stock \
  -H "Authorization: Bearer $TOKEN"
```

## 💻 Tester l'API Web (BFF)

```bash
# Dashboard complet
curl http://localhost/w/dashboard \
  -H "Authorization: Bearer $TOKEN"

# Vue d'ensemble du stock
curl http://localhost/w/inventory/overview \
  -H "Authorization: Bearer $TOKEN"
```

## 🐛 Problèmes courants

### "Connection refused" ou "Service unavailable"

**Solution** : Les services mettent 20-30 secondes à démarrer complètement.

```bash
# Vérifier l'état
docker-compose ps

# Attendre que tous les services soient "healthy"
# Vous pouvez suivre le démarrage avec :
docker-compose logs -f
```

### "Cannot connect to database"

**Solution** : PostgreSQL n'est pas encore prêt.

```bash
# Vérifier PostgreSQL
docker-compose logs postgres

# Attendre le message "database system is ready to accept connections"
```

### Token JWT expiré

**Solution** : Se reconnecter pour obtenir un nouveau token.

```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "ADMIN_PASSWORD"}'
```

### Port déjà utilisé

**Solution** : Modifier les ports dans `.env` ou arrêter le service qui utilise le port.

```bash
# Voir quel processus utilise le port 80
netstat -ano | findstr :80

# Ou modifier GATEWAY_PORT dans .env
```

## 📚 Documentation complète

Pour aller plus loin, consultez :
- **[README.md](README.md)** - Documentation complète
- **[CLAUDE.md](CLAUDE.md)** - Spécification d'architecture détaillée
- **http://localhost/docs** - Documentation interactive des APIs

## ✅ Checklist de démarrage

- [ ] Docker et Docker Compose installés
- [ ] Fichier `.env` créé (copie de `.env.example`)
- [ ] `docker-compose up --build -d` exécuté
- [ ] Tous les services affichent "Up" dans `docker-compose ps`
- [ ] `curl http://localhost/health` retourne "healthy"
- [ ] Connexion réussie avec admin/ADMIN_PASSWORD
- [ ] Première ferme créée
- [ ] Premier produit créé
- [ ] Premier mouvement de stock enregistré

Félicitations! Vous êtes prêt à utiliser l'application. 🎊

## 🎓 Prochaines étapes

1. Créer des utilisateurs avec différents rôles
2. Créer des parcelles liées aux fermes
3. Enregistrer des saisons/campagnes
4. Créer des clients
5. Enregistrer des ventes
6. Générer des rapports comptables et TVA
7. Exporter des rapports PDF/Excel

Bon développement! 🚜🌾
