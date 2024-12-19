# Opettaja: Online-Learning


docker compose up -d --build

Tämä repositorio on opettajan kopio. Opiskelijat voivat käyttää sitä templaattina.

Koopisnippetit kopioidaan kurssivideoiden tallentamisen myötä `course-materials`-repositorioon ja indeksoidaan sen `README.md`-tiedostoon.

## Valmiin projektin käyttöönotto

Aloita valitsemalla identifier, joka on osa kaikkia resursseja. Terraformin variables.tf poimii tämän ympäristömuuttujasta `TF_VAR_identifier`.

Aseta se Linuxissa: `export TF_VAR_identifier=ope`

1. Kirjaudu Azure CLI:llä sisään. Lue ohje [scripts/README.md](scripts/README.md).
2. Luo Azureen Container Registry (docker imageille)

    ```bash
    cd infra/tf/container_registry

    terraform init --upgrade
    terraform apply
    ```

3. Kirjaudu Azure Container Registryyn

    ```bash
    ./scripts/01_acr_login.sh
    ```

4. Buildaa haluamasi appi

    ```bash
    ./scripts/02_build_app.sh <APP> <VERSION>
    ```

    Jos `APP` esimerkiksi `drawhello`, skripti buildaa Dockerfilen kansiossa `src/drawhello` ja puskee sen Azure Container Registryyn. Versio on päättämäsi versionumero.

    Julkaise kaikki kolme:

    * `drawhello`
    * `modeller`
    * `predicthello`

5. Julkaise Services tf-skriptien mukaiset palvelut

    Käy muokkaamassa `variables.tf`-tiedostoa kaikkien kolmen palvelun kohdalla. Vaihda muuttujan backend/frontend/modeller default-arvoksi Azure Portalista kopioimasi arvo, kuten vaikkapa: `default     = "cropeolearn.azurecr.io/drawhello:1"`

    ```bash
    cd infra/tf/services

    terraform init --upgrade
    terraform apply

    # Voit seurata logeja näin (Ctrl+C lopettaa)
    az container logs --resource-group rg-identifier-olearn --name ci-identifier-olearn --follow
    ```

6. Käy saitilla

    Saat palvelun osoitteen komennolla: `terraform output`, joka pitää ajaa kyseisessä hakemistossa (`infra/tf/services`).

7. Tarkkeile Storage Accountia

    Lataa Microsoft Azure Storage Explorer ja tutki, kuinka Queueen (esim. `sq-ope-olearn`) saapuu rivejä, kun lisäät frontista kuvia koulutusjonoon. Kun kuvia on jonossa 2 tai enemmän, `modeller`-palvelu työstää uuden CSV-tiedoston ja uuden mallin. Nämä löytyvät Blob Containerista (esim. `st-ope-olearn`).

8. Poista palvelut

    Aja lopulta seuraava komento ensin `services`-hakemistossa ja sitten `container_registry`-hakemistossa:

    ```bash
    terraform destroy
    ```