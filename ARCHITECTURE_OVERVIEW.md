# 📐 ARCHITECTURE OVERVIEW - Application Agricole & Élevage

Document de synthèse de l'architecture microservices mise en place.

## 🎯 Vue d'ensemble

Architecture **microservices modulaire** basée sur les principes du **Domain-Driven Design (DDD)** avec communication événementielle pour garantir la cohérence des données.

### Principes clés

1. **Database-per-Service** : Chaque service possède sa propre base de données
2. **Event-Driven** : Communication asynchrone via RabbitMQ (pattern Saga)
3. **Append-Only** : Stock et comptabilité en mode immuable (audit trail complet)
4. **BFF Pattern** : Backends dédiés pour Mobile et Web
5. **API Gateway** : Point d'entrée unique avec rate limiting et routing

## 📊 Diagramme d'architecture

```
                                 ┌─────────────────┐
                                 │  Mobile Client  │
                                 └────────┬────────┘
                                          │
                                 ┌────────▼────────┐
                                 │   Web Client    │
                                 └────────┬────────┘
                                          │
                    ┌─────────────────────▼─────────────────────┐
                    │         API Gateway (Nginx)               │
                    │  - Rate limiting                          │
                    │  - TLS termination                        │
                    │  - Routing                                │
                    └──┬────────────────────────────────────┬───┘
                       │                                    │
         ┌─────────────▼──────────┐            ┌──────────▼────────────┐
         │    BFF Mobile          │            │     BFF Web           │
         │  - 1 endpoint = 1 écran│            │  - Dashboards         │
         │  - Optimisé réseau     │            │  - Admin features     │
         └──┬──────────────────┬──┘            └──┬────────────────┬───┘
            │                  │                  │                │
    ┌───────▼──────┐  ┌────────▼────────┐  ┌─────▼──────┐  ┌──────▼──────┐
    │  Identity    │  │     Farm        │  │ Inventory  │  │   Sales     │
    │  Service     │  │   Service       │  │  Service   │  │  Service    │
    └───────┬──────┘  └────────┬────────┘  └─────┬──────┘  └──────┬──────┘
            │                  │                  │                │
         ┌──▼──────────────────▼──────────────────▼────────────────▼───┐
         │                    RabbitMQ (Event Bus)                     │
         │  - sale.created, stock.decremented, ledger.posted, etc.    │
         └──┬──────────────────┬──────────────────┬────────────────┬───┘
            │                  │                  │                │
    ┌───────▼──────┐  ┌────────▼────────┐  ┌─────▼──────┐  ┌──────▼──────┐
    │ Accounting   │  │   Reporting     │  │   Redis    │  │  MinIO      │
    │  Service     │  │    Service      │  │  (Cache)   │  │ (Storage)   │
    └───────┬──────┘  └────────┬────────┘  └────────────┘  └─────────────┘
            │                  │
         ┌──▼──────────────────▼──────────────────────────────────────────┐
         │              PostgreSQL (6 databases)                          │
         │  identity_db | farm_db | inventory_db | sales_db | etc.       │
         └────────────────────────────────────────────────────────────────┘
```

## 🏗️ Microservices détaillés

### 1. Identity & Access Service (Port 8001)

**Responsabilité** : Authentification, autorisation, gestion des utilisateurs

**Technologies** :
- FastAPI
- PostgreSQL (identity_db)
- JWT (access + refresh tokens)
- BCrypt pour hash des mots de passe

**Fonctionnalités** :
- Login/Logout
- Gestion des utilisateurs (CRUD)
- RBAC (4 rôles : Admin, Gestionnaire, Agent terrain, Comptable)
- Gestion des permissions granulaires
- Rotation des refresh tokens

**Modèle de données** :
- `users` : Utilisateurs avec hash de mot de passe
- `roles` : Rôles système
- `permissions` : Permissions granulaires (resource + action)
- `user_roles` : Association many-to-many
- `role_permissions` : Association many-to-many
- `refresh_tokens` : Tokens de rafraîchissement

### 2. Farm Service (Port 8002)

**Responsabilité** : Gestion des fermes, parcelles, saisons/campagnes

**Modèle de données** :
- `farms` : Fermes avec localisation, superficie, propriétaire
- `plots` : Parcelles avec type de sol, irrigation
- `seasons` : Campagnes/saisons agricoles
- `crop_types` : Référentiel des types de cultures

**Événements publiés** :
- `farm.created`
- `plot.created`
- `season.created`

### 3. Inventory Service (Port 8003)

**Responsabilité** : Gestion du stock avec pattern append-only

**Pattern clé** : **Append-Only Ledger**
- Les mouvements de stock ne sont JAMAIS modifiés ou supprimés
- Corrections via nouveaux mouvements d'ajustement
- Garantit un audit trail complet

**Modèle de données** :
- `products` : Catalogue produits (intrants, récoltes, produits transformés)
- `stock_movements` : Journal des mouvements (ENTREE, SORTIE, AJUSTEMENT)
- Pas de table "stock_levels" → calculé en temps réel depuis les mouvements

**Événements** :
- Publie : `stock.entree`, `stock.sortie`, `stock.decremented`, `stock.failed`
- Consomme : `sale.created` (pour décrémenter automatiquement)

**Calcul du stock** :
```sql
SELECT SUM(quantity) FROM stock_movements WHERE product_id = ?
```

### 4. Sales Service (Port 8004)

**Responsabilité** : Gestion des ventes avec pattern Saga

**Pattern clé** : **Event-Driven Saga**

Flux d'une vente :
1. Client crée vente → status = PENDING
2. Service publie `sale.created`
3. Inventory Service décrémente stock → publie `stock.decremented`
4. Accounting Service crée écriture → publie `ledger.posted`
5. Sales Service met à jour status → CONFIRMED ou REJECTED

**Modèle de données** :
- `customers` : Clients (wholesale/retail/individual)
- `sales` : Ventes avec statut (PENDING/CONFIRMED/REJECTED)
- `sale_lines` : Lignes de vente avec TVA
- `payments` : Paiements (cash, mobile_money, bank_transfer)

**Idempotence** :
- `correlation_id` pour tracer la transaction
- `idempotency_key` pour éviter doublons

### 5. Accounting & Tax Service (Port 8005)

**Responsabilité** : Comptabilité double-partie et TVA (19,25%)

**Pattern clé** : **Append-Only Ledger** + **Double-Entry Bookkeeping**

**Modèle de données** :
- `accounts` : Plan comptable avec hiérarchie
- `ledger_entries` : Journal général (immuable)
- `tax_records` : Enregistrements TVA (collectée/déductible)

**Montants** : Stockés en **entiers** (FCFA cents) pour éviter problèmes de précision float

**Calcul TVA** :
```
TVA = (montant_base × 1925) ÷ 10000
Montant TTC = montant_base + TVA
```

**Événements** :
- Consomme : `sale.created` → crée TVA collectée
- Consomme : `purchase.received` → crée TVA déductible
- Publie : `ledger.posted`, `tax.tva_collectee`, `tax.tva_deductible`

**Rapports** :
- État mensuel TVA (collectée - déductible)
- Balance de vérification (trial balance)
- Journal général

### 6. Reporting Service (Port 8006)

**Responsabilité** : Génération de rapports PDF/Excel, dashboards

**Technologies** :
- WeasyPrint pour PDF
- OpenPyXL pour Excel
- MinIO pour stockage S3-compatible

**Fonctionnalités** :
- Génération asynchrone de rapports
- Stockage dans MinIO avec expiration (30 jours)
- Dashboards temps réel (agrégation de données)

**Types de rapports** :
- Résumé des ventes
- État du stock
- TVA mensuelle
- Balance de vérification
- Dashboards personnalisés

### 7. BFF Mobile (Port 8010)

**Responsabilité** : Agrégation pour mobile

**Pattern** : **1 endpoint = 1 écran mobile**

**Avantages** :
- Réduit le nombre d'appels réseau (critique sur mobile)
- Optimise la bande passante
- Simplifie le code mobile

**Endpoints** :
- `GET /m/home` → Dashboard mobile (1 appel au lieu de 5+)
- `GET /m/plot/{id}/overview` → Toutes les données d'une parcelle
- `POST /m/sync/push` → Synchronisation offline

### 8. BFF Web (Port 8011)

**Responsabilité** : Agrégation pour back-office web

**Endpoints** :
- `GET /w/dashboard` → Dashboard complet avec graphiques
- `GET /w/inventory/overview` → Vue d'ensemble stock
- `GET /w/accounting/overview` → Vue comptable complète

### 9. API Gateway (Port 80)

**Responsabilité** : Reverse proxy, rate limiting, routing

**Technologies** : Nginx

**Fonctionnalités** :
- Rate limiting (5 req/min pour auth, 10 req/s pour général)
- Routing vers les BFF
- Compression Gzip
- Headers de sécurité
- TLS termination (à configurer en production)

**Routes** :
- `/api/v1/auth/*` → Identity Service
- `/m/*` → BFF Mobile
- `/w/*` → BFF Web

## 🔄 Communication entre services

### Synchrone (REST/HTTP)

Utilisé pour :
- Authentification (critique, doit être immédiat)
- Requêtes de lecture simple
- BFF → Services backend

**Timeouts** :
- Connect: 5-10s
- Read: 10-60s (selon service)

### Asynchrone (Events/RabbitMQ)

Utilisé pour :
- Opérations métier critiques (ventes, stock, compta)
- Événements inter-services
- Pattern Saga

**Format d'événement** :
```json
{
  "event_id": "uuid",
  "event_type": "sale.created",
  "occurred_at": "2025-12-31T12:00:00Z",
  "producer": "sales-service",
  "correlation_id": "uuid",
  "idempotency_key": "optional",
  "payload": {}
}
```

## 💾 Gestion des données

### Base de données par service

Chaque service a sa propre base PostgreSQL :
- `identity_db`
- `farm_db`
- `inventory_db`
- `sales_db`
- `accounting_db`
- `reporting_db`

**Avantage** :
- Isolation des données
- Évolutivité indépendante
- Pas de couplage par la base

**Inconvénient** :
- Pas de JOIN entre services
- Solution : CQRS avec read models dans Reporting Service

### Pattern Append-Only

**Où** : Inventory (stock_movements), Accounting (ledger_entries, tax_records)

**Pourquoi** :
- Audit trail complet
- Traçabilité totale
- Conformité réglementaire
- Facilite le debug et l'analyse

**Comment** :
- Jamais de UPDATE ou DELETE
- Corrections via nouvelles entrées
- Status pour marquer l'état

## 🔐 Sécurité

### Authentification

- **JWT** avec access token (30 min) + refresh token (7 jours)
- Rotation automatique des refresh tokens
- Hash BCrypt pour mots de passe

### Autorisation (RBAC)

4 rôles prédéfinis :
- **admin** : Tout
- **gestionnaire** : Opérations (pas users)
- **agent_terrain** : Saisie terrain
- **comptable** : Compta + TVA

Permissions granulaires :
- Format : `resource:action` (ex: `farm:read`, `sales:write`)
- Associées aux rôles
- Vérifiées à chaque requête

### Rate Limiting

- **Auth** : 5 requêtes / minute
- **Général** : 10 requêtes / seconde
- Implémenté dans Nginx

## 📊 Monitoring et Observabilité

### Logs structurés

- Format JSON
- Champs standard : timestamp, level, service, correlation_id
- Bibliothèque : structlog

### Métriques (à implémenter)

- Prometheus pour collecte
- Grafana pour visualisation

### Tracing (à implémenter)

- OpenTelemetry
- Jaeger pour visualisation

## 🚀 Déploiement

### Développement

```bash
docker-compose up --build -d
```

### Production (recommandé)

- Kubernetes avec Helm charts
- Secrets management (Vault)
- Auto-scaling des services
- Load balancer externe

## 📈 Évolutivité

### Scaling horizontal

Tous les services sont **stateless** → facilement scalables

```yaml
# Exemple avec Docker Compose
docker-compose up --scale inventory-service=3
```

### Scaling vertical

Ajuster les ressources dans docker-compose.yml :

```yaml
services:
  inventory-service:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## 🎓 Bonnes pratiques appliquées

✅ **Database-per-Service** : Isolation des données
✅ **Event-Driven** : Résilience et découplage
✅ **Append-Only** : Audit trail
✅ **Idempotence** : Sécurité des opérations
✅ **BFF Pattern** : Performance mobile
✅ **API Gateway** : Point d'entrée unique
✅ **RBAC** : Sécurité granulaire
✅ **Structured Logging** : Observabilité
✅ **Docker** : Portabilité
✅ **Health Checks** : Monitoring

## 🔮 Roadmap

- [ ] Observabilité complète (Prometheus/Grafana)
- [ ] Tests automatisés (pytest)
- [ ] CI/CD (GitHub Actions)
- [ ] Déploiement Kubernetes
- [ ] Service Mesh (Istio)
- [ ] API versioning
- [ ] GraphQL Gateway
- [ ] Offline-first mobile avec sync bidirectionnel

---

**Version** : 1.0.0
**Date** : 31 Décembre 2025
**Auteur** : LLM Agents Class
