# RAG Search avec Claude + BigQuery

Interface Python pour faire des recherches de recettes intelligentes utilisant :
- **BigQuery** : stockage vectorisé
- **Vertex AI** : embeddings semantic
- **Claude** : extraction intelligente des allergies

## 🚀 Démarrage rapide

### 1. Installation

```bash
pip install google-cloud-bigquery anthropic
```

### 2. Configuration

**Configurer ta clé Claude** :

```bash
# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-xxxxx"

# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**Ou via fichier `.env`** (à la racine du projet) :
```
ANTHROPIC_API_KEY=sk-ant-xxxxx
GOOGLE_APPLICATION_CREDENTIALS=./cle_bigquery.json
```

**Vérifier que c'est bon** :
```powershell
# PowerShell
[Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY', 'User')

# Ou directement en Python
python -c "import os; print(os.environ.get('ANTHROPIC_API_KEY', 'NOT SET'))"
```

### 3. Utiliser l'interface interactive

```bash
python rag_search.py
```

Le programme te pose des questions une par une :

```
============================================================
==== MOTEUR DE RECHERCHE DE RECETTES (RAG + Claude) ====
============================================================

[PLAT] Quel type de plat cherches-tu? (ex: 'un plat chaud et réconfortant')
> un plat végétarien et sain

[ALLERGIES] Allergies/ingrédients à ÉVITER? (ex: 'fromage, noix' ou 'aucun')
> fromage, noix, arachides

[RESULTATS] Combien de résultats? (par défaut: 5)
> 3

[CLAUDE] Extraction des ingrédients à éviter...
[CLAUSE] ingredients NOT LIKE '%fromage%' AND ingredients NOT LIKE '%noix%' AND ingredients NOT LIKE '%arachides%'

[RECHERCHE] Recherche en cours...

1. Salade de Légumes
   Distance: 0.8234
   Ingrédients: laitue, tomates, concombre, vinaigrette

2. Soupe de Pois
   Distance: 0.8567
   Ingrédients: pois chiches, carottes, oignon, épices

[SUITE] Veux-tu essayer une autre recherche? (oui/non)
> non
```

---

## 📚 Documentation

- **[rag_bigquery.md](rag_bigquery.md)** : Guide complet BigQuery + Vertex AI (setup, SQL, VECTOR_SEARCH)
- **[rag_search.py](rag_search.py)** : Code source (classe RAGSearchEngine)

---

## 🧠 Comment ça fonctionne avec Claude

Quand tu rentres tes allergies, voici le flux :

```
1. Utilisateur tape : "fromage, noix, œufs"
   ↓
2. Claude extrait une WHERE clause SQL :
   "ingredients NOT LIKE '%fromage%' AND ingredients NOT LIKE '%noix%' ..."
   ↓
3. BigQuery l'applique AVANT la recherche vectorielle
   ↓
4. VECTOR_SEARCH ne retourne QUE les recettes sans ces ingrédients
   ↓
5. Résultats affichés (filtrés + classés par similarité)
```

**Avantage** : Tu combines puissance AI (Claude) + filtrage intelligent (SQL) + recherche sémantique (BigQuery)

---

## 📖 Exemples d'utilisation

```python
from rag_search import RAGSearchEngine

engine = RAGSearchEngine(
    project_id="projet-3-wild",
    dataset="marts",
    model_name="mon_modele_ia",
    vectorized_table="table_recettes_vectorisees"
)

# Avec allergies (Claude extrait automatiquement)
where_clause = engine.extract_allergies_with_claude(
    dish_description="un plat léger",
    allergies="fromage, oeufs"
)

# Chercher
results = engine.search(
    query_text="un plat léger et sain",
    top_k=5,
    where_clause=where_clause
)

# Accéder aux résultats
for result in results:
    base = result.get('base', {})
    titre = base.get('titre')
    distance = result.get('distance')
    print(f"{titre} - {distance:.4f}")
```

---

## 📊 Comprendre la distance

- **0.70-0.80** = ✅ Excellent match
- **0.80-0.90** = ✅ Bon match
- **0.90-1.00** = ⚠️ Acceptable
- **> 1.00** = ❌ Mauvais match

**Rappel** : Distance basse = résultat meilleur!

---

## 🧪 Tests

Tester sans interface interactive :

```bash
python test_claude_integration.py
```

---

## 🆘 Dépannage

### ❌ `AuthenticationError`
→ Vérifiez votre `ANTHROPIC_API_KEY`

### ❌ `ModuleNotFoundError: anthropic`
→ `pip install anthropic`

### ❌ `Permission Denied` (BigQuery)
→ Vérifiez que votre compte de service a les droits `Utilisateur Vertex AI`

### ❌ Les résultats disparaissent quand j'ajoute des allergies
→ Les allergies sont trop restrictives. Claude génère une WHERE clause qui élimine tout.

---

## 📋 Fichiers du projet

```
├── rag_search.py                 # Code principal (RAGSearchEngine + interface)
├── rag_bigquery.md              # Guide BigQuery/Vertex AI complet
├── USAGE_CLAUDE.md              # Guide Claude & allergies
├── test_claude_integration.py   # Tests de validation
├── cle_bigquery.json            # Credentials GCP (à ne pas partager!)
└── README.md                    # Ce fichier
```

---

## 🎯 Comment ça marche en arrière-plan

```
1. Utilisateur input
   ↓
2. Claude extrait allergies → WHERE clause SQL
   ↓
3. BigQuery filtre et vectorise la requête
   ↓
4. VECTOR_SEARCH compare et retourne top-k
   ↓
5. Résultats affichés avec distances
```

---

## 💡 Cas d'usage

✅ Trouver des recettes adaptées à des allergies  
✅ Chercher par description générale ("un truc rapide")  
✅ Combiner filtres SQL + recherche sémantique  
✅ Intégrer dans une appli (API-like)

---

Créé pour les étudiants du projet-3-wild. Happy coding! 🚀
