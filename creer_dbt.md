# Guide dbt avec BigQuery (projet p3_dbt)

Ce document explique pas à pas comment configurer, exécuter et surveiller un projet dbt (Data Build Tool) sur Google BigQuery.

## 1. Objectif et architecture globale

- Source : données JSON ingérées depuis une API par Python (dataset raw_data).
- Transformations : dbt dans les datasets staging, intermediate, marts.
- Orchestration : Airflow (optionnel, recommandé en production).

## 2. Prérequis

- GCP + projet activé.
- Compte de service GCP avec rôles BigQuery Admin, BigQuery Job User.
- Clé JSON du compte service (`cle_bigquery.json`).
- Python 3.10+.
- dbt (adapter `dbt-bigquery`).
- `.gitignore` contenant :
  - .env
  - *.json
  - my-env/

## 3. Ingestion Python vers BigQuery

1. Installer :

```bash
pip install google-cloud-bigquery python-dotenv requests
```

2. `.env` :

```text
GOOGLE_APPLICATION_CREDENTIALS="cle_bigquery.json"
```

3. Logique :
- appel API + parse JSON,
- nettoyer / typage,
- charger dans `raw_data.raw_users` via BigQuery API.

4. Vérifier sur la console BigQuery que la table existe.

## 4. Installation et initialisation dbt

```bash
pip install dbt-bigquery
dbt init p3_dbt
```

`p3_dbt` est un nom modèle (pas de tiret).

Cela crée une arborescence :
```
p3_dbt/
  ├── models/          # tes fichiers SQL + YAML
  ├── macros/          # tes fonctions dbt
  ├── tests/           # tests de données
  ├── dbt_project.yml  # config du projet
  └── profiles.yml    # connecté à BigQuery (voir section 5)
```

## 5. Configuration `profiles.yml`

Windows : `C:\Users\<user>\.dbt\profiles.yml`

```yaml
p3_dbt:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: <votre-id-projet-gcp>
      dataset: p3_analytics
      keyfile: ../cle_bigquery.json
      threads: 1
      location: US # mettre la location comme elle a été mise dans bigquery, je recommande US
      priority: interactive
```

Tester :

```bash
cd p3_dbt
dbt debug
```

Résultat attendu : `All checks passed!`

## 6. Architecture des modèles et création des fichiers

- `models/staging/` : nettoyage + structuration des données brutes.
- `models/intermediate/` : logique métier.
- `models/marts/` : tables finies pour BI.

**Où créer les fichiers :**
1. Crée le dossier `staging/` à l'intérieur de `models/` s'il n'existe pas.
2. Crée `sources.yml` et `stg_users.sql` dedans.
3. Même logique pour `intermediate/` et `marts/`.

### 6.1 Déclaration source

**Fichier à créer :** `models/staging/sources.yml`

```yaml

version: 2
sources:
  - name: api_source
    database: <votre-id-projet-gcp>
    schema: raw_data
    tables:
      - name: raw_users
```

### 6.2 Exemple modèle staging

**Fichier à créer :** `models/staging/stg_users.sql`

```sql
with raw as (
  select *
  from {{ source('api_source', 'raw_users') }}
)

select
  id as user_id,
  upper(trim(name)) as name,
  cast(age as int64) as age,
  timestamp(parse_datetime(created_at, '%Y-%m-%dT%H:%M:%S')) as created_at
from raw
```

**Fichier à créer :** `models/staging/schema.yml`

```yaml
version: 2
models:
  - name: stg_users
    description: "Données brutes soignées"
    columns:
      - name: user_id
        description: "Identifiant unique utilisateur"
```

## 7. Macro `generate_schema_name`

**Fichier à créer :** `macros/generate_schema_name.sql`

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name | trim }}
  {%- endif -%}
{%- endmacro %}
```

**À modifier dans :** `dbt_project.yml`

```yaml
models:
  p3_dbt:
    +schema: "{{ generate_schema_name(None, this) }}"
    staging:
      +schema: staging
    intermediate:
      +schema: intermediate
    marts:
      +schema: marts
```

## 8. Commandes dbt clés

- `dbt run`
- `dbt test`
- `dbt docs generate && dbt docs serve`

## 9. Vérification des rôles et droits (détaillé)

### 9.1 Dans GCP Console (IAM) - les clics précis
1. Ouvrir la console GCP et sélectionner le bon projet.
2. Aller sur Menu > IAM & Admin > IAM.
3. Dans la liste, trouver le compte de service utilisé (`<service-account>@<projet>.iam.gserviceaccount.com`).
4. Cliquer sur l’icône crayon à droite pour modifier.
5. Vérifier que les rôles suivants sont présents :
   - BigQuery Data Editor
   - BigQuery Job User
   - BigQuery User
   - (optionnel) BigQuery Admin pour tests/deploiement complet.
6. Si un rôle manque : cliquer sur + Ajouter un autre rôle > rechercher et sélectionner > Enregistrer.

### 9.2 Dans GCP Console (BigQuery Dataset) - les clics précis
1. Ouvrir Menu > BigQuery.
2. Dans l’arborescence, sélectionner le dataset concerné (raw_data, p3_analytics, etc).
3. Cliquer sur les trois points à droite du dataset > Autorisations.
4. Cliquer sur + Ajouter principal.
5. Saisir le compte de service, puis choisir le rôle `BigQuery Data Editor` et Enregistrer.
6. Vérifier que le compte de service apparaîsse bien avec le rôle.

### 9.3 Cas réels de conflits repérés (tes retours)
- Conflit région : `Dataset not found in location EU` (dataset situé europe-west9 / tu as `location: EU` par défaut). Solution : réécrire `location` dans `profiles.yml` à europe-west9.
- Dataset manquant même existant : mauvais projet configuré dans `profiles.yml` ou dataset dans un autre projet.
- Toutes les tables finissent dans `p3_analytics` : `dbt_project.yml` avec plus de `+schema` pour staging/marts.
- `Access Denied` sur requêtes : compte de service pas dans `BigQuery Data Editor` du dataset.

### 9.4 Reprendre ta logique (vérifie à l’écran ET dans le YAML)
- `profiles.yml` :
  - `project` = projet GCP réel
  - `dataset` = p3_analytics (ou autre défini)
  - `location` = emplacment exact du dataset
- `dbt_project.yml` :
  - `models:` pour staging/intermediate/marts
  - `+schema` correspond aux datasets
- En GUI : dataset > autorisations > compte service rôle Data Editor + Job User.

## 10. Erreurs fréquentes et solutions rapides

**Erreur : `Dataset not found in location EU`**
- Tu as des données à europe-west9 mais `profiles.yml` dit location: EU.
- Solution : change `location: europe-west9` dans `profiles.yml`.

**Erreur : `p3_analytics was not found`**
- dbt cherche le dataset mais il n'existe pas.
- Solution : crée-le dans BigQuery avec la même région que `raw_data`.

**Erreur : `Access Denied` ou `Permission denied`**
- Le compte de service n'a pas accès aux datasets.
- Solution : Menu > BigQuery > dataset > trois points > Autorisations > + Ajouter principal > compte service > rôle `BigQuery Data Editor` > Enregistrer.

**Erreur : toutes les tables finissent dans `p3_analytics`**
- dbt ne range pas staging/marts séparément.
- Solution : vérifie `dbt_project.yml` et que tu as les lignes `+schema: staging`, `+schema: intermediate`, `+schema: marts`.


## 11. Checklist finale

- `dbt debug` réussi (`All checks passed!`)
- `dbt run` réussi
- `dbt test` réussi
- destinations vérifiées :
  - `raw_data`: ingestion brute
  - `staging`, `intermediate`, `marts`: transformation

## 12. Conseils pratiques

- garder secrets (`.env`, `profiles.yml`) hors du dépôt Git
- versionner `models/`, `macros/`, `sources.yml`
- nommage clair des datasets et tables

