from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
# Import de la fonction refactorisée (déplacée dans plugins)
from load_data_bis import ingest_data_bis

with DAG(
    dag_id="pipeline_complet_bq_dbt",
    start_date=datetime(2026, 3, 18),
    schedule_interval="@daily",
    catchup=False
) as dag:

    # Étape 1 : Ingestion JSON -> BigQuery
    task_ingest = PythonOperator(
        task_id="ingestion_api",
        python_callable=ingest_data_bis
    )

    # Étape 2 : Transformation dbt
    # On dit à Docker d'aller dans le dossier monté et de lancer dbt
    task_dbt = BashOperator(
        task_id="transform_dbt",
        bash_command="cd /opt/airflow/p3_dbt && dbt run"
    )

    # L'ordre d'exécution
    task_ingest >> task_dbt