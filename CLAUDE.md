# APPLICATION AGRICOLE & ÉLEVAGE — Spécification d’architecture (Microservices)  
*(FastAPI + PostgreSQL, Web + Mobile, orienté développement rapide)*

## 1) Contexte

Cette application vise à digitaliser la gestion **Agricole & Élevage** (contexte terrain, connectivité parfois instable) avec une cible **Web (back-office)** et **Mobile Android** (agents terrain).

**Périmètre fonctionnel clé (MVP + évolutions)**
- **Agricole** : parcelles, campagnes/saisons, cultures, itinéraires techniques (opérations planifiées/réalisées), récoltes, pertes.
- **Élevage** : gestion par lots (ex. volailles, hannetons), événements (alimentation, mortalité, soins, production…).
- **Stocks** : produits (intrants, aliments, récoltes, produits transformés), mouvements d’entrée/sortie/ajustement, alertes stock bas.
- **Achats/Ventes** : fournisseurs/clients, lignes, paiements (cash / mobile money), suivi.
- **Comptabilité & TVA** : journal d’écritures, TVA **19,25%** (collectée/déductible), états mensuels, synthèses.
- **Rapports & Exports** : tableaux de bord + exports **PDF/Excel**.
- **Utilisateurs & rôles** : Admin / Gestionnaire / Agent terrain / Comptable.

**Objectifs non-fonctionnels**
- Fiabilité des données (stocks, paiements, comptabilité/TVA).
- Performance sur réseau mobile.
- Évolutivité (multi-fermes, offline/synchronisation phase 2).
- Observabilité (logs, métriques, traçage) et maintenance.

---

## 2) Architecture technique

### Stack recommandée
- **API** : FastAPI (Python)
- **Base de données** : PostgreSQL (un DB ou schéma par service)
- **ORM & migrations** : SQLAlchemy 2.0 + Alembic
- **Auth** : JWT (access + refresh), RBAC
- **Message Bus** (événements) : RabbitMQ (simple et efficace)  
  *(alternatives : NATS, Kafka si très gros volume)*
- **Gateway** : Nginx / Kong / Traefik (selon préférence)
- **BFF** : FastAPI (2 services dédiés)
- **Cache** (optionnel) : Redis (sessions, rate limiting, cache de lecture)
- **Exports** :
  - Excel : openpyxl / xlsxwriter
  - PDF : WeasyPrint (HTML→PDF) ou ReportLab
- **Stockage fichiers** (recommandé) : MinIO (S3 compatible) pour exports PDF/Excel
- **Observabilité** :
  - Logs : Loki/ELK
  - Metrics : Prometheus + Grafana
  - Traces : OpenTelemetry + Jaeger/Tempo
- **Déploiement** :
  - Dev/MVP : Docker Compose
  - Prod : Kubernetes (ou Docker Swarm si simple)
  - CI/CD : GitHub Actions

### Principes d’architecture
- **Un seul point d’entrée** : API Gateway
- **Deux BFF** (Backend-for-Frontend) :
  - BFF Mobile : endpoints “1 appel = 1 écran”
  - BFF Web : endpoints orientés dashboards & admin
- **Microservices domain-driven** (DDD)
- **Communication hybride** :
  - Synchrone REST pour lectures simples et actions directes
  - Asynchrone via événements pour orchestrer stock/compta/ventes (pattern Saga)

---

## 3) Vue d’ensemble (proposition)

### Composants
**Clients**
- Mobile Android (React Native recommandé)
- Web Admin (React/Next.js recommandé)

**Plateforme**
- API Gateway (auth, routage, rate limiting, TLS)
- BFF Mobile (optimisation réseau + agrégation)
- BFF Web (agrégation dashboards)
- Microservices métiers (FastAPI)
- Message Bus (RabbitMQ) pour événements
- Stockage exports (MinIO/S3)
- Observabilité (logs/metrics/traces)

### Pourquoi des BFF ?
Sans BFF, le mobile doit faire trop d’appels pour un écran (réseau instable = UX mauvaise).  
Le BFF Mobile fournit des endpoints “composites” pour limiter latence et complexité côté client.

---

## 4) Découpage microservices recommandé (domain-driven)

> Chaque service **possède** ses données et sa logique métier.  
> Les services ne lisent pas directement la base des autres services.

### 1) Identity & Access Service (Auth/RBAC)
- Users, rôles, permissions
- JWT access/refresh, rotation, révocation
- Gestion des sessions/appareils (optionnel)

### 2) Farm Service (Structure exploitation)
- Fermes, parcelles, campagnes/saisons
- Référentiel cultures (types, unités, métadonnées)

### 3) Crop Operations Service (Itinéraires techniques)
- Opérations (planifiées/réalisées), main d’œuvre, intrants utilisés, coûts
- Statut et suivi des tâches par parcelle/culture/campagne

### 4) Harvest Service (Récoltes)
- Récoltes, pertes, qualité, affectation (stock/vente/transformation)

### 5) Livestock Service (Élevage)
- Lots (volailles / hannetons)
- Événements : alimentation, mortalité, soins, ponte/production, transformation (ex. farine)

### 6) Inventory Service (Stock)
- Catalogue produits (intrants, aliments, récoltes, transformés)
- **Stock en mouvements** : entrées/sorties/ajustements
- Alertes stock bas, inventaires

### 7) Procurement Service (Achats)
- Achats fournisseurs + lignes + réception
- Déclenche des événements impactant stock + TVA déductible

### 8) Sales Service (Ventes)
- Ventes clients + lignes
- Paiements (cash / mobile money), statuts (pending/confirmed/rejected)
- Déclenche événements impactant stock + TVA collectée

### 9) Accounting & Tax Service (Comptabilité/TVA)
- Journal comptable (append-only), écritures de correction par contre-écriture
- TVA : collectée/déductible, états mensuels, exports fiscaux internes

### 10) Reporting & Export Service
- Read models pour dashboards
- Exports PDF/Excel
- Historique des exports, génération asynchrone

### 11) Notification/Automation Service (optionnel)
- Notifications (email/SMS/WhatsApp/Discord)
- Peut être piloté par n8n au début (alertes, rapports périodiques)

### 12) Sync Service (phase 2 offline)
- Ingestion des “outbox events” mobiles
- Résolution de conflits, idempotence, replay sécurisé

### 13) BFF Mobile
- API “écrans”
- Cache, pagination adaptée, compression, gestion offline/sync

### 14) BFF Web
- API dashboards/admin (agrégation multi-services + read models)

---

## 5) Communication entre services (simple et robuste)

### A) Synchrone (REST interne)
À utiliser pour :
- Lectures simples, non critiques (ex. récupérer des métadonnées produit)
- Actions qui doivent répondre immédiatement (ex. auth)

**Recommandations**
- Timeouts stricts
- Retries limités
- Circuit breaker (si nécessaire)
- Pas de chaînes d’appels longues (éviter “service A → B → C → D”)

### B) Asynchrone (événements) — recommandé pour le métier critique
À utiliser pour :
- Stock / ventes / achats / compta / TVA
- Orchestration “Saga” sans transaction distribuée

**Exemples d’événements**
- `sale.created`
- `stock.reserved` / `stock.decremented` / `stock.failed`
- `payment.recorded`
- `ledger.posted`
- `purchase.received`

### Format d’enveloppe d’événement (conseillé)
```json
{
  "event_id": "uuid",
  "event_type": "sale.created",
  "occurred_at": "2025-12-28T10:15:30Z",
  "producer": "sales-service",
  "correlation_id": "uuid",
  "idempotency_key": "string",
  "payload": { }
}
```

**Bonnes pratiques**
- **Idempotence** : chaque consommateur ignore les doublons (`event_id`/`idempotency_key`)
- **Outbox pattern** côté producteurs : publier l’événement de manière fiable
- Versionner `payload` si besoin (compatibilité)

---

## 6) Gestion des données (règle d’or)

### Règle d’or
✅ **Database-per-service** (ou au minimum schéma isolé + droits stricts)  
❌ Pas de lectures/écritures directes dans la DB d’un autre service

### Pourquoi ?
- Évite couplage fort
- Permet déploiements indépendants
- Simplifie l’évolution des schémas

### Agrégations multi-domaines (dashboards)
Ne pas faire de “JOIN” cross-services en prod.  
Utiliser :
- **Reporting Service** avec read models (CQRS)
- Vues matérialisées / tables de stats alimentées par événements
- Jobs périodiques (ETL léger) si nécessaire

### Stock et comptabilité : modèles robustes
- **Stock** : toujours via `stock_movements` (append-only)
- **Compta** : toujours via `ledger_entries` (append-only)
- Montants en **entiers** (ex. FCFA), jamais float

### Publication fiable d’événements
- Outbox pattern : écriture business + insertion outbox dans la même transaction
- Un worker publie outbox → bus, puis marque “sent”

---

## 7) Exemple concret : “Créer une vente” (flux fiable)

Objectif : éviter incohérences (vente créée mais stock non décrémenté, etc.)

### Étapes (Saga orientée événements)
1. **Client (Mobile/Web)** → Gateway → **BFF** → **Sales Service**
2. Sales Service :
   - crée `sale` + `sale_lines` + `payment` (statut `PENDING`)
   - écrit outbox `sale.created`
3. Bus publie `sale.created`
4. **Inventory Service** consomme :
   - vérifie disponibilité
   - crée `stock_movements` (sortie) ou `reservation`
   - émet `stock.decremented` ou `stock.failed`
5. **Accounting & Tax Service** consomme :
   - calcule TVA collectée
   - poste `ledger_entries` (journal)
   - émet `ledger.posted`
6. Sales Service consomme retours :
   - si `stock.decremented` + `ledger.posted` => sale `CONFIRMED`
   - si `stock.failed` => sale `REJECTED` + (option) annule paiement / marque “à régulariser”

### Idempotence & robustesse
- Chaque étape est **rejouable** sans doublons
- En cas de panne, les événements sont rejoués via bus/outbox
- Statuts explicites : `PENDING / CONFIRMED / REJECTED`

---

## 8) Mobile : offline-first (dès le design, même si phase 2)

Même si l’offline arrive en phase 2, on prépare dès la V1 pour éviter une refonte.

### Stockage local
- Base locale : SQLite (recommandé) ou Realm
- Tables locales “miroir” : parcelles, lots, produits, opérations, ventes brouillons…

### Pattern Outbox mobile
- Chaque action (ex. “ajouter opération”, “enregistrer mortalité”, “vente”) est enregistrée localement :
  - `pending_actions` (outbox)
- Un synchroniseur tente d’envoyer au **Sync Service** quand réseau OK

### Idempotence
- Chaque action a :
  - `client_action_id` (UUID)
  - `idempotency_key`
- Côté serveur, si la même action est renvoyée, elle est ignorée/rejouée proprement

### Stratégie de conflits (guidelines)
- Événements (mortalité, alimentation, opérations) : souvent **append-only** → peu de conflits
- Données “référentielles” (parcelle, produit) : **server wins**
- Cas sensibles (stock/compta) : pas d’édition offline directe ; passer par événements + validation serveur

### Endpoints BFF Mobile “1 écran = 1 appel”
Exemples :
- `GET /m/plot/{id}/overview`
- `GET /m/livestock/{batch_id}/timeline`
- `POST /m/sync/push` (batch actions)
- `GET /m/sync/pull?since=...`

---

## 9) Sécurité & exploitation (obligatoire en microservices)

### Sécurité
- Gateway :
  - TLS
  - Rate limiting
  - Validation JWT (ou délégation à Identity service)
- Services :
  - RBAC strict (scopes/roles)
  - Validation Pydantic
  - Protection injections (SQLAlchemy paramétré)
- Interne :
  - réseau privé (VPC)
  - mTLS (si possible) entre services
- Gestion secrets :
  - Vault/KMS ou secrets Kubernetes
  - rotation des clés JWT / tokens

### Journalisation & audit
- Audit trail pour actions sensibles :
  - corrections stock
  - annulations ventes
  - écritures comptables/TVA
- Logs structurés (JSON) : user_id, correlation_id, service, endpoint

### Observabilité
- OpenTelemetry (traces)
- Prometheus (metrics)
- Grafana (dashboards)
- Alerting (erreurs 5xx, latence, backlog queue)

### Backups & résilience
- Sauvegarde PostgreSQL (planifiée)
- Sauvegarde MinIO/S3 (exports)
- Tests de restauration réguliers (important)

### Déploiement & CI/CD
- Docker multi-service (dev) + docker-compose
- CI : lint + tests + build images
- CD : déploiement staging/prod (K8s)
- Migration DB via Alembic à chaque release

---

## Annexe — conventions recommandées (très utiles pour développement rapide)

### Conventions d’identifiants
- UUID v4 pour toutes entités exposées à mobile
- `created_at`, `updated_at`, `deleted_at` (soft delete si utile)

### Conventions d’API
- Versionnement : `/api/v1/...`
- Pagination : `limit`, `cursor` (ou `offset` en MVP)
- Tri/filtre : `sort`, `from`, `to`, `status`

### Conventions d’événements
- `domain.action` (`sale.created`, `stock.decremented`, `ledger.posted`)
- `correlation_id` pour tracer une transaction métier bout-en-bout

---

**Fin du document.**
