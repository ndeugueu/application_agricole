# Guide de Lancement - Application Agricole Complète

## 🎯 Vue d'ensemble

Application complète de gestion agricole et d'élevage avec:
- **Backend**: 8 microservices Python/FastAPI
- **Frontend**: Application web React/Next.js responsive
- **Infrastructure**: PostgreSQL, RabbitMQ, Redis, MinIO
- **Gateway**: Nginx reverse proxy

## 📋 Prérequis

- Docker Desktop installé et démarré
- Docker Compose v2.0+
- 8 Go RAM minimum
- 10 Go espace disque disponible

**Pour Windows**: Assurez-vous que Docker Desktop est bien démarré et que WSL2 est configuré.

## 🚀 Lancement rapide (5 minutes)

### 1. Vérifier l'environnement

```bash
# Vérifier Docker
docker --version
docker-compose --version

# Vérifier que Docker est démarré
docker ps
```

### 2. Démarrer l'application

```bash
# Depuis le dossier racine du projet
cd c:\LLM_agents_class\application_agricole

# Construire et démarrer tous les services
docker-compose up --build -d
```

### 3. Attendre que tout démarre (2-3 minutes)

```bash
# Voir les logs en temps réel
docker-compose logs -f

# Vérifier que tous les conteneurs sont "healthy" ou "running"
docker-compose ps
```

Vous devriez voir **14 conteneurs**:
- ✅ postgres
- ✅ rabbitmq
- ✅ redis
- ✅ minio
- ✅ identity-service
- ✅ farm-service
- ✅ inventory-service
- ✅ sales-service
- ✅ accounting-service
- ✅ reporting-service
- ✅ bff-mobile
- ✅ bff-web
- ✅ frontend
- ✅ gateway

### 4. Accéder à l'application

**🌐 Frontend Web (Principal)**
```
http://localhost
```
ou
```
http://localhost:3001
```

**Identifiants par défaut:**
- Username: `admin`
- Password: `Admin@2025`

## 📱 Interfaces disponibles

### Application Web (Frontend)
- **URL**: http://localhost ou http://localhost:3001
- **Pages disponibles**:
  - `/` - Redirection auto vers dashboard ou login
  - `/login` - Connexion
  - `/dashboard` - Tableau de bord avec graphiques
  - `/farms` - Gestion des exploitations
  - `/inventory` - Gestion de l'inventaire
  - `/sales` - Gestion des ventes
  - `/accounting` - Comptabilité
  - `/reports` - Génération de rapports PDF/Excel

### API Gateway
- **URL**: http://localhost
- **Routes**:
  - `/api/v1/auth/*` - Authentification
  - `/w/*` - Web BFF API
  - `/m/*` - Mobile BFF API
  - `/docs` - Documentation API Swagger

### Interfaces d'administration

**RabbitMQ Management**
```
http://localhost:15672
Username: agricole_rabbit
Password: rabbit_secure_password_2025
```

**MinIO Console**
```
http://localhost:9001
Username: minio_admin
Password: minio_secure_password_2025
```

**PostgreSQL**
```
Host: localhost
Port: 5433
Username: agricole_user
Password: agricole_secure_password_2025
Databases: identity_db, farm_db, inventory_db, sales_db, accounting_db, reporting_db
```

## 🎨 Utilisation du Frontend

### Première connexion

1. Ouvrir http://localhost dans votre navigateur
2. Vous serez redirigé vers `/login`
3. Entrer les identifiants:
   - Username: `admin`
   - Password: `Admin@2025`
4. Cliquer sur "Se connecter"
5. Vous serez redirigé vers le dashboard

### Navigation

L'interface est **entièrement responsive** et fonctionne sur:
- 💻 Desktop
- 📱 Mobile
- 📱 Tablette

**Sur mobile**: Cliquez sur l'icône menu (☰) en haut à gauche pour ouvrir la sidebar.

### Fonctionnalités principales

#### 📊 Dashboard
- Vue d'ensemble du chiffre d'affaires
- Graphiques de ventes mensuelles
- État de l'inventaire (pie chart)
- Top produits vendus
- Actions rapides

#### 🌾 Exploitations
- Créer une nouvelle exploitation
- Modifier les informations
- Voir les détails (surface, localisation)
- Supprimer une exploitation

#### 📦 Inventaire
- Ajouter des produits (céréales, légumes, fruits, bétail, etc.)
- Gérer les entrées/sorties de stock
- Alertes stock faible (badge rouge)
- Visualiser le stock en temps réel

#### 💰 Ventes
- Consulter l'historique des ventes
- Voir les détails de chaque vente
- Statut des paiements
- Montants HT/TVA/TTC

#### 📊 Comptabilité
- Écritures comptables (débit/crédit)
- Soldes des comptes
- TVA automatique à 19.25%

#### 📄 Rapports
- Générer des rapports (Ventes, Inventaire, Comptabilité)
- Télécharger en PDF
- Exporter en Excel
- Historique des rapports générés

## 🛠️ Commandes utiles

### Voir les logs

```bash
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f frontend
docker-compose logs -f identity-service
docker-compose logs -f gateway
```

### Redémarrer un service

```bash
# Redémarrer le frontend
docker-compose restart frontend

# Redémarrer le gateway
docker-compose restart gateway

# Redémarrer tous les services
docker-compose restart
```

### Arrêter l'application

```bash
# Arrêter tous les services
docker-compose down

# Arrêter et supprimer les volumes (⚠️ perte de données)
docker-compose down -v
```

### Reconstruire après modification

```bash
# Reconstruire tous les services
docker-compose up --build -d

# Reconstruire un service spécifique
docker-compose up --build -d frontend
```

## 🔧 Résolution de problèmes

### Le frontend ne se charge pas

1. Vérifier que le conteneur est démarré:
```bash
docker-compose ps frontend
```

2. Voir les logs:
```bash
docker-compose logs frontend
```

3. Redémarrer:
```bash
docker-compose restart frontend gateway
```

### Erreur "port already allocated" pour PostgreSQL

Le port 5433 est déjà configuré dans `.env`. Si vous avez toujours l'erreur:

```bash
# Arrêter le service qui utilise le port
# Ou changer le port dans .env
POSTGRES_PORT=5434
```

Puis redémarrer:
```bash
docker-compose down
docker-compose up -d
```

### Erreur 502 Bad Gateway

Cela signifie qu'un service backend n'est pas prêt. Attendre 1-2 minutes que tous les services démarrent:

```bash
# Vérifier l'état
docker-compose ps

# Voir les logs
docker-compose logs -f
```

### Page blanche sur le frontend

1. Vérifier les logs du navigateur (F12 > Console)
2. Vérifier que l'API Gateway est accessible:
```bash
curl http://localhost/api/v1/auth/health
```

3. Vérifier les variables d'environnement du frontend:
```bash
docker-compose exec frontend env | grep NEXT_PUBLIC
```

### Problème de connexion (login)

1. Vérifier que le service identity est démarré:
```bash
docker-compose logs identity-service
```

2. Vérifier que la base de données est prête:
```bash
docker-compose exec postgres psql -U agricole_user -d identity_db -c "SELECT COUNT(*) FROM users;"
```

3. Utiliser les bons identifiants:
   - Username: `admin` (pas Admin ou ADMIN)
   - Password: `Admin@2025`

## 📊 Monitoring

### Vérifier la santé des services

```bash
# Via API Gateway
curl http://localhost/health

# Via Docker
docker-compose ps

# Statistiques ressources
docker stats
```

### Métriques

- **RabbitMQ**: http://localhost:15672 (voir les messages, queues, etc.)
- **MinIO**: http://localhost:9001 (voir les fichiers stockés)

## 🔒 Sécurité

### En développement

Les mots de passe par défaut sont dans `.env`. **Ne pas utiliser en production!**

### En production

1. Changer tous les mots de passe dans `.env`
2. Utiliser HTTPS (certificat SSL)
3. Configurer un firewall
4. Limiter l'accès aux ports d'administration
5. Activer l'authentification forte

## 📦 Architecture des conteneurs

```
┌─────────────────────────────────────────────────┐
│              Nginx Gateway :80                  │
│         (Reverse Proxy & Load Balancer)         │
└────────────┬────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐      ┌──────────────┐
│Frontend │      │   Backend    │
│Next.js  │      │ Microservices│
│  :3001  │      │              │
└─────────┘      └──────┬───────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
    ┌────────┐    ┌──────────┐   ┌────────┐
    │Postgres│    │RabbitMQ  │   │ Redis  │
    │  :5433 │    │:5672/15672   │ :6380  │
    └────────┘    └──────────┘   └────────┘
```

## 🎓 Premiers pas recommandés

1. **Se connecter** sur http://localhost avec admin/Admin@2025
2. **Explorer le dashboard** pour voir les graphiques
3. **Créer une exploitation** dans /farms
4. **Ajouter des produits** dans /inventory
5. **Faire des entrées de stock**
6. **Générer un rapport** dans /reports

## 📞 Support

Pour signaler un bug ou demander de l'aide:
- Consulter les logs: `docker-compose logs`
- Vérifier l'état: `docker-compose ps`
- Redémarrer si nécessaire: `docker-compose restart`

## ✅ Checklist de démarrage

- [ ] Docker Desktop démarré
- [ ] Exécuté `docker-compose up --build -d`
- [ ] Attendu 2-3 minutes
- [ ] Tous les conteneurs sont "running"
- [ ] Ouvert http://localhost
- [ ] Connecté avec admin/Admin@2025
- [ ] Dashboard affiché correctement

**Bon usage! 🚀**
