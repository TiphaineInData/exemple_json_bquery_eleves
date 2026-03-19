FROM apache/airflow:2.7.1

USER root

# Installer les dépendances système
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

USER airflow

# Installer dbt-core et dbt-bigquery avec leurs dépendances correctes
# On utilise une version de dbt compatible avec Python 3.8 et Airflow 2.7.1
RUN pip install --no-cache-dir \
    dbt-core==1.0.0 \
    dbt-bigquery==1.0.0 \
    google-cloud-bigquery>=2.30.0

# Forcer les versions de Jinja2, MarkupSafe, et typing_extensions compatibles avec Airflow 2.7.1
# APRÈS l'installation de dbt, pour éviter les conflits
RUN pip install --force-reinstall --no-cache-dir \
    "Jinja2>=3.0.0" \
    "MarkupSafe>=2.0" \
    "typing_extensions>=4.0.0" \
    "pydantic>=1.10.0"


