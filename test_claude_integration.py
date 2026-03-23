#!/usr/bin/env python3
"""
Script de test pour vérifier que rag_search.py fonctionne
avec la nouvelle intégration Claude + allergies
"""

import os
import sys
from rag_search import RAGSearchEngine

# Configuration
PROJECT_ID = "projet-3-wild"
DATASET = "marts"
MODEL_NAME = "mon_modele_ia"
VECTORIZED_TABLE = "table_recettes_vectorisees"
CREDENTIALS_PATH = "./cle_bigquery.json"

print("\n" + "="*60)
print("TEST: RAG Search avec Claude Integration")
print("="*60)

# Créer l'engine
print("\n[SETUP] Initializing RAG Engine...")
engine = RAGSearchEngine(
    project_id=PROJECT_ID,
    dataset=DATASET,
    model_name=MODEL_NAME,
    vectorized_table=VECTORIZED_TABLE,
    credentials_path=CREDENTIALS_PATH
)
print("[OK] Engine initialized")

# TEST 1: Recherche simple
print("\n" + "="*60)
print("TEST 1: Simple recipe search (no allergies)")
print("="*60)

try:
    results = engine.search(
        query_text="un plat chaud et réconfortant, avec des légumes",
        top_k=3
    )
    print(f"\n[RESULTS] Found {len(results)} recipes")
    
    if results:
        first = results[0]
        base = first.get('base', {})
        title = base.get('titre', 'N/A')
        distance = first.get('distance', 'N/A')
        print(f"[TOP1] {title} (distance: {distance})")
    
except Exception as e:
    print(f"[ERROR] Test 1 failed: {e}")
    sys.exit(1)

# TEST 2: Recherche avec allergies (Si Claude key est setup)
if os.environ.get('ANTHROPIC_API_KEY'):
    print("\n" + "="*60)
    print("TEST 2: Recipe search with allergies via Claude")
    print("="*60)
    
    try:
        # Claude extrait allergies
        print("\n[CLAUDE] Extracting avoid ingredients...")
        where_clause = engine.extract_allergies_with_claude(
            dish_description="un plat facile et rapide",
            allergies="fromage, oeufs, produits_laitiers"
        )
        
        # Recherche avec filtrage
        print("\n[SEARCH] Searching with filters...")
        results = engine.search(
            query_text="un plat facile et rapide",
            top_k=5,
            where_clause=where_clause
        )
        
        print(f"\n[RESULTS] Found {len(results)} recipes")
        if results:
            first = results[0]
            base = first.get('base', {})
            title = base.get('titre', 'N/A')
            distance = first.get('distance', 'N/A')
            print(f"[TOP1] {title} (distance: {distance})")
        
    except Exception as e:
        print(f"[ERROR] Test 2 failed: {e}")
        print("[INFO] This might be expected if ANTHROPIC_API_KEY is not valid")
else:
    print("\n" + "="*60)
    print("SKIPPED TEST 2: Claude integration")
    print("(ANTHROPIC_API_KEY not set)")
    print("="*60)

print("\n" + "="*60)
print("TESTS COMPLETED")
print("="*60 + "\n")
