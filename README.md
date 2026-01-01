# APPLICATION AGRICOLE & ÉLEVAGE

Système de gestion agricole et d'élevage basé sur une architecture microservices.

## 📋 Vue d'ensemble

Application web et mobile pour la digitalisation de la gestion agricole et d'élevage avec :
- Gestion des fermes, parcelles et campagnes
- Gestion du stock (produits, mouvements)
- Gestion des ventes et paiements
- Comptabilité et TVA (19,25%)
- Rapports et exports (PDF/Excel)
- Authentification et gestion des utilisateurs (RBAC)

## 🏗️ Architecture

### Frontend
- **Web Application** (port 3001) : Application React/Next.js responsive (mobile, tablette, desktop)
  - Dashboard avec graphiques et statistiques
  - Gestion des exploitations, inventaire, ventes
  - Comptabilité et génération de rapports
  - Authentification JWT

### Microservices
- **Identity Service** (port 8001) : Authentification JWT, gestion des utilisateurs et rôles (RBAC)
- **Farm Service** (port 8002) : Gestion des fermes, parcelles, campagnes/saisons
- **Inventory Service** (port 8003) : Gestion du stock avec pattern append-only
- **Sales Service** (port 8004) : Ventes, clients, paiements (cash/mobile money)
- **Accounting Service** (port 8005) : Comptabilité, journal, TVA
- **Reporting Service** (port 8006) : Génération de rapports PDF/Excel, dashboards
- **BFF Mobile** (port 8010) : Backend-for-Frontend optimisé pour mobile (1 endpoint = 1 écran)
- **BFF Web** (port 8011) : Backend-for-Frontend pour le back-office web
- **API Gateway** (port 80) : Point d'entrée unique avec Nginx (rate limiting, routing)

### Infrastructure
- **PostgreSQL** (port 5433) : 6 bases de données (une par service)
- **RabbitMQ** (ports 5672, 15672) : Message broker pour événements asynchrones (pattern Saga)
- **Redis** (port 6380) : Cache et sessions
- **MinIO** (ports 9000, 9001) : Stockage S3-compatible pour les exports PDF/Excel

## 🚀 Guide de lancement

### Prérequis
- Docker et Docker Compose installés
- 8 GB RAM minimum
- Ports disponibles : 80, 5433, 5672, 6380, 9000, 9001, 15672, 8001-8006, 8010-8011

### Installation rapide

1. **Cloner et naviguer vers le projet**
```bash
cd c:\LLM_agents_class\application_agricole
```

2. **Configuration de l'environnement**
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env et personnaliser les mots de passe (IMPORTANT pour production)
# Les valeurs par défaut fonctionnent pour le développement
```

3. **Lancer l'application**
```bash
# Build et démarrage de tous les services
docker-compose up --build -d

# Ou avec Make
make setup
make build
make up
```

4. **Vérifier le statut**
```bash
# Voir les services en cours d'exécution (14 conteneurs attendus)
docker-compose ps

# Ou
make ps

# Suivre les logs
docker-compose logs -f

# Ou
make logs-f
```

5. **Accéder à l'application**

**🌐 Application Web (Interface principale)**
```
http://localhost
```
ou directement:
```
http://localhost:3001
```

**Identifiants par défaut:**
- Username: `admin`
- Password: `Admin@2025`

**Pages disponibles:**
- `/` - Redirection automatique
- `/login` - Connexion
- `/dashboard` - Tableau de bord avec graphiques
- `/farms` - Gestion des exploitations
- `/inventory` - Gestion de l'inventaire
- `/sales` - Gestion des ventes
- `/accounting` - Comptabilité
- `/reports` - Rapports PDF/Excel

### Autres interfaces

**API Documentation (Swagger)**
```
http://localhost/docs
```

**Interfaces d'administration**
- **RabbitMQ Management** : http://localhost:15672 (user: agricole_rabbit / voir .env)
- **MinIO Console** : http://localhost:9001 (user: minio_admin / voir .env)

### Premier utilisateur

Un utilisateur admin est créé automatiquement au démarrage du service Identity :
- **Username** : `admin`
- **Password** : `Admin@2025`
- **Rôle** : Administrateur (accès complet)

### Rôles disponibles

1. **admin** : Accès complet au système
2. **gestionnaire** : Gestion opérationnelle (pas de gestion utilisateurs)
3. **agent_terrain** : Saisie des données terrain (fermes, opérations)
4. **comptable** : Gestion comptabilité et TVA

## 📖 Utilisation de l'API

### Authentification

1. **Se connecter**
```bash
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@2025"
  }'
```

Réponse :
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {...}
}
```

2. **Utiliser le token**
```bash
# Ajouter le header Authorization pour toutes les requêtes
curl -X GET http://localhost/api/v1/users/me \
  -H "Authorization: Bearer <access_token>"
```

### API Mobile (BFF Mobile)

Endpoints optimisés pour le mobile (1 appel = 1 écran) :

```bash
# Écran d'accueil mobile
GET /m/home

# Détails d'une parcelle
GET /m/plot/{plot_id}/overview

# Produits en stock bas
GET /m/inventory/low-stock

# Créer une vente rapidement
POST /m/sales/quick-create

# Synchronisation offline
GET /m/sync/pull?since=2025-01-01T00:00:00Z
POST /m/sync/push
```

### API Web (BFF Web)

Endpoints pour le back-office web :

```bash
# Dashboard complet
GET /w/dashboard

# Vue d'ensemble du stock
GET /w/inventory/overview

# Analytiques des ventes
GET /w/sales/analytics?start_date=2025-01-01&end_date=2025-12-31

# Vue comptable
GET /w/accounting/overview

# Gestion des utilisateurs
GET /w/users/management

# Générer un rapport
POST /w/reports/generate
```

### Exemples complets

**Créer un produit**
```bash
curl -X POST http://localhost/api/v1/products \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "MAI001",
    "name": "Maïs Blanc",
    "product_type": "recolte",
    "unit": "kg",
    "min_stock_level": 100,
    "unit_price": 50000
  }'
```

**Créer un mouvement de stock**
```bash
curl -X POST http://localhost/api/v1/stock-movements \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "<product_uuid>",
    "movement_type": "entree",
    "quantity": 500,
    "reference_type": "harvest",
    "notes": "Récolte parcelle A",
    "location": "Entrepôt principal"
  }'
```

**Créer une vente**
```bash
curl -X POST http://localhost/api/v1/sales \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "<customer_uuid>",
    "lines": [
      {
        "product_id": "<product_uuid>",
        "product_code": "MAI001",
        "product_name": "Maïs Blanc",
        "quantity": 50,
        "unit_price": 50000,
        "tax_rate": 19.25
      }
    ],
    "payment_method": "cash",
    "notes": "Vente comptant"
  }'
```

## 🔧 Commandes utiles

```bash
# Arrêter tous les services
docker-compose down
# ou
make down

# Redémarrer
docker-compose restart
# ou
make restart

# Voir les logs d'un service spécifique
docker-compose logs -f identity-service

# Nettoyer tout (ATTENTION : supprime les données)
docker-compose down -v
# ou
make clean

# Reconstruire un service spécifique
docker-compose build identity-service
docker-compose up -d identity-service
```

## 🧪 Tests et développement

### Accès aux bases de données

```bash
# Se connecter à PostgreSQL
docker exec -it agricole_postgres psql -U agricole_user -d identity_db

# Lister les bases
\l

# Se connecter à une base spécifique
\c inventory_db

# Lister les tables
\dt
```

### Monitoring

- **RabbitMQ** : http://localhost:15672 - Voir les queues et les événements
- **MinIO** : http://localhost:9001 - Voir les fichiers générés (rapports)
- **Logs structurés** : Tous les services utilisent des logs JSON pour faciliter le parsing

## 📊 Pattern événementiel (Saga)

### Flux d'une vente

1. Client crée une vente (status: PENDING)
2. Sales Service publie événement `sale.created`
3. Inventory Service consomme et décrémente le stock → publie `stock.decremented`
4. Accounting Service consomme et crée les écritures → publie `ledger.posted`
5. Sales Service consomme les deux événements → met à jour status à CONFIRMED
6. Si échec stock → status REJECTED

### Idempotence

Tous les événements et actions critiques supportent l'idempotence via :
- `idempotency_key` pour éviter les doublons
- `event_id` unique pour chaque événement
- Pattern append-only pour stock et comptabilité

## 🔒 Sécurité

- JWT avec access token (30 min) et refresh token (7 jours)
- RBAC (Role-Based Access Control) avec 4 rôles prédéfinis
- Rate limiting au niveau du gateway (5 requêtes/min pour auth, 10/s pour le reste)
- Secrets externalisés dans .env
- Headers de sécurité (X-Frame-Options, X-Content-Type-Options, etc.)

## 📝 Structure du projet

```
application_agricole/
├── docker-compose.yml          # Orchestration de tous les services
├── .env.example                # Configuration exemple
├── Makefile                    # Commandes pratiques
├── CLAUDE.md                   # Spécification d'architecture
├── infrastructure/             # Scripts d'infrastructure
│   └── init-databases.sh      # Création des bases PostgreSQL
├── shared/                     # Code partagé entre services
│   ├── database.py            # Configuration base de données
│   ├── auth.py                # JWT et RBAC
│   ├── events.py              # Event publisher/consumer
│   └── logging_config.py      # Logs structurés
├── services/                   # Microservices
│   ├── identity/              # Service d'authentification
│   ├── farm/                  # Service fermes/parcelles
│   ├── inventory/             # Service stock
│   ├── sales/                 # Service ventes
│   ├── accounting/            # Service comptabilité
│   ├── reporting/             # Service rapports
│   ├── bff-mobile/            # BFF pour mobile
│   └── bff-web/               # BFF pour web
└── gateway/                    # API Gateway (Nginx)
    ├── nginx.conf
    └── default.conf
```

## 🐛 Troubleshooting

### Les services ne démarrent pas

```bash
# Vérifier les logs
docker-compose logs

# Vérifier que les ports ne sont pas occupés
netstat -ano | findstr :80
netstat -ano | findstr :5433

# Nettoyer et redémarrer
docker-compose down -v
docker-compose up --build
```

### Erreur de connexion à la base de données

```bash
# Attendre que PostgreSQL soit prêt (peut prendre 10-20 secondes)
docker-compose logs postgres

# Vérifier la santé
docker-compose ps
```

### RabbitMQ ne démarre pas

```bash
# Nettoyer les données RabbitMQ
docker-compose down
docker volume rm application_agricole_rabbitmq_data
docker-compose up -d rabbitmq
```

## 📚 Documentation technique

- **Architecture détaillée** : Voir [CLAUDE.md](CLAUDE.md)
- **API Documentation** : http://localhost/docs (Swagger UI automatique)
- **Pattern Outbox** : Implémenté dans shared/events.py
- **Migrations DB** : Alembic (à venir pour chaque service)

## 🎯 Roadmap / Évolutions futures

- [ ] Service Crop Operations (itinéraires techniques)
- [ ] Service Livestock (élevage)
- [ ] Service Procurement (achats fournisseurs)
- [ ] Service Sync (synchronisation offline avancée)
- [ ] Service Notifications (email/SMS/WhatsApp)
- [ ] Observabilité complète (Prometheus + Grafana)
- [ ] Tests automatisés (pytest)
- [ ] CI/CD (GitHub Actions)
- [ ] Déploiement Kubernetes

## 📄 Licence

Projet de formation - LLM Agents Class

## 👥 Support

Pour toute question ou problème, consulter :
1. Ce README
2. La documentation dans CLAUDE.md
3. Les logs des services
4. L'API documentation (Swagger)
