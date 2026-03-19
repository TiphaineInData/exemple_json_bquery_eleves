import os
import requests
from google.cloud import bigquery
# pip install google-cloud-bigquery


# 1. Config (à remplir par l'élève)

# Pour avoir le fichier de clé JSON, il faut :
# - Aller sur https://console.cloud.google.com/ 
# - Sélectionner votre projet
# - Aller dans "IAM & Admin" > "Service Accounts"
# - Créer un compte de service (ex: "bigquery-loader")
# - Donner les permissions "Job user" et "Admin BigQuery"
# - Créer une clé JSON et la télécharger (ex: "cle_bigquery.json")
# - Placer ce fichier dans le même dossier que ce script
# - Remplir le chemin vers ce fichier dans la variable d'environnement GOOGLE_APPLICATION_CREDENTIALS : GOOGLE_APPLICATION_CREDENTIALS="cle_bigquery.json"
# - Attention : ne pas partager ce fichier, il contient des clés d'accès à votre projet Google Cloud ! Mettez le dans le gitignore !!!

# Il faut que le projet, dataset et table existent déjà dans BigQuery. 
# Pour créer un dataset :
# - Aller sur https://console.cloud.google.com/bigquery
# - Sélectionner votre projet
# - Cliquer sur "Créer un ensemble de données" (dataset)
# - Donner un ID (=nom (ex: "raw_data")) et choisir une localisation (ex: "europe-west9")

table_id = "projet-3-wild.raw_data.raw_users" # La table RAW

# table_id = "nom_du_projet.nom_de_lensemble_de_donnees.nom_de_la_table_raw" 

def ingest_data_bis():
    # Charger les credentials INSIDE la fonction, pas au niveau global
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/cle_bigquery.json"
    client = bigquery.Client()
    
    # 2. Récupération (API JSONPlaceholder)
    url = "https://jsonplaceholder.typicode.com/users"
    response = requests.get(url)
    data = response.json()

    # 3. Config du chargement
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND", # On ajoute à la suite
        autodetect=True,                  # BigQuery crée les colonnes seul
    )

    # 4. Envoi
    load_job = client.load_table_from_json(data, table_id, job_config=job_config)
    load_job.result() 

    print(f"Succès : {len(data)} utilisateurs insérés dans BigQuery.")

if __name__ == "__main__":
    ingest_data_bis()

# pip install dbt-bigquery : pour créer des modèles SQL dans dbt qui s'appuient sur les données chargées dans BigQuery
# dbt init : pour initialiser un projet 