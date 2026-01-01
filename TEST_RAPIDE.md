# 🧪 Test Rapide de l'Application

Guide pour tester rapidement toutes les fonctionnalités de l'application.

## ⚡ Prérequis

L'application doit être démarrée:
```bash
cd c:\LLM_agents_class\application_agricole
docker-compose up -d
```

Attendre 2-3 minutes que tous les services démarrent.

## 🔐 1. Test d'authentification (2 min)

### Connexion
1. Ouvrir http://localhost dans le navigateur
2. Vous devriez être redirigé vers `/login`
3. Entrer:
   - Username: `admin`
   - Password: `admin123`
4. Cliquer sur "Se connecter"

**✅ Résultat attendu**: Redirection vers le dashboard

### Vérifier la session
1. Ouvrir les DevTools (F12)
2. Aller dans Application > Local Storage > http://localhost
3. Vérifier la présence de:
   - `access_token`
   - `refresh_token`
   - `user`

**✅ Résultat attendu**: Les 3 clés sont présentes

## 📊 2. Test du Dashboard (2 min)

URL: http://localhost/dashboard

### Vérifications visuelles

**Cartes statistiques** (4 cartes en haut):
- [ ] Chiffre d'affaires (en FCFA)
- [ ] Ventes totales (nombre)
- [ ] Produits (nombre)
- [ ] Stock faible (nombre)

**Graphiques**:
- [ ] Graphique ligne "Ventes par mois"
- [ ] Graphique pie "État de l'inventaire"
- [ ] Graphique bar "Produits les plus vendus"

**Actions rapides** (4 boutons):
- [ ] Nouvelle vente
- [ ] Gérer stock
- [ ] Comptabilité
- [ ] Rapports

### Test navigation
Cliquer sur chaque bouton d'action rapide et vérifier que la page correspondante s'ouvre.

**✅ Résultat attendu**: Navigation fluide sans erreur

## 🌾 3. Test Gestion Exploitations (3 min)

URL: http://localhost/farms

### Créer une exploitation
1. Cliquer sur "Nouvelle exploitation"
2. Remplir le formulaire:
   - Nom: `Ferme de Test`
   - Localisation: `Dakar, Sénégal`
   - Surface: `50`
   - Description: `Exploitation agricole test`
3. Cliquer sur "Créer"

**✅ Résultat attendu**: La ferme apparaît dans la liste

### Modifier une exploitation
1. Cliquer sur "Modifier" sur la ferme créée
2. Changer le nom: `Ferme Test Modifiée`
3. Cliquer sur "Modifier"

**✅ Résultat attendu**: Le nom est mis à jour

### Supprimer (optionnel)
1. Cliquer sur l'icône poubelle
2. Confirmer

**✅ Résultat attendu**: La ferme est supprimée

## 📦 4. Test Gestion Inventaire (5 min)

URL: http://localhost/inventory

### Créer un produit
1. Cliquer sur "Nouveau produit"
2. Remplir:
   - Nom: `Riz`
   - Catégorie: `CEREALE`
   - Unité: `kg`
   - Prix unitaire: `500`
   - Description: `Riz de qualité`
3. Cliquer sur "Créer"

**✅ Résultat attendu**: Le produit apparaît dans la table

### Faire une entrée de stock
1. Cliquer sur l'icône flèche vers le bas (entrée) sur le produit Riz
2. Remplir:
   - Quantité: `1000`
   - Référence: `BON-001`
   - Notes: `Livraison janvier`
3. Cliquer sur "Confirmer"

**✅ Résultat attendu**: Le stock actuel passe à 1000 kg

### Faire une sortie de stock
1. Cliquer sur l'icône flèche vers le haut (sortie)
2. Remplir:
   - Quantité: `50`
   - Notes: `Vente locale`
3. Cliquer sur "Confirmer"

**✅ Résultat attendu**: Le stock actuel passe à 950 kg

### Vérifier le badge stock
- Badge VERT si stock >= 10
- Badge ROUGE si stock < 10

**✅ Résultat attendu**: Badge vert pour 950 kg

## 💰 5. Test Ventes (2 min)

URL: http://localhost/sales

### Consulter la liste
- [ ] Table avec colonnes: N° Vente, Date, Client, Montant TTC, Statut
- [ ] Badges de statut colorés (PENDING, COMPLETED, CANCELLED)

### Créer une vente (via API - optionnel)
Pour créer une vente, vous devez passer par l'API Documentation:
1. Aller sur http://localhost/docs
2. Chercher `POST /api/v1/sales`
3. Essayer avec un payload de test

**✅ Résultat attendu**: Vente créée et visible dans la liste

## 📊 6. Test Comptabilité (2 min)

URL: http://localhost/accounting

### Vérifier les cartes
- [ ] Total Débit (en FCFA)
- [ ] Total Crédit (en FCFA)
- [ ] Solde (en FCFA)

### Vérifier la table
- [ ] Colonnes: Date, Compte, Description, Débit, Crédit
- [ ] Débit en VERT
- [ ] Crédit en ROUGE
- [ ] Format dates: dd/MM/yyyy

**✅ Résultat attendu**: Écritures comptables affichées correctement

## 📄 7. Test Rapports (3 min)

URL: http://localhost/reports

### Générer un rapport
1. Cliquer sur "Rapport Ventes"
2. Attendre la génération (quelques secondes)

**✅ Résultat attendu**: Le rapport apparaît dans la table "Rapports générés"

### Télécharger PDF
1. Cliquer sur le bouton "PDF" du rapport
2. Le fichier PDF se télécharge

**✅ Résultat attendu**: PDF téléchargé et lisible

### Télécharger Excel
1. Cliquer sur le bouton "Excel" du rapport
2. Le fichier .xlsx se télécharge

**✅ Résultat attendu**: Excel téléchargé et lisible

## 📱 8. Test Responsive (3 min)

### Ouvrir DevTools
1. Appuyer sur F12
2. Cliquer sur l'icône mobile (ou Ctrl+Shift+M)

### Tester différentes tailles

**Mobile (375x667 - iPhone SE)**:
- [ ] Menu hamburger visible en haut à gauche
- [ ] Sidebar cachée par défaut
- [ ] Cliquer sur hamburger ouvre la sidebar
- [ ] Cartes en 1 colonne
- [ ] Table avec scroll horizontal

**Tablette (768x1024 - iPad)**:
- [ ] Sidebar toujours cachée
- [ ] Cartes en 2 colonnes
- [ ] Menu hamburger présent

**Desktop (1920x1080)**:
- [ ] Sidebar toujours visible
- [ ] Pas de menu hamburger
- [ ] Cartes en 4 colonnes
- [ ] Table pleine largeur

**✅ Résultat attendu**: L'interface s'adapte correctement à chaque taille

## 🔄 9. Test Refresh Token (2 min)

### Simuler expiration du token
1. Ouvrir DevTools (F12) > Application > Local Storage
2. Modifier `access_token` avec une valeur invalide: `invalid_token`
3. Faire une action (ex: naviguer vers /farms)

**✅ Résultat attendu**:
- L'app tente un refresh automatique
- Si le refresh token est valide, nouveau access_token obtenu
- Si invalide, redirection vers /login

## 🚪 10. Test Déconnexion (1 min)

### Se déconnecter
1. Cliquer sur le bouton "Déconnexion" en bas de la sidebar
2. Vérifier:
   - Redirection vers `/login`
   - Local storage vidé (F12 > Application > Local Storage)
   - Impossible d'accéder aux pages protégées

### Tester protection routes
1. Après déconnexion, essayer d'aller sur http://localhost/dashboard
2. Vérifier redirection automatique vers `/login`

**✅ Résultat attendu**: Toutes les routes sont protégées

## 🔍 11. Test API Documentation (1 min)

URL: http://localhost/docs

### Vérifier Swagger UI
- [ ] Interface Swagger chargée
- [ ] Liste des endpoints visible
- [ ] Endpoints groupés par tags

### Tester un endpoint
1. Cliquer sur `POST /api/v1/auth/login`
2. Cliquer sur "Try it out"
3. Remplir:
```json
{
  "username": "admin",
  "password": "admin123"
}
```
4. Cliquer sur "Execute"

**✅ Résultat attendu**: Réponse 200 avec access_token et refresh_token

## 🎨 12. Test Design & UX (2 min)

### Vérifier cohérence visuelle
- [ ] Couleurs cohérentes (thème vert agricole)
- [ ] Icônes Feather uniformes
- [ ] Spacing régulier
- [ ] Typographie lisible
- [ ] Hover effects sur boutons
- [ ] Transitions fluides

### Vérifier accessibilité basique
- [ ] Textes contrastés
- [ ] Boutons cliquables (curseur pointer)
- [ ] Inputs avec labels
- [ ] Messages d'erreur clairs

**✅ Résultat attendu**: Design professionnel et cohérent

## 📊 Résumé des tests

### Checklist globale

- [ ] ✅ Connexion fonctionne
- [ ] ✅ Dashboard affiche les graphiques
- [ ] ✅ CRUD Exploitations OK
- [ ] ✅ CRUD Produits OK
- [ ] ✅ Entrées/Sorties stock OK
- [ ] ✅ Ventes affichées
- [ ] ✅ Comptabilité affichée
- [ ] ✅ Génération rapports OK
- [ ] ✅ Téléchargement PDF/Excel OK
- [ ] ✅ Responsive mobile OK
- [ ] ✅ Refresh token automatique OK
- [ ] ✅ Déconnexion OK
- [ ] ✅ Protection routes OK

## ⏱️ Temps total estimé

**~30 minutes** pour tous les tests

## 🐛 En cas de problème

### Frontend ne charge pas
```bash
docker-compose logs frontend
docker-compose restart frontend
```

### Erreur 502 Bad Gateway
```bash
# Attendre que les services démarrent
docker-compose ps
# Vérifier que tous sont "healthy" ou "running"
```

### Erreur de connexion
- Vérifier username: `admin` (minuscule)
- Vérifier password: `admin123`
- Voir les logs: `docker-compose logs identity-service`

### Redémarrer tout
```bash
docker-compose down
docker-compose up -d
# Attendre 2-3 minutes
```

## ✅ Validation finale

Si tous les tests passent:

**🎉 L'APPLICATION EST FONCTIONNELLE À 100% !** 🎉

Vous pouvez commencer à l'utiliser pour gérer vos données agricoles.

---

**Bon tests! 🚀**
