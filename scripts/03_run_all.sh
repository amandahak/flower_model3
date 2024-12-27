#!/bin/bash

# Skripti käynnistää Azure-palvelut Terraformilla

set -e  # Lopeta suoritus, jos tulee virhe

echo "🚀 Aloitetaan Azure-palveluiden käynnistäminen..."

# Vaihe 1: Luo Azure Container Registry
echo "🔧 Luodaan Azure Container Registry..."
cd ../infra/tf/container_registry || { echo "❌ Hakemisto infra/tf/container_registry ei löytynyt!"; exit 1; }

terraform init --upgrade
terraform apply -auto-approve # Terraformi ei vaadi 'yes' -vastausta suorittaakseen

# Vaihe 2: Kirjaudu Azure Container Registryyn
echo "🔑 Kirjaudutaan Azure Container Registryyn..."
cd ../../../scripts || { echo "❌ Hakemisto scripts ei löytynyt!"; exit 1; }
./01_acr_login.sh

# Vaihe 3: Buildaa ja julkaise Docker-kuvat
echo "🐳 Buildataan Docker-kuvat..."

# Buildaa flowerpredict
./02_build_n_release.sh flowerpredict 1.0
# Buildaa flowerui
./02_build_n_release.sh flowerui 1.0
# Buildaa modeller
./02_build_n_release.sh modeller 1.0

echo "🐳 flowerpredict, flowerui ja modeller buildattu!"

# Vaihe 4: Julkaise palvelut Terraformilla
echo "🚀 Julkaistaan Azure-palvelut..."
cd ../infra/tf/services || { echo "❌ Hakemisto infra/tf/services ei löytynyt!"; exit 1; }

terraform init --upgrade
terraform apply -auto-approve # Terraformi ei vaadi 'yes' -vastausta suorittaakseen

echo "✅ Azure-palveluiden käynnistys valmis!"
