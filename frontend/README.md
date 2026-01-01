# AgriApp Frontend

Application web responsive React/Next.js pour la gestion agricole et d'élevage.

## Caractéristiques

- **Framework**: Next.js 14 avec App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **State Management**: Zustand
- **API Client**: Axios avec intercepteurs JWT
- **Responsive**: Design mobile-first, fonctionne sur desktop, tablette et mobile

## Pages disponibles

### 🔐 Authentification
- `/login` - Page de connexion avec JWT

### 📊 Dashboard
- `/dashboard` - Tableau de bord avec statistiques et graphiques
  - Chiffre d'affaires
  - Ventes totales
  - État de l'inventaire
  - Graphiques de ventes mensuelles
  - Top produits

### 🌾 Gestion des Exploitations
- `/farms` - Liste et gestion des exploitations
  - Créer/Modifier/Supprimer des exploitations
  - Visualiser les parcelles
  - Gestion des saisons

### 📦 Inventaire
- `/inventory` - Gestion des produits et du stock
  - CRUD produits
  - Entrées/Sorties de stock
  - Alertes stock faible
  - Vue en temps réel des niveaux de stock

### 💰 Ventes
- `/sales` - Gestion des ventes
  - Liste des ventes
  - Détails des ventes
  - Statut des paiements

### 📊 Comptabilité
- `/accounting` - Comptabilité
  - Écritures comptables
  - Soldes des comptes
  - TVA à 19.25%

### 📄 Rapports
- `/reports` - Génération et téléchargement de rapports
  - Rapports PDF
  - Export Excel
  - Rapports ventes, inventaire, comptabilité

## Installation et Développement

### Prérequis
- Node.js 20+
- npm

### Installation locale
```bash
cd frontend
npm install
npm run dev
```

L'application sera disponible sur http://localhost:3000

### Variables d'environnement

Créer un fichier `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost
```

## Déploiement Docker

L'application est automatiquement déployée via Docker Compose:

```bash
# Depuis le dossier racine du projet
docker-compose up -d frontend
```

Accès: http://localhost:3000 (ou via le gateway http://localhost/)

## Architecture

```
frontend/
├── src/
│   ├── app/              # Pages Next.js (App Router)
│   │   ├── dashboard/    # Tableau de bord
│   │   ├── farms/        # Exploitations
│   │   ├── inventory/    # Inventaire
│   │   ├── sales/        # Ventes
│   │   ├── accounting/   # Comptabilité
│   │   ├── reports/      # Rapports
│   │   └── login/        # Authentification
│   ├── components/       # Composants réutilisables
│   │   └── Layout.tsx    # Layout principal avec sidebar
│   ├── contexts/         # Contexts React
│   │   └── AuthContext.tsx # Gestion authentification
│   └── lib/              # Utilitaires
│       └── api.ts        # Client API avec intercepteurs JWT
├── public/               # Fichiers statiques
├── Dockerfile            # Image Docker production
└── package.json
```

## Fonctionnalités clés

### Authentification
- Login avec username/password
- JWT avec refresh token automatique
- Protection des routes
- Déconnexion automatique en cas d'expiration

### Responsive Design
- Mobile-first approach
- Sidebar collapsible sur mobile
- Tableaux avec scroll horizontal
- Grilles adaptatives

### API Integration
- Client API centralisé
- Gestion automatique des tokens
- Refresh token automatique
- Gestion des erreurs

### Performance
- Build optimisé avec Next.js standalone
- Images optimisées
- Code splitting automatique
- Cache des static assets

## Identifiants par défaut

```
Username: admin
Password: admin123
```

## Support navigateurs

- Chrome/Edge (dernières versions)
- Firefox (dernières versions)
- Safari 14+
- Mobile: iOS Safari, Chrome Android

## Scripts disponibles

```bash
npm run dev          # Développement
npm run build        # Build production
npm start            # Démarrer build
npm run lint         # Linter
```

## Contribution

Pour ajouter une nouvelle page:

1. Créer le fichier dans `src/app/nom-page/page.tsx`
2. Ajouter la route dans `src/components/Layout.tsx`
3. Créer les appels API dans `src/lib/api.ts` si nécessaire

## Production

En production, l'application utilise:
- Build optimisé Next.js standalone
- Serving via Nginx (API Gateway)
- Container Docker isolé
- Variables d'environnement sécurisées
