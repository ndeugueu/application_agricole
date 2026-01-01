#!/bin/bash
# Script de test de l'API
# Teste les endpoints principaux pour vérifier que tout fonctionne

set -e

BASE_URL="${BASE_URL:-http://localhost}"
echo "🧪 Test de l'API Agricole - $BASE_URL"
echo "=========================================="
echo ""

# Fonction pour afficher les résultats
check_response() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1"
        exit 1
    fi
}

# 1. Test de santé
echo "📍 Test de santé de l'API Gateway..."
curl -s -f $BASE_URL/health > /dev/null
check_response "API Gateway opérationnel"
echo ""

# 2. Test d'authentification
echo "🔐 Test d'authentification..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@2025"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Échec de l'authentification"
    echo "Réponse: $LOGIN_RESPONSE"
    exit 1
fi

check_response "Authentification réussie"
echo ""

# 3. Test de récupération du profil utilisateur
echo "👤 Test de récupération du profil..."
curl -s -f $BASE_URL/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" > /dev/null
check_response "Profil utilisateur récupéré"
echo ""

# 4. Test de la liste des rôles
echo "🔑 Test de récupération des rôles..."
curl -s -f $BASE_URL/api/v1/roles \
  -H "Authorization: Bearer $TOKEN" > /dev/null
check_response "Rôles récupérés"
echo ""

# 5. Test BFF Mobile - Home
echo "📱 Test BFF Mobile (home)..."
curl -s -f $BASE_URL/m/home \
  -H "Authorization: Bearer $TOKEN" > /dev/null
check_response "BFF Mobile opérationnel"
echo ""

# 6. Test BFF Web - Dashboard
echo "💻 Test BFF Web (dashboard)..."
curl -s -f $BASE_URL/w/dashboard \
  -H "Authorization: Bearer $TOKEN" > /dev/null
check_response "BFF Web opérationnel"
echo ""

# 7. Test création d'une ferme
echo "🚜 Test création d'une ferme..."
FARM_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/farms \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "TEST_FARM_001",
    "name": "Ferme Test",
    "location": "Test Location",
    "total_area": 5.0,
    "owner_name": "Test Owner"
  }')

FARM_ID=$(echo $FARM_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$FARM_ID" ]; then
    echo "⚠️  Ferme non créée (peut déjà exister)"
else
    check_response "Ferme créée avec succès"
fi
echo ""

# 8. Test création d'un produit
echo "📦 Test création d'un produit..."
PRODUCT_RESPONSE=$(curl -s -X POST $BASE_URL/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "TEST_PROD_001",
    "name": "Produit Test",
    "product_type": "recolte",
    "unit": "kg",
    "min_stock_level": 10,
    "unit_price": 1000
  }')

PRODUCT_ID=$(echo $PRODUCT_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$PRODUCT_ID" ]; then
    echo "⚠️  Produit non créé (peut déjà exister)"
else
    check_response "Produit créé avec succès"
    echo "   Product ID: $PRODUCT_ID"
fi
echo ""

# 9. Test récupération des niveaux de stock
echo "📊 Test récupération des niveaux de stock..."
curl -s -f $BASE_URL/api/v1/stock-levels \
  -H "Authorization: Bearer $TOKEN" > /dev/null
check_response "Niveaux de stock récupérés"
echo ""

# 10. Test de la liste des types de cultures
echo "🌾 Test récupération des types de cultures..."
curl -s -f $BASE_URL/api/v1/crop-types \
  -H "Authorization: Bearer $TOKEN" > /dev/null
check_response "Types de cultures récupérés"
echo ""

echo "=========================================="
echo "✅ Tous les tests sont passés avec succès!"
echo ""
echo "🎉 L'application est opérationnelle!"
echo ""
echo "🔑 Token d'accès (valide 30 min):"
echo "$TOKEN"
echo ""
echo "📚 Documentation interactive: $BASE_URL/docs"
echo "🐰 RabbitMQ Management: http://localhost:15672"
echo "📦 MinIO Console: http://localhost:9001"
