# Guide RAG et Vectorisation avec BigQuery

Ce guide t'explique comment créer un moteur de recherche intelligent (RAG = Retrieval Augmented Generation) en utilisant BigQuery + Vertex AI pour transformer du texte en nombres (embedding), puis chercher les résultats les plus pertinents.

## 🎯 Vue d'ensemble

- **Vertex AI** = l'IA Google (contient les modèles de langage)
- **BigQuery** = la base de données (stocke les données et appelle l'IA via SQL)
- **Embedding** = conversion d'un texte en liste de 768 nombres
- **RAG** = combinaison de recherche vectorielle + filtres SQL = résultats sur-mesure

---

## Étape 1 : Configurer la connexion BigQuery ↔ Vertex AI

### 1.1 Créer la connexion (interface GCP)

**Lieu d'action** : https://console.cloud.google.com/bigquery

1. Clique sur le menu **+ AJOUTER** (haut gauche, près de "Explorer")
2. Choisis **Connexions à des sources de données externes**
3. Dans le panneau qui s'ouvre :
   - **Type de source** : `Modèles de machine learning et analyse distante`
   - **ID de connexion** : donne un nom simple (ex : `connexion-ia`)
   - **Région** : choisis celle de ton dataset (ex : `EU` ou `US`)
4. Clique **Créer la connexion**

### 1.2 Récupérer l'ID du compte de service

1. Dans BigQuery, va à **External Connections** (côté gauche)
2. Finds ta connexion créée
3. Clique dessus
4. À droite, trouve **ID de compte de service** : c'est une longue adresse type
   ```
   bqcx-123456-xyzw@gcp-sa-bigquery-condel.iam.gserviceaccount.com
   ```
5. **Copie cette adresse**

### 1.3 Donner les droits IAM (= 90% des erreurs viennent d'ici!)

1. Va à https://console.cloud.google.com/iam-admin/iam
2. Clique **Accorder l'accès** (en haut)
3. **Nouveaux principaux** : colle l'adresse copiée ci-dessus
4. **Attribuer des rôles** : cherche et clique `Utilisateur Vertex AI`
5. Clique **Enregistrer**

### ✅ Checklist avant de continuer

- [ ] Connexion créée dans BigQuery
- [ ] ID compte de service copié
- [ ] Rôle `Utilisateur Vertex AI` attribué dans IAM
- [ ] (attendre ~30 secondes pour que Google applique les droits)

---

## Étape 2 : Créer le modèle "Remote"

Le modèle remote est juste un **pointeur** vers l'API Vertex AI. Il n'occupe pas d'espace, il dit juste "utilise cette API pour transformer du texte en chiffres".

**Lieu d'action** : BigQuery SQL Editor

```sql
CREATE OR REPLACE MODEL `dataset.mon_modele_ia`
REMOTE WITH CONNECTION `location.ma-connexion`
OPTIONS (ENDPOINT = 'text-embedding-004');
```

**Variables à remplacer** :
- `dataset` : ton dataset (ex : `p3_analytics` ou `marts`)
- `mon_modele_ia` : le nom du modèle (ex : `gemini_embedding_model`)
- `location` : ta région (ex : `EU` ou `US`)
- `ma-connexion` : l'ID de ta connexion (ex : `connexion-ia`)

**Exemple complet** :
```sql
CREATE OR REPLACE MODEL `projet-3-wild.marts.mon_modele_ia`
REMOTE WITH CONNECTION `EU.connexion-ia`
OPTIONS (ENDPOINT = 'text-embedding-004');
```

✅ Clique **Exécuter**

---

## Étape 3 : Vectoriser tes données (Embedding)

On transforme tes données en liste de chiffres (vecteurs).

### 3.1 Table source

Suppose que tu as une table `table_brute` avec des colonnes texte comme `titre` et `ingredients`.

### 3.2 Exécuter la vectorisation

```sql
SELECT * FROM ML.GENERATE_EMBEDDING(
  MODEL `dataset.mon_modele_ia`,
  (SELECT *, CONCAT(titre, " ", ingredients) AS content FROM `table_brute`),
  STRUCT(TRUE AS flatten_json_output)
)
```

**Variables à remplacer** :
- `dataset.mon_modele_ia` : le modèle créé en Étape 2
- `table_brute` : ta vraie table source
- `titre, ingredients` : tes colonnes à combiner

**Exemple** :
```sql
SELECT * FROM ML.GENERATE_EMBEDDING(
  MODEL `projet-3-wild.marts.mon_modele_ia`,
  (SELECT *, CONCAT(titre, " ", ingredients) AS content FROM `projet-3-wild.raw.recettes_brutes`),
  STRUCT(TRUE AS flatten_json_output)
)
```

**Résultat** : une table avec colonne `ml_generate_embedding_result` (les 768 chiffres).

Pour sauvegarder cette table vectorisée :

```sql
CREATE OR REPLACE TABLE `dataset.table_recettes_vectorisees` AS
SELECT * FROM ML.GENERATE_EMBEDDING(
  MODEL `dataset.mon_modele_ia`,
  (SELECT *, CONCAT(titre, " ", ingredients) AS content FROM `table_brute`),
  STRUCT(TRUE AS flatten_json_output)
);
```

---

## Étape 4 : Faire une recherche RAG (VECTOR_SEARCH)

On pose une question et BigQuery compare avec tes données vectorisées pour trouver les résultats les plus pertinents.

### 4.1 Requête simple

```sql
SELECT 
  base.titre,
  base.ingredients,
  base.distance
FROM VECTOR_SEARCH(
  (SELECT * FROM `dataset.table_recettes_vectorisees`), 
  'vecteur_ia',
  (SELECT ml_generate_embedding_result FROM ML.GENERATE_EMBEDDING(
    MODEL `dataset.mon_modele_ia`,
    (SELECT "un plat chaud et réconfortant, avec des légumes" AS content),
    STRUCT(TRUE AS flatten_json_output)
  )),
  top_k => 5
) base;
```

**Variables à remplacer** :
- `dataset.table_recettes_vectorisees` : ta table vectorisée
- `vecteur_ia` : le nom de ta colonne d'embedding (si tu l'as renommée, ex : `ml_generate_embedding_result`)
- `dataset.mon_modele_ia` : le modèle créé en Étape 2
- `"un plat chaud et réconfortant, avec des légumes"` : ta question
- `top_k => 5` : combien de résultats tu veux

**Exemple** :
```sql
SELECT 
  base.titre,
  base.ingredients,
  base.distance
FROM VECTOR_SEARCH(
  (SELECT * FROM `projet-3-wild.marts.table_recettes_vectorisees`), 
  'vecteur_ia',
  (SELECT ml_generate_embedding_result FROM ML.GENERATE_EMBEDDING(
    MODEL `projet-3-wild.marts.mon_modele_ia`,
    (SELECT "un plat chaud et réconfortant" AS content),
    STRUCT(TRUE AS flatten_json_output)
  )),
  top_k => 3
) base;
```

### 4.2 Recherche avec filtre SQL

Tu peux filtrer **avant** la recherche vectorielle :

```sql
SELECT 
  base.titre,
  base.ingredients,
  base.distance
FROM VECTOR_SEARCH(
  (SELECT * FROM `dataset.table_recettes_vectorisees` 
   WHERE ingredients NOT LIKE '%fromage%' 
     AND ingredients NOT LIKE '%pecorino%'
     AND ingredients NOT LIKE '%parmesan%'), 
  'vecteur_ia',
  (SELECT ml_generate_embedding_result FROM ML.GENERATE_EMBEDDING(
    MODEL `dataset.mon_modele_ia`,
    (SELECT "un plat chaud et réconfortant, avec des légumes" AS content),
    STRUCT(TRUE AS flatten_json_output)
  )),
  top_k => 3
) base;
```

**Avantage** : tu combines filtrage SQL classique + recherche intelligente = résultats ciblés et rapides.

---

## � Comprendre la distance (Score de similarité)

Quand VECTOR_SEARCH retourne les résultats, chaque ligne a une colonne `distance`. Voici comment l'interpréter :

**Distance basse (proche de 0) = Résultat TRÈS pertinent ✅**
**Distance haute (proche de 1) = Résultat MOINS pertinent ❌**

### Exemple concret

Recherche : *"un plat chaud et réconfortant, avec des légumes"*

| Rang | Recette | Distance | Raison |
|------|---------|----------|--------|
| 1️⃣ | Ratatouille | **0.8751** | Beaucoup de légumes + chaud ✅ Très proche |
| 2️⃣ | Gratin Dauphinois | **0.8913** | Mit ail mais surtout crème + pommes de terre |
| 3️⃣ | Omelette | **0.9498** | Protéine chaud, peu de légumes |

**0.8751 < 0.8913** donc Ratatouille est rangée en premier = c'est le meilleur résultat!

### Comment ça marche en arrière-plan

1. Ta question = transformée en 768 chiffres (embedding)
2. Chaque recette = aussi transformée en 768 chiffres
3. BigQuery calcule la **distance euclidienne** entre ces deux listes de chiffres
4. Plus la distance est **proche de 0**, plus les vecteurs sont **similaires**

### Dans le code

```python
results = engine.search(query_text="...", top_k=3)
# Les résultats sont automatiquement triés par distance croissante
# Premier résultat = distance la plus basse = meilleur match
```

---

### ❌ Error: `Permission Denied`
**Cause** : Le compte de service n'a pas le rôle `Utilisateur Vertex AI`
**Solution** : Refais Étape 1.3 (IAM), attends 30 sec, retry

### ❌ Error: `Connection not found`
**Cause** : `<connexion-id>` ou `<region>` mal écrits
**Solution** : Copie exactement depuis BigQuery > External Connections

### ❌ Error: `Model not found`
**Cause** : Chemin du modèle incorrect ou pas encore créé
**Solution** : Refais Étape 2 d'abord

### ❌ Error: `Column 'content' not found`
**Cause** : Tu n'as pas nommé la colonne `content` dans GENERATE_EMBEDDING
**Solution** : Ajoute `AS content` après ton CONCAT

### ❌ Les résultats sont tous à distance = 1.0 ou similaire
**Cause** : Les données ne sont pas vectorisées correctement ou pas du tout
**Solution** : Vérifie que ta table `recettes_vectorisees` existe et a des embeddings

---

## 📋 Checklist complète (du début à la fin)

### Setup initial
- [ ] Connexion BigQuery ↔ Vertex AI créée
- [ ] ID compte de service copié
- [ ] Rôle `Utilisateur Vertex AI` attribué

### Modèle
- [ ] Modèle `gemini_embedding_model` créé (Étape 2)

### Données
- [ ] Table source existe (`raw_recettes`)
- [ ] Table vectorisée créée (`recettes_vectorisees`)
- [ ] La colonne `embedding` est bien présente

### Test
- [ ] Test VECTOR_SEARCH simple (Étape 4.1) fonctionne
- [ ] Test VECTOR_SEARCH avec filtre (Étape 4.2) fonctionne

---

## 🧠 Glossaire

| Terme | Définition |
|-------|-----------|
| **Embedding** | Conversion d'un texte en vecteur (liste de 768 nombres) |
| **Vecteur** | Liste de nombres qui représente le "position" d'un texte dans l'espace mathématique |
| **Distance** | Mesure d'éloignement entre deux vecteurs (0 = identiques, 1 = totalement différents) |
| **Top-K** | Retourner les K résultats les proches |
| **RAG** | Retrieval (chercher) + Augmented (boosted) + Generation = chercher les infos pertinentes puis les ajouter à l'IA pour mieux répondre |
| **Remote Model** | Modèle qui n'existe que sur une API externe (ici Vertex AI) |
| **Content** | Colonne spéciale que l'IA lit dans GENERATE_EMBEDDING (doit s'appeler `content`) |

---

## 💡 Astuces avancées

**Combiner plusieurs colonnes** :
```sql
CONCAT(titre, ' | ', ingredients, ' | ', description, ' | ', tags) AS content
```

**Créer une vue** (= raccourci pour requêtes fréquentes) :
```sql
CREATE OR REPLACE VIEW `<projet>.<dataset>.rag_search` AS
SELECT titre, ingredients, distance
FROM VECTOR_SEARCH(...)
WHERE distance < 0.3;  -- Garder que les bons résultats
```

**Ajouter un score de pertinence** :
```sql
SELECT 
  titre,
  ingredients,
  distance,
  ROUND((1 - distance) * 100, 2) AS pertinence_percent
FROM VECTOR_SEARCH(...)
ORDER BY distance ASC;
```

---

## 📚 Ressources officielles

- BigQuery ML docs : https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-intro
- Vertex AI Embeddings : https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/overview
