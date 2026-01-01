#!/bin/bash
# Script pour initialiser des données par défaut
# Utile pour le développement et les démonstrations

set -e

BASE_URL="${BASE_URL:-http://localhost}"
echo "🌱 Initialisation des données par défaut"
echo "=========================================="
echo ""

# Authentification
echo "🔐 Authentification en cours..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@2025"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Échec de l'authentification"
    exit 1
fi

echo "✅ Authentification réussie"
echo ""

# Créer des utilisateurs de démonstration
echo "👥 Création des utilisateurs..."

# Gestionnaire
curl -s -X POST $BASE_URL/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "gestionnaire",
    "email": "gestionnaire@agricole.local",
    "password": "Gestionnaire@2025",
    "full_name": "Jean Gestionnaire",
    "role_ids": []
  }' > /dev/null || echo "  ⚠️  Gestionnaire existe déjà"

# Agent terrain
curl -s -X POST $BASE_URL/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "agent",
    "email": "agent@agricole.local",
    "password": "Agent@2025",
    "full_name": "Marie Agent Terrain",
    "role_ids": []
  }' > /dev/null || echo "  ⚠️  Agent existe déjà"

# Comptable
curl -s -X POST $BASE_URL/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "comptable",
    "email": "comptable@agricole.local",
    "password": "Comptable@2025",
    "full_name": "Pierre Comptable",
    "role_ids": []
  }' > /dev/null || echo "  ⚠️  Comptable existe déjà"

echo "✅ Utilisateurs créés"
echo ""

# Créer des fermes
echo "🚜 Création des fermes de démonstration..."

# Ferme 1
FARM1=$(curl -s -X POST $BASE_URL/api/v1/farms \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "FARM_NORD_001",
    "name": "Ferme du Nord",
    "location": "Région Nord - Korhogo",
    "total_area": 25.5,
    "owner_name": "Kouadio Yao",
    "owner_phone": "+225 07 12 34 56 78",
    "owner_email": "k.yao@agricole.local"
  }')

# Ferme 2
FARM2=$(curl -s -X POST $BASE_URL/api/v1/farms \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "FARM_SUD_002",
    "name": "Ferme du Sud",
    "location": "Région Sud - Abidjan",
    "total_area": 15.0,
    "owner_name": "N Guessan Marie",
    "owner_phone": "+225 05 98 76 54 32"
  }')

echo "✅ Fermes créées"
echo ""

# Créer des produits
echo "📦 Création des produits..."

# Produits agricoles
curl -s -X POST $BASE_URL/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "MAIS_001",
    "name": "Maïs Blanc",
    "product_type": "recolte",
    "unit": "kg",
    "min_stock_level": 500,
    "unit_cost": 25000,
    "unit_price": 50000
  }' > /dev/null

curl -s -X POST $BASE_URL/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "RIZ_001",
    "name": "Riz Paddy",
    "product_type": "recolte",
    "unit": "kg",
    "min_stock_level": 1000,
    "unit_cost": 30000,
    "unit_price": 60000
  }' > /dev/null

# Intrants
curl -s -X POST $BASE_URL/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "ENGRAIS_NPK",
    "name": "Engrais NPK 15-15-15",
    "product_type": "intrant",
    "unit": "kg",
    "min_stock_level": 100,
    "unit_cost": 75000,
    "unit_price": 100000
  }' > /dev/null

curl -s -X POST $BASE_URL/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "SEMENCE_MAIS",
    "name": "Semences Maïs Hybride",
    "product_type": "intrant",
    "unit": "kg",
    "min_stock_level": 50,
    "unit_cost": 150000,
    "unit_price": 200000
  }' > /dev/null

echo "✅ Produits créés"
echo ""

# Créer des clients
echo "👥 Création des clients..."

curl -s -X POST $BASE_URL/api/v1/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "CLIENT_001",
    "name": "Coopérative des Agriculteurs",
    "contact_person": "Traoré Seydou",
    "phone": "+225 01 23 45 67 89",
    "email": "coop.agriculteurs@example.ci",
    "classification": "wholesale"
  }' > /dev/null

curl -s -X POST $BASE_URL/api/v1/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "CLIENT_002",
    "name": "Marché Central",
    "contact_person": "Bakayoko Awa",
    "phone": "+225 07 98 76 54 32",
    "classification": "retail"
  }' > /dev/null

echo "✅ Clients créés"
echo ""

echo "=========================================="
echo "✅ Données par défaut initialisées!"
echo ""
echo "📊 Résumé:"
echo "  - 3 utilisateurs supplémentaires"
echo "  - 2 fermes"
echo "  - 4 produits"
echo "  - 2 clients"
echo ""
echo "🔑 Identifiants de test:"
echo "  Admin:        admin / Admin@2025"
echo "  Gestionnaire: gestionnaire / Gestionnaire@2025"
echo "  Agent:        agent / Agent@2025"
echo "  Comptable:    comptable / Comptable@2025"
echo ""
echo "🌐 Accès: $BASE_URL"
echo "📚 Documentation: $BASE_URL/docs"
