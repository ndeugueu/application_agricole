# Implémentation du Frontend React

## 📱 Vue d'ensemble

Frontend web **responsive** React/Next.js 14 avec TypeScript et Tailwind CSS.

**Compatibilité:**
- 💻 Desktop (Chrome, Firefox, Edge, Safari)
- 📱 Mobile (iOS Safari, Chrome Android)
- 📱 Tablette

## 🎯 Fonctionnalités implémentées

### ✅ Authentification
- [x] Page de connexion avec design moderne
- [x] Gestion JWT avec refresh token automatique
- [x] Protection des routes (redirection si non authentifié)
- [x] Déconnexion
- [x] Context global d'authentification

### ✅ Layout Responsive
- [x] Sidebar collapsible sur mobile (hamburger menu)
- [x] Navigation adaptative
- [x] Header avec user info
- [x] Mobile-first design
- [x] Breakpoints Tailwind (sm, md, lg, xl)

### ✅ Dashboard
- [x] 4 cartes statistiques (CA, ventes, produits, stock faible)
- [x] Graphique ligne - Ventes par mois (Recharts)
- [x] Graphique pie - État inventaire (Recharts)
- [x] Graphique bar - Top produits (Recharts)
- [x] Actions rapides (boutons navigation)
- [x] Responsive grids (1 col mobile, 2-4 cols desktop)

### ✅ Gestion Exploitations (/farms)
- [x] Liste des exploitations en grilles responsive
- [x] Créer une exploitation (modal)
- [x] Modifier une exploitation
- [x] Supprimer une exploitation (confirmation)
- [x] Affichage surface, localisation, description
- [x] Design avec icônes

### ✅ Gestion Inventaire (/inventory)
- [x] Table responsive des produits
- [x] CRUD complet produits
- [x] Entrées/Sorties de stock (modals séparés)
- [x] Affichage stock en temps réel
- [x] Badges stock faible (rouge) / stock normal (vert)
- [x] Catégories (céréale, légume, fruit, bétail, intrant)
- [x] Prix unitaire et unités

### ✅ Gestion Ventes (/sales)
- [x] Table responsive des ventes
- [x] Affichage montants HT/TVA/TTC
- [x] Statut ventes (badges colorés)
- [x] Format dates (dd/MM/yyyy)
- [x] Navigation vers détails vente
- [x] Bouton nouvelle vente

### ✅ Comptabilité (/accounting)
- [x] 3 cartes statistiques (débit, crédit, solde)
- [x] Table écritures comptables
- [x] Affichage débit/crédit avec couleurs
- [x] Format dates
- [x] Responsive table

### ✅ Rapports (/reports)
- [x] 4 boutons génération rapports
- [x] Table historique rapports générés
- [x] Téléchargement PDF
- [x] Téléchargement Excel
- [x] Types de rapports (ventes, inventaire, comptabilité, custom)
- [x] Format dates avec heures

## 🗂️ Structure des fichiers créés

```
frontend/
├── package.json                    # Dépendances Next.js, React, Tailwind
├── tsconfig.json                   # Configuration TypeScript
├── tailwind.config.js              # Thème Tailwind personnalisé
├── postcss.config.js               # PostCSS pour Tailwind
├── next.config.js                  # Config Next.js (standalone build)
├── .env.local                      # Variables d'environnement
├── Dockerfile                      # Image Docker multi-stage
├── .dockerignore                   # Exclusions Docker
├── README.md                       # Documentation frontend
│
├── src/
│   ├── app/                        # Next.js App Router
│   │   ├── layout.tsx              # Layout root avec AuthProvider
│   │   ├── page.tsx                # Page d'accueil (redirection)
│   │   ├── globals.css             # Styles globaux + Tailwind
│   │   │
│   │   ├── login/
│   │   │   └── page.tsx            # Page connexion
│   │   │
│   │   ├── dashboard/
│   │   │   └── page.tsx            # Dashboard avec graphiques
│   │   │
│   │   ├── farms/
│   │   │   └── page.tsx            # Gestion exploitations
│   │   │
│   │   ├── inventory/
│   │   │   └── page.tsx            # Gestion inventaire
│   │   │
│   │   ├── sales/
│   │   │   └── page.tsx            # Gestion ventes
│   │   │
│   │   ├── accounting/
│   │   │   └── page.tsx            # Comptabilité
│   │   │
│   │   └── reports/
│   │       └── page.tsx            # Rapports
│   │
│   ├── components/
│   │   └── Layout.tsx              # Layout avec sidebar responsive
│   │
│   ├── contexts/
│   │   └── AuthContext.tsx         # Context authentification
│   │
│   └── lib/
│       └── api.ts                  # Client API avec intercepteurs JWT
```

## 🎨 Technologies utilisées

### Core
- **Next.js 14**: Framework React avec App Router
- **React 18**: Bibliothèque UI
- **TypeScript**: Typage statique

### Styling
- **Tailwind CSS 3**: Utility-first CSS
- **Autoprefixer**: Compatibilité navigateurs

### State & Data
- **Zustand**: State management léger
- **Axios**: Client HTTP avec intercepteurs
- **React Context**: Authentification globale

### Charts & Icons
- **Recharts**: Graphiques (Line, Bar, Pie)
- **React Icons**: Icônes (Feather Icons)
- **date-fns**: Manipulation dates

## 🔧 Configuration API Client

Le client API (`src/lib/api.ts`) inclut:

### Intercepteurs Request
- Ajout automatique du token JWT dans les headers
- Headers `Authorization: Bearer {token}`

### Intercepteurs Response
- Détection des erreurs 401
- Refresh token automatique
- Retry de la requête avec nouveau token
- Redirection `/login` si refresh échoue

### Stockage
- Tokens stockés dans `localStorage`
- `access_token` - durée 30 min
- `refresh_token` - durée 7 jours
- `user` - infos utilisateur

### Méthodes disponibles
```typescript
// Auth
api.login(username, password)
api.logout()
api.getCurrentUser()

// Dashboard
api.getDashboard()
api.getInventoryOverview()
api.getSalesOverview()
api.getAccountingOverview()

// Farms
api.getFarms()
api.createFarm(data)
api.updateFarm(id, data)
api.deleteFarm(id)

// Inventory
api.getProducts()
api.createProduct(data)
api.updateProduct(id, data)
api.deleteProduct(id)
api.getStockMovements()
api.createStockMovement(data)
api.getStockLevels()

// Sales
api.getCustomers()
api.getSales()
api.createSale(data)
api.getSale(id)

// Accounting
api.getAccounts()
api.getLedgerEntries()
api.getMonthlyReport(year, month)

// Reports
api.getReports()
api.generateReport(data)
api.downloadReport(reportId, format)
```

## 🎨 Design System

### Couleurs principales
```css
primary-50  à primary-900  /* Vert agricole */
gray-50 à gray-900         /* Neutrals */
red-50 à red-900          /* Erreurs/Alertes */
green-50 à green-900      /* Succès */
blue-50 à blue-900        /* Info */
```

### Breakpoints Tailwind
```
sm:  640px  (tablette portrait)
md:  768px  (tablette landscape)
lg:  1024px (laptop)
xl:  1280px (desktop)
```

### Composants réutilisables

#### Layout
- Sidebar responsive avec menu hamburger
- Header sticky
- Container principal avec padding adaptatif

#### Cards
- Cartes statistiques avec icônes
- Hover effects
- Shadow et transitions

#### Tables
- Tables responsive avec overflow-x-auto
- Headers sticky
- Hover rows

#### Modals
- Overlay backdrop
- Centrage responsive
- Scroll intégré si contenu long

#### Boutons
- Primary (vert)
- Secondary (gris)
- Danger (rouge)
- Tailles sm, md, lg

## 📊 Graphiques (Recharts)

### Line Chart - Ventes par mois
- Axe X: Mois
- Axe Y: Montant (FCFA)
- Couleur: Vert primary
- Responsive Container

### Pie Chart - État inventaire
- 3 segments: En stock, Stock faible, Rupture
- Couleurs: Vert, Orange, Rouge
- Labels avec pourcentages

### Bar Chart - Top produits
- 2 barres par produit: Quantité, Revenu
- Couleurs: Vert, Bleu
- Tooltip interactif

## 🔐 Sécurité

### Authentification
- JWT stocké en localStorage
- Refresh automatique avant expiration
- Déconnexion automatique si token invalide
- Protection routes avec redirect

### Headers sécurité
Gérés par Nginx Gateway:
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

## 🚀 Déploiement

### Build Docker
```dockerfile
# Multi-stage build
1. base (Node 20 Alpine)
2. deps (npm install)
3. builder (npm run build)
4. runner (production)
```

### Optimisations
- Output standalone
- Static optimization
- Code splitting automatique
- Image optimization Next.js
- Cache static assets

## 📱 Responsive Design

### Mobile (< 640px)
- Sidebar cachée par défaut
- Menu hamburger
- Grilles 1 colonne
- Tables avec scroll horizontal
- Boutons pleine largeur

### Tablette (640px - 1024px)
- Sidebar cachée par défaut (lg breakpoint)
- Grilles 2 colonnes
- Meilleure utilisation espace

### Desktop (> 1024px)
- Sidebar toujours visible
- Grilles 3-4 colonnes
- Tables pleine largeur
- Hover effects actifs

## ✅ Tests manuels recommandés

- [ ] Login/Logout
- [ ] Navigation entre pages
- [ ] CRUD exploitations
- [ ] CRUD produits
- [ ] Entrées/sorties stock
- [ ] Affichage graphiques dashboard
- [ ] Génération rapports
- [ ] Téléchargement PDF/Excel
- [ ] Responsive mobile (Chrome DevTools)
- [ ] Refresh token automatique
- [ ] Protection routes

## 📚 Documentation

- **README Frontend**: `frontend/README.md`
- **Guide lancement**: `GUIDE_LANCEMENT_COMPLET.md`
- **README projet**: `README.md`

## 🎯 Prochaines améliorations possibles

- [ ] Dark mode
- [ ] Notifications toast
- [ ] Pagination tables
- [ ] Filtres avancés
- [ ] Export CSV
- [ ] Impression factures
- [ ] PWA (Progressive Web App)
- [ ] Mode offline
- [ ] Multi-langue (i18n)
- [ ] Tests unitaires (Jest)
- [ ] Tests E2E (Playwright)
