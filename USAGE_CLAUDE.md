# 🤖 Utiliser rag_search.py avec Claude API

## Prérequis

Tu as besoin de :
1. **Clé Claude** (déjà mentionné que tu l'as ✅)
2. **Variable d'environnement** `ANTHROPIC_API_KEY` configurée

### Configurer ta clé Claude

#### Option 1 : Variable d'environnement (recommandé)

**Windows PowerShell** :
```powershell
$env:ANTHROPIC_API_KEY = "votre-clé-ici"
```

**Windows CMD** :
```cmd
set ANTHROPIC_API_KEY=votre-clé-ici
```

**Linux/Mac** :
```bash
export ANTHROPIC_API_KEY="votre-clé-ici"
```

#### Option 2 : Fichier `.env` (pour plus tard)

Crée un fichier `.env` à la racine du projet :
```
ANTHROPIC_API_KEY=votre-clé-ici
GOOGLE_APPLICATION_CREDENTIALS=./cle_bigquery.json
```

Puis modifie le script pour load le .env :
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Flux du programme

### 1️⃣ Démarrer le script

```bash
python rag_search.py
```

### 2️⃣ Le script te pose des questions

```
============================================================
==== MOTEUR DE RECHERCHE DE RECETTES (RAG + Claude) ====
============================================================

[PLAT] Quel type de plat cherches-tu? (ex: 'un plat chaud et réconfortant')
> un plat léger et sain
```

### 3️⃣ Déclarer les allergies

```
[ALLERGIES] Allergies/ingrédients à ÉVITER? (ex: 'fromage, noix' ou 'aucun')
> fromage, œufs, produits laitiers
```

**Ce qui se passe en arrière-plan** :
- Claude reçoit ta description + allergies
- Claude retourne une WHERE clause : `ingredients NOT LIKE '%fromage%' AND ingredients NOT LIKE '%oeufs%' AND ingredients NOT LIKE '%produits_laitiers%'`
- BigQuery applique ce filtre avant de chercher

### 4️⃣ Nombre de résultats

```
[RESULTATS] Combien de résultats? (par défaut: 5)
> 3
```

### 5️⃣ Résultats

```
[RECHERCHE] Recherche: 'un plat léger et sain'
   Filtre: ingredients NOT LIKE '%fromage%' AND ingredients NOT LIKE '%oeufs%' AND ...
   Top-3 résultats

1. Salade Verte
   Distance: 0.8234
   Ingrédients: salade, tomates, concombre, vinaigrette

2. Soupe de Légumes
   Distance: 0.8567
   Ingrédients: carottes, oignons, céleri, bouillon

3. Poisson Grillé
   Distance: 0.8901
   Ingrédients: poisson blanc, citron, thym, olive oil
```

---

## Types de conversations

### Exemple 1 : Chercher sans allergies

```
[PLAT] Quel type de plat?
> un plat réconfortant

[ALLERGIES] Allergies?
> aucun  ← ou simplement appuyer sur Entrée

[RESULTATS] Résultats?
> 5

[SUITE] Continuer?
> non
```

### Exemple 2 : Allergies multiples

```
[PLAT] Quel type de plat?
> plat végétarien sans noix

[ALLERGIES] Allergies?
> amendel, cacahuètes, noix, poisson

[RESULTATS] Résultats?
> 8

[SUITE] Continuer?
> oui
```

---

## Comprendre la distance

| Distance | Signification |
|----------|---------------|
| 0.7 - 0.8 | ✅ **Excellent match** |
| 0.8 - 0.9 | ✅ **Bon match** |
| 0.9 - 1.0 | ⚠️ **Acceptable** |
| > 1.0 | ❌ **Pauvre match** |

**Rappel** : Distance basse = résultat meilleur!

---

## En Python (sans interface interactive)

Tu peux aussi l'utiliser dans du code Python :

```python
from rag_search import RAGSearchEngine

engine = RAGSearchEngine(
    project_id="projet-3-wild",
    dataset="marts",
    model_name="mon_modele_ia",
    vectorized_table="table_recettes_vectorisees"
)

# Extraire allergies avec Claude
allergies = "fromage, oeufs"
where_clause = engine.extract_allergies_with_claude(
    dish_description="un plat léger",
    allergies=allergies
)

# Chercher
results = engine.search(
    query_text="un plat léger et sain",
    top_k=5,
    where_clause=where_clause
)

# Accéder aux résultats
for result in results:
    base_data = result.get('base', {})
    titre = base_data.get('titre')
    distance = result.get('distance')
    print(f"{titre} - Distance: {distance}")
```

---

## Dépannage

### ❌ `AuthenticationError: invalid_request_error`
**Cause** : ANTHROPIC_API_KEY invalide ou non définie
**Solution** : Vérifie ta clé et la variable d'environnement

### ❌ `ModuleNotFoundError: No module named 'anthropic'`
**Cause** : anthropic SDK pas installé
**Solution** : `pip install anthropic`

### ❌ `No results found` quand tu utilises des allergies complexes
**Cause** : Claude génère une WHERE clause qui élimine tout
**Solution** : Utilise des allergies plus spécifiques

---

## Fichier de code exemple (test_claude.py)

```python
#!/usr/bin/env python3
import os
from rag_search import RAGSearchEngine

# Configuration
os.environ['ANTHROPIC_API_KEY'] = 'votre-clé-ici'  # À remplacer!

engine = RAGSearchEngine(
    project_id="projet-3-wild",
    dataset="marts",
    model_name="mon_modele_ia",
    vectorized_table="table_recettes_vectorisees",
    credentials_path="./cle_bigquery.json"
)

# Test 1: Recherche sans allergies
print("\n=== TEST 1 : Recherche simple ===")
results = engine.search("un plat chaud et réconfortant", top_k=3)

# Test 2: Recherche avec allergies (Claude)
print("\n=== TEST 2 : Avec allergies (Claude) ===")
where = engine.extract_allergies_with_claude(
    "un plat facile et rapide",
    "fromage, oeufs"
)
results = engine.search("un plat facile et rapide", top_k=5, where_clause=where)
```

Sauvegarde ce fichier et test-le avec : `python test_claude.py`
