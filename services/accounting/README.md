# Accounting & Tax Service

Service de comptabilité et gestion de la TVA pour l'application agricole.

## Fonctionnalités

### 1. Plan Comptable (Chart of Accounts)
- Création et gestion des comptes comptables
- Types de comptes: Actif, Passif, Capitaux Propres, Produit, Charge
- Support de la hiérarchie des comptes (comptes parents/sous-comptes)

### 2. Journal Comptable (Ledger Entries)
- Écritures comptables en partie double (débit/crédit)
- **Pattern append-only**: Les écritures ne sont jamais modifiées ou supprimées
- Corrections via écritures d'inversion
- Montants stockés en centimes FCFA (entiers) pour éviter les erreurs de précision
- Traçabilité complète: date, type, référence, utilisateur

### 3. Gestion de la TVA (19.25%)
- TVA collectée (sur les ventes)
- TVA déductible (sur les achats)
- Calcul automatique basé sur le montant HT
- Rapports mensuels de TVA
- États de TVA nette (à payer ou à récupérer)

### 4. Rapports
- Balance de vérification (Trial Balance)
- Rapports mensuels de TVA
- Analyse par période fiscale

### 5. Événements
Le service écoute et réagit aux événements:
- `sale.created`: Crée automatiquement la TVA collectée
- `purchase.received`: Crée automatiquement la TVA déductible

Le service publie des événements:
- `ledger.posted`: Écriture comptable créée
- `tax.tva_collectee`: TVA collectée enregistrée
- `tax.tva_deductible`: TVA déductible enregistrée

## Modèles de Données

### Account (Compte)
```python
- id: UUID
- code: str (unique, ex: "401", "512")
- name: str
- account_type: AccountType
- parent_account_id: UUID (optionnel)
- description: str
- is_active: int
```

### LedgerEntry (Écriture comptable)
```python
- id: UUID
- entry_date: str (YYYY-MM-DD)
- entry_type: EntryType
- debit_account_id: UUID
- credit_account_id: UUID
- amount: int (FCFA cents)
- reference_type: str
- reference_id: UUID
- description: str
- fiscal_month: str (YYYY-MM)
- fiscal_year: str (YYYY)
- is_reversed: int
- idempotency_key: str
```

### TaxRecord (Enregistrement TVA)
```python
- id: UUID
- tax_type: TaxType (TVA_COLLECTEE ou TVA_DEDUCTIBLE)
- base_amount: int (montant HT en centimes FCFA)
- tax_rate: int (1925 = 19.25%)
- tax_amount: int (montant TVA en centimes FCFA)
- reference_type: str
- reference_id: UUID
- transaction_date: str (YYYY-MM-DD)
- fiscal_month: str (YYYY-MM)
- fiscal_year: str (YYYY)
- idempotency_key: str
```

## API Endpoints

### Plan Comptable
- `POST /api/v1/accounts` - Créer un compte
- `GET /api/v1/accounts` - Liste des comptes
- `GET /api/v1/accounts/{account_id}` - Détails d'un compte

### Écritures Comptables
- `POST /api/v1/ledger-entries` - Créer une écriture
- `GET /api/v1/ledger-entries` - Liste des écritures (filtrable)
- `POST /api/v1/ledger-entries/{entry_id}/reverse` - Inverser une écriture

### TVA
- `POST /api/v1/tax-records` - Créer un enregistrement TVA
- `GET /api/v1/tax-records` - Liste des enregistrements TVA

### Rapports
- `GET /api/v1/reports/tva/monthly` - Rapports mensuels TVA (tous les mois)
- `GET /api/v1/reports/tva/monthly/{fiscal_month}` - Rapport TVA pour un mois spécifique
- `GET /api/v1/reports/trial-balance` - Balance de vérification

### Health Check
- `GET /health` - Vérification de santé du service

## Sécurité & Permissions

### Rôles autorisés
- **ADMIN**: Accès complet
- **COMPTABLE**: Création/consultation écritures et rapports TVA
- **GESTIONNAIRE**: Consultation des rapports uniquement

### Pattern Append-Only
Les écritures comptables et les enregistrements de TVA ne sont **jamais** modifiés ou supprimés:
- Garantit la traçabilité et l'auditabilité
- Les corrections se font par écritures d'inversion
- Champ `is_reversed` pour marquer les écritures annulées

### Idempotence
Toutes les opérations critiques supportent l'idempotence via `idempotency_key`:
- Évite les doublons en cas de retry
- Crucial pour les événements asynchrones

## Calcul de la TVA

Taux standard: **19.25%**

```python
# Montants stockés en centimes FCFA
base_amount_cents = 100000  # 1000 FCFA
tax_rate = 1925  # 19.25%
tax_amount = (base_amount_cents * tax_rate) / 10000
# tax_amount = 19250 centimes = 192.50 FCFA
```

## Exemple d'utilisation

### 1. Créer des comptes
```bash
# Compte client
POST /api/v1/accounts
{
  "code": "411",
  "name": "Clients",
  "account_type": "actif"
}

# Compte ventes
POST /api/v1/accounts
{
  "code": "701",
  "name": "Ventes de produits agricoles",
  "account_type": "produit"
}
```

### 2. Créer une écriture comptable
```bash
POST /api/v1/ledger-entries
{
  "entry_date": "2025-01-15",
  "entry_type": "vente",
  "debit_account_id": "411-uuid",
  "credit_account_id": "701-uuid",
  "amount": 100000,  # 1000 FCFA en centimes
  "reference_type": "sale",
  "reference_id": "sale-uuid",
  "description": "Vente de tomates"
}
```

### 3. Obtenir le rapport TVA mensuel
```bash
GET /api/v1/reports/tva/monthly/2025-01

# Réponse:
{
  "fiscal_month": "2025-01",
  "tva_collectee": 50000,    # 500 FCFA
  "tva_deductible": 20000,   # 200 FCFA
  "tva_net": 30000,          # 300 FCFA à payer
  "sales_count": 10,
  "purchases_count": 5
}
```

## Variables d'Environnement

```bash
DATABASE_URL=postgresql://user:password@host:5432/accounting_db
RABBITMQ_URL=amqp://user:password@rabbitmq:5672/
DEBUG=false
```

## Démarrage

### Développement
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Docker
```bash
docker build -t accounting-service .
docker run -p 8000:8000 accounting-service
```

## Tests

Les tests devraient couvrir:
- Création d'écritures comptables
- Calcul de la TVA (19.25%)
- Rapports mensuels
- Idempotence des opérations
- Gestion des événements (sale.created, purchase.received)
- Écritures d'inversion

## Notes Importantes

1. **Montants**: Toujours en centimes FCFA (entiers) pour éviter les erreurs de précision des float
2. **Append-Only**: Ne jamais modifier/supprimer les écritures ou enregistrements de TVA
3. **Idempotence**: Toujours utiliser `idempotency_key` pour les événements
4. **Fiscal Period**: Dates au format `YYYY-MM-DD`, périodes fiscales `YYYY-MM`
5. **TVA**: Taux fixe de 19.25% (1925 en représentation entière)
