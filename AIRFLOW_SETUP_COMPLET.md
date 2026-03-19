# 🎯 GUIDE COMPLET : Setup Airflow + dbt + BigQuery

## 📁 Architecture finale

```
json_to_bigquery/
├── Airflow/
│   ├── docker-compose.yaml      ← MODIFIÉ (volumes + env vars)
│   ├── Dockerfile               ← CRÉÉ (dbt-bigquery + dépendances)
│   ├── dags/
│   │   └── mon-premier-dag.py   ← DAG principal
│   ├── plugins/
│   │   └── load_data_bis.py     ← Fonction réutilisable (from load_data.py)
│   ├── logs/                    ← Auto-généré
│   └── .env                     ← Auto-généré
├── p3_dbt/                      ← Projet dbt
│   ├── dbt_project.yml          ← MODIFIÉ (ajout config-version: 2)
│   ├── profiles.yml             ← CRÉÉ (config BigQuery)
│   └── models/
├── cle_bigquery.json            ← Clé de service GCP
└── load_data.py                 ← Original
```

---

# 🚀 ÉTAPES DE SETUP

## 1️⃣ Télécharger Airflow avec curl

```bash
cd json_to_bigquery
mkdir Airflow
cd Airflow

curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'
```

Cela crée un fichier `docker-compose.yaml` standard avec postgres, redis, webserver, etc.

---

## 2️⃣ Créer le Dockerfile

### 🤔 Pourquoi un Dockerfile ?

Normalement, Airflow s'installe tout seul. Mais ici, on veut aussi **dbt** dans le même conteneur.

**Le problème :** Les dépendances se battent ! 🥊

- **dbt-bigquery 0.21.1** dit : "J'ai besoin de Jinja2 version 2.11.3"
- **Airflow 2.7.1** dit : "Moi j'ai besoin de Jinja2 version 3.0.0 ou plus récent"

C'est comme si deux applications demandaient des versions différentes de Python. **Impossible de tout installer d'un coup.**

**La solution :** Un custom Dockerfile qui :
1. Installe dbt en premier
2. Puis force-réinstalle les bonnes versions pour Airflow

**Fichier : `Airflow/Dockerfile`**

```dockerfile
FROM apache/airflow:2.7.1
# On part de l'image officielle Airflow

USER root
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
# Installe git (utile si tu pulls des repos dbt)

USER airflow
# On bascule à l'utilisateur airflow (sécurité, pas root dans le conteneur)

# ===== ÉTAPE 1 : Installer dbt =====
RUN pip install --no-cache-dir \
    dbt-core==1.0.0 \
    dbt-bigquery==1.0.0 \
    google-cloud-bigquery>=2.30.0
# À ce stade, Jinja2 2.11.3 s'installe (demandée par dbt)

# ===== ÉTAPE 2 : Forcer les bonnes versions pour Airflow =====
RUN pip install --force-reinstall --no-cache-dir \
    "Jinja2>=3.0.0" \
    "MarkupSafe>=2.0" \
    "typing_extensions>=4.0.0" \
    "pydantic>=1.10.0"
# --force-reinstall : Désinstalle et réinstalle (même si déjà présent)
# Ça remplace Jinja2 2.11.3 → 3.1.2+ (compatible Airflow)
```

### 💡 Résumé pour les reconvertis :
- **Sans Dockerfile :** `docker compose up` crash car pip ne sait pas résoudre les conflits
- **Avec Dockerfile :** Python gère l'installation étape par étape. Chaque étape écrase la précédente.
- **Résultat :** Les deux (dbt ET Airflow) fonctionnent ensemble ✅

---

## 3️⃣ Modifier docker-compose.yaml

### 🔴 LIGNE #1 : Utiliser le Dockerfile (remplacé)

**AVANT :**
```yaml
  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.7.1}
  # build: .
```

**APRÈS :**
```yaml
  # image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.7.1}
  build: .
```

---

### 🔴 LIGNE #2 : Corriger _PIP_ADDITIONAL_REQUIREMENTS (remplacé)

**AVANT :**
```yaml
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:- }
                                                                  ↑ espace cause erreur
```

**APRÈS :**
```yaml
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}
                                                                  ↑ vide
```

**Pourquoi ?** L'espace faisait crasher pip avec l'erreur : `You must give at least one requirement to install`

---

### 🔴 LIGNE #3 : Ajouter les variables d'environnement pour dbt et BigQuery

#### 🤔 Pourquoi ?

Les variables d'environnement sont comme des **instructions** qu'on passe au conteneur Docker :
- "Ici, tu vas trouver tes credentials BigQuery"
- "Ici, tu vas trouver ton fichier de config dbt"

Sans ça, dbt et Python ne savent pas où chercher !

**AVANT :**
```yaml
environment:
  &airflow-common-env
  AIRFLOW__CORE__EXECUTOR: CeleryExecutor
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
  AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
  AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
  AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
  AIRFLOW__CORE__FERNET_KEY: ''
  AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
  AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
  AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth'
  _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}
  # Les deux lignes suivantes MANQUENT !
```

**APRÈS :**
```yaml
environment:
  &airflow-common-env
  AIRFLOW__CORE__EXECUTOR: CeleryExecutor
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
  AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
  AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
  AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
  AIRFLOW__CORE__FERNET_KEY: ''
  AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
  AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
  AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth'
  # ===== NOUVELLES LIGNES =====
  GOOGLE_APPLICATION_CREDENTIALS: /opt/airflow/cle_bigquery.json
  # Dit à Python où trouver la clé de service Google (pour BigQuery)
  DBT_PROFILES_DIR: /opt/airflow/p3_dbt
  # Dit à dbt où trouver son fichier profiles.yml
  # ===== FIN NOUVELLES LIGNES =====
  _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}
```

---

### 🔴 LIGNE #4 : Ajouter les volumes pour p3_dbt et cle_bigquery.json

#### 🤔 Pourquoi ?

Les **volumes** font le lien entre ta machine (l'hôte) et le conteneur Docker.

Imagine que ton dossier `p3_dbt` est dans `/Users/tipha/Documents/json_to_bigquery/p3_dbt` (sur ta machine).

Mais à l'intérieur du conteneur, ce dossier n'existe pas ! C'est un environnement isolé.

Donc on dit à Docker : **"Prends le dossier p3_dbt de la machine hôte et rends-le accessible au conteneur sous le chemin `/opt/airflow/p3_dbt`"**

Pareil pour `cle_bigquery.json` (la clé de service Google).

**Sans ces volumes :**
- dbt ne trouverait pas ses fichiers → Crash ❌
- Python ne trouverait pas la clé Google → Crash ❌

**AVANT :**
```yaml
volumes:
  - ./dags:/opt/airflow/dags
  - ./logs:/opt/airflow/logs
  - ./plugins:/opt/airflow/plugins
```

**APRÈS :**
```yaml
volumes:
  - ./dags:/opt/airflow/dags
  - ./logs:/opt/airflow/logs
  - ./plugins:/opt/airflow/plugins
  # ===== NOUVELLES LIGNES =====
  - ../p3_dbt:/opt/airflow/p3_dbt
  # Récupère le dossier p3_dbt du parent (..=remonte d'un niveau)
  # Et le monte en /opt/airflow/p3_dbt INSIDE le conteneur
  - ../cle_bigquery.json:/opt/airflow/cle_bigquery.json
  # Pareil pour la clé Google
  # ===== FIN NOUVELLES LIGNES =====
```

---

## 4️⃣ Créer/modifier les fichiers dbt

### `p3_dbt/dbt_project.yml` (MODIFIÉ)

**AJOUTER CETTE LIGNE :**
```yaml
name: 'p3_dbt'
version: '1.0.0'
config-version: 2                 ← AJOUTER (dbt 1.0.0+ l'exige)
profile: 'p3_dbt'
```

**Pourquoi ?** dbt 1.0.0 utilise un nouveau format de configuration (v2). L'ancien format (v1) génère l'erreur `Invalid config version: 1, expected 2`

---

### `p3_dbt/profiles.yml` (NEW - À CRÉER)

```yaml
p3_dbt:
  outputs:
    dev:
      type: bigquery
      project: projet-3-wild
      dataset: raw_data
      threads: 4
      timeout_seconds: 300
      location: europe-west9
      method: service-account
      keyfile: /opt/airflow/cle_bigquery.json    ← Chemin inside le conteneur
  target: dev
```

Cette configuration dit à dbt **comment se connecter à BigQuery**.

---

## 5️⃣ Créer les fichiers Python

### `Airflow/plugins/load_data_bis.py` (COPIE DE load_data.py)

```python
import os
import requests
from google.cloud import bigquery

# 🔴 NE PAS faire : from dotenv import load_dotenv; load_dotenv()
# POURQUOI ?
# - load_dotenv() cherche un fichier .env sur la MACHINE
# - Dans le conteneur Docker, ce fichier n'existe pas
# - À la place, on utilise os.environ[] qui accède aux variables définies dans docker-compose

table_id = "projet-3-wild.raw_data.raw_users"

def ingest_data_bis():
    """
    LES CREDENTIALS SONT ICI, PAS AU NIVEAU GLOBAL.
    Pourquoi ? Airflow parse ce fichier au démarrage.
    S'il y a des imports/connexions au niveau global, ça crash.
    C'est sûr seulement quand la fonction s'exécute (dans une tâche).
    """
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/cle_bigquery.json"
    client = bigquery.Client()
    
    # 2. Récupération (API JSONPlaceholder)
    url = "https://jsonplaceholder.typicode.com/users"
    response = requests.get(url)
    data = response.json()

    # 3. Config du chargement
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True,
    )

    # 4. Envoi
    load_job = client.load_table_from_json(data, table_id, job_config=job_config)
    load_job.result()
    
    print(f"Succès : {len(data)} utilisateurs insérés dans BigQuery.")

if __name__ == "__main__":
    ingest_data_bis()
```

**Changement clé par rapport à `load_data.py` :**
- AVANT : `from dotenv import load_dotenv; load_dotenv()` → Ne fonctionne pas en Docker
- APRÈS : `os.environ["..."] = "..."` → Fonctionne en Docker

---

### `Airflow/dags/mon-premier-dag.py` (CRÉÉ)

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
from load_data_bis import ingest_data_bis

with DAG(
    dag_id="pipeline_complet_bq_dbt",
    start_date=datetime(2026, 3, 18),
    schedule_interval="@daily",
    catchup=False
) as dag:

    # Tâche 1 : Ingestion JSON → BigQuery (via Python)
    task_ingest = PythonOperator(
        task_id="ingestion_api",
        python_callable=ingest_data_bis
    )

    # Tâche 2 : Transformation (via dbt bash command)
    task_dbt = BashOperator(
        task_id="transform_dbt",
        bash_command="cd /opt/airflow/p3_dbt && dbt run"
    )

    # Tâche 1 → Tâche 2 (en séquence)
    task_ingest >> task_dbt
```

---

# 🖥️ COMMANDES TERMINAL - LANCER TOUT

## 📋 Récapitulatif : Ce qu'on a créé

Avant de lancer, on a :
1. ✅ Créé `Airflow/Dockerfile` (résout les conflits de version)
2. ✅ Modifié `Airflow/docker-compose.yaml` (volumes + env vars)
3. ✅ Créé `p3_dbt/dbt_project.yml` avec `config-version: 2`
4. ✅ Créé `p3_dbt/profiles.yml` (config BigQuery pour dbt)
5. ✅ Copié `load_data_bis.py` dans `Airflow/plugins/`
6. ✅ Créé `Airflow/dags/mon-premier-dag.py` (le DAG)

## 🚀 Démarrage complet :

```bash
cd json_to_bigquery/Airflow

# ===== ÉTAPE 1 : Builder l'image Docker =====
docker compose build
# Ça lit le Dockerfile, télécharge apache/airflow:2.7.1
# Installe dbt, Google Cloud, et force les versions
# Peut prendre 5-10 minutes la première fois ⏳

# ===== ÉTAPE 2 : Lancer les services =====
docker compose up -d
# -d = détaché (background)
# Lance : webserver, scheduler, worker, triggerer, postgres, redis

# ===== ÉTAPE 3 : Vérifier que tout marche =====
docker compose ps
```

**Résultat attendu :**
```
NAME                          STATUS
airflow-webserver-1           Up 30s (healthy)           ← Interface web : localhost:8080
airflow-scheduler-1           Up 30s (healthy)           ← Déclenche les DAGs
airflow-worker-1              Up 30s (health: starting)  ← Exécute les tâches (ingestion + dbt)
airflow-triggerer-1           Up 30s (healthy)           ← Gère les événements
postgres-1                    Up 30s (healthy)           ← Base de données (stocke l'état des DAGs)
redis-1                       Up 30s (healthy)           ← Queue de messages (communique entre worker/scheduler)
```

💚 **Si tout est soit ✅ healthy**, tu peux continuer !

---

## Redémarrer après modification :

```bash
docker compose restart airflow-worker airflow-scheduler
```

Utilise cette commande quand tu modifies docker-compose.yaml ou les fichiers DAG/plugins.

---

## Voir les logs :

```bash
# Logs du webserver
docker compose logs airflow-webserver

# Logs du DAG parser et scheduler
docker compose logs airflow-scheduler

# Logs du worker (où s'exécutent les tâches)
docker compose logs airflow-worker

# Derniers 50 logs
docker compose logs airflow-worker --tail 50
```

---

## Arrêter les services :

```bash
docker compose down
```

---

# 🌐 CONNEXION BIGQUERY : AUTOMATIQUE ! ✅

## ❓ Question : Dois-je configurer une connexion dans `Admin → Connections` ?

**Réponse : NON ! C'est complètement automatique !** ✅

### 🤔 Pourquoi ?

Le secret : **Airflow N'EST PAS un client BigQuery.**

Airflow, c'est juste un **chef d'orchestre**. Il orchestre les tâches.

Ceux qui se connectent vraiment à BigQuery sont :

#### 1️⃣ Ta fonction Python `ingest_data_bis()` (dans `plugins/`)
```python
client = bigquery.Client()
```
- Cette ligne crée un client Google Cloud
- Il cherche la clé d'authentification via `os.environ["GOOGLE_APPLICATION_CREDENTIALS"]`
- `GOOGLE_APPLICATION_CREDENTIALS` pointe vers `/opt/airflow/cle_bigquery.json`
- Et grâce aux **volumes**, ce fichier existe inside le conteneur ! ✅

#### 2️⃣ dbt (via le BashOperator)
```bash
dbt run
```
- dbt lit `profiles.yml` à partir du chemin `DBT_PROFILES_DIR`
- `DBT_PROFILES_DIR` est défini dans docker-compose.yaml = `/opt/airflow/p3_dbt`
- `profiles.yml` dit : "utilise la clé `/opt/airflow/cle_bigquery.json` pour BigQuery"
- Et cette clé existe grâce aux volumes ! ✅

### 📍 Résumé : Pourquoi c'est automatique ?

| Élément | Défini où ? | Résultat |
|---------|-------------|----------|
| `GOOGLE_APPLICATION_CREDENTIALS` | `docker-compose.yaml` (env var) | Python sait où chercher la clé ✅ |
| `cle_bigquery.json` | `docker-compose.yaml` (volume) | Python peut accéder à la clé ✅ |
| `DBT_PROFILES_DIR` | `docker-compose.yaml` (env var) | dbt sait où chercher profiles.yml ✅ |
| `/opt/airflow/p3_dbt` | `docker-compose.yaml` (volume) | dbt peut accéder à profiles.yml ✅ |

**Grâce à ces 4 configurations, tout fonctionne sans qu'Airflow UI ait besoin de rien faire ! 🎉**

💡 **Analogie :** C'est comme si tu mettais tous les outils d'un menuisier dans sa camionnette AVANT qu'il ne parte. Il n'a rien à faire, tout est déjà là !

---

# 📊 FLUX COMPLET : DE DOCKER À BIGQUERY

```
╔════════════════════════════════════════════════════════════════╗
║                    TU LANCES LES COMMANDES                     ║
║                    docker compose build                        ║
║                    docker compose up -d                        ║
╚════════════════════════════════════════════════════════════════╝
                              ↓
        Docker crée 6 conteneurs et les lance :
        - airflow-webserver (interface web)
        - airflow-scheduler (découvre les DAGs)
        - airflow-worker (exécute les tâches)
        - postgres (base de données)
        - redis (queue de messages)
        - triggerer (gère les événements)
                              ↓
        Scheduler scanne le dossier /opt/airflow/dags/
        Et trouve : mon-premier-dag.py
                              ↓
        mon-premier-dag.py définit un DAG avec :
        - schedule_interval: "@daily" (se déclenche chaque jour)
        - Deux tâches en séquence
                              ↓
        ╔═══════════════════════════════════════════╗
        ║       LE DAG SE DÉCLENCHE (chaque jour)    ║
        ╚═══════════════════════════════════════════╝
                              ↓
        ┌─────────────────────────────────────────────────┐
        │  TÂCHE 1 : ingestion_api                        │
        │  (PythonOperator)                               │
        └─────────────────────────────────────────────────┘
             ↓
        Exécute : ingest_data_bis() (de plugins/load_data_bis.py)
             ↓
        Python l'initialize :
        - lit os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        - crée un client BigQuery
             ↓
        Python se connecte à BigQuery :
        - utilise la clé /opt/airflow/cle_bigquery.json
        - (qui existe grâce au volume du docker-compose.yaml)
             ↓
        Python fetch https://jsonplaceholder.typicode.com/users
        et charge les données dans :
        projet-3-wild.raw_data.raw_users ✅
                              ↓
        ┌─────────────────────────────────────────────────┐
        │  TÂCHE 2 : transform_dbt                        │
        │  (BashOperator)                                 │
        │  S'EXÉCUTE SEULEMENT SI TÂCHE 1 EST OK         │
        └─────────────────────────────────────────────────┘
             ↓
        Exécute : cd /opt/airflow/p3_dbt && dbt run
             ↓
        dbt l'initialize :
        - lit DBT_PROFILES_DIR = /opt/airflow/p3_dbt
        - cherche profiles.yml
        - lit la config BigQuery dedans
             ↓
        dbt se connecte à BigQuery :
        - utilise la clé /opt/airflow/cle_bigquery.json
        - (qui existe grâce au volume du docker-compose.yaml)
             ↓
        dbt scanne les fichiers .sql dans models/
        et les exécute contre BigQuery ✅
             ↓
        Résultat :
        - Tables transformées créées dans BigQuery
        - Ingestion + Transformation = FAIT ! 🎉
```

---

# ✅ CHECKLIST : TOUT CE QUI A ÉTÉ FAIT

### Infrastructure
- [x] Dockerfile créé (résout les conflits dbt ↔ Airflow)
- [x] docker-compose.yaml modifié (env vars + volumes)

### Configuration dbt
- [x] dbt_project.yml : `config-version: 2` ajoutée (pour dbt 1.0.0+)
- [x] profiles.yml créé avec config BigQuery (chemin Docker : /opt/airflow/p3_dbt/)

### Code Python & DAG
- [x] load_data_bis.py copié dans `plugins/` (modification : os.environ au lieu de load_dotenv)
- [x] mon-premier-dag.py créé dans `dags/` (2 tâches : ingestion + dbt)

### Démarrage
- [x] `docker compose build` (crée l'image)
- [x] `docker compose up -d` (lance les services)

---

# 🎯 LANCER L'INGESTION + LA TRANSFORMATION

## 📍 Étape 1 : Accéder à Airflow

**URL :** http://localhost:8080
**Utilisateur :** `airflow`
**Mot de passe :** `airflow`

Tu vois l'interface web d'Airflow avec une liste des DAGs.

## 📍 Étape 2 : Déclencher le pipeline

Cherche le DAG nommé **`pipeline_complet_bq_dbt`** dans la liste.

Clique sur le **bouton ▶️ vert** à droite du DAG ("Trigger DAG with default parameters").

## 📍 Étape 3 : Regarder l'exécution

Rafraîchis la page (F5) quelques secondes plus tard.

Tu vois :
- ✅ **Tâche 1 : `ingestion_api`** (devient verte) = données insérées dans BigQuery
- ✅ **Tâche 2 : `transform_dbt`** (devient verte) = dbt a transformé les données

## 🎉 C'EST FINI !

Les deux tâches s'exécutent **automatiquement en séquence** :
1. Python ingère les données de JSONPlaceholder → BigQuery ✅
2. dbt les transforme → Tables finales dans BigQuery ✅

### 📊 Vérifier les données

Pour voir ce qui a été inséré dans BigQuery :

**Requête 1 : Les utilisateurs brutes**
```sql
SELECT * FROM `projet-3-wild.raw_data.raw_users` LIMIT 5;
```

**Requête 2 : Les données transformées (via dbt)**
```sql
-- Dépend de tes modèles dbt
SELECT * FROM `projet-3-wild.raw_data.fct_users` LIMIT 5;
```

---

### 💡 Bonus : Le beau du setup

**À partir de maintenant :**
- Le DAG se déclenche **chaque jour automatiquement** (grâce à `@daily`)
- Tu n'as rien à faire ! ✨
- Chaque matin, Airflow ingère les données + dbt les transforme
- Tout fonctionne "en prod" sans intervention 🚀

