#!/bin/bash

# Varmista, että skripti on suorituskelpoinen

[ -x "./scripts/04_destroy_all.sh" ] || chmod +x ./scripts/04_destroy_all.sh


# Skripti tuhoaa Azure-palvelut Terraformilla

echo "🛑 Sammutetaan Azure-palvelut Terraformilla..."

# Siirrytään Terraform-hakemistoon
cd infra/tf/services  || { echo "❌ Services-hakemistoa ei löytynyt!"; exit 1; }

# Tuhoamisprosessi
echo "💣 Sammutetaan palvelut..."
terraform destroy -auto-approve || { echo "❌ Terraform-tuhoaminen epäonnistui!"; exit 1; }

echo "✅ Palvelut sammutettu onnistuneesti!"

cd ..

cd container_registry || { echo "❌ container_registry-hakemistoa ei löytynyt!"; exit 1; }

# Tuhoamisprosessi 2
echo "💣 Sammutetaan container registry..."
terraform destroy -auto-approve || { echo "❌ Terraform-tuhoaminen epäonnistui!"; exit 1; }

echo "✅ Myös Container Registry sammutettu onnistuneesti!"
