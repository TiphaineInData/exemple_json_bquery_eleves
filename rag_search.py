#!/usr/bin/env python3
"""
RAG Search Interface for BigQuery + Vertex AI
Permet de faire des recherches vectorielles depuis Python
"""

from google.cloud import bigquery
import os
from typing import List, Dict, Optional


class RAGSearchEngine:
    """Moteur de recherche RAG utilisant BigQuery + Vertex AI"""
    
    def __init__(
        self,
        project_id: str,
        dataset: str,
        model_name: str,
        vectorized_table: str,
        credentials_path: str = None
    ):
        """
        Initialiser le moteur RAG
        
        Args:
            project_id: ID du projet GCP (ex: "projet-3-wild")
            dataset: Dataset contenant le modèle (ex: "marts")
            model_name: Nom du modèle remote (ex: "mon_modele_ia")
            vectorized_table: Nom de la table vectorisée (ex: "table_recettes_vectorisees")
            credentials_path: Chemin vers la clé JSON (optionnel, utilise .env par défaut)
        """
        # Charger les credentials
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        elif 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
            # Chercher cle_bigquery.json par défaut
            default_path = './cle_bigquery.json'
            if os.path.exists(default_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = default_path
        
        # Initialiser BigQuery client
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset = dataset
        self.model_name = model_name
        self.vectorized_table = vectorized_table
    
    def setup_model(self, connection_id: str, region: str = "EU") -> None:
        """
        Créer le modèle remote (une fois!)
        
        Args:
            connection_id: ID de la connexion BigQuery ↔ Vertex AI (ex: "connexion-ia")
            region: Région (ex: "EU" ou "US")
        """
        query = f"""
        CREATE OR REPLACE MODEL `{self.project_id}.{self.dataset}.{self.model_name}`
        REMOTE WITH CONNECTION `{region}.{connection_id}`
        OPTIONS (ENDPOINT = 'text-embedding-004');
        """
        print(f"✓ Création du modèle {self.model_name}...")
        self.client.query(query).result()
        print("✓ Modèle créé!")
    
    def vectorize_table(self, source_table: str, text_columns: List[str]) -> None:
        """
        Vectoriser une table (une fois!)
        
        Args:
            source_table: Table source (ex: "projet-3-wild.raw.recettes_brutes")
            text_columns: Colonnes à combiner (ex: ["titre", "ingredients"])
        """
        # Créer la partie CONCAT
        concat_part = ' " " '.join(text_columns)
        concat_sql = f'CONCAT({concat_part})'
        
        # Créer la liste des colonnes à garder
        columns_select = ', '.join(text_columns)
        
        query = f"""
        CREATE OR REPLACE TABLE `{self.project_id}.{self.dataset}.{self.vectorized_table}` AS
        SELECT 
            {columns_select},
            ml_generate_embedding_result AS vecteur_ia
        FROM ML.GENERATE_EMBEDDING(
            MODEL `{self.project_id}.{self.dataset}.{self.model_name}`,
            (
                SELECT 
                    {columns_select},
                    {concat_sql} AS content
                FROM `{source_table}`
            ),
            STRUCT(TRUE AS flatten_json_output)
        );
        """
        print(f"✓ Vectorisation de {source_table}...")
        print("  (cette opération peut prendre quelques minutes...)")
        self.client.query(query).result()
        print("✓ Table vectorisée créée!")
    
    def search(
        self,
        query_text: str,
        top_k: int = 5,
        where_clause: str = None
    ) -> List[Dict]:
        """
        Faire une recherche RAG
        
        Args:
            query_text: Question (ex: "un plat chaud et réconfortant")
            top_k: Nombre de résultats (défaut: 5)
            where_clause: Filtre SQL optionnel (ex: "WHERE ingredients NOT LIKE '%porc%'")
        
        Returns:
            Liste de dictionnaires avec titre, ingredients, distance
        """
        # Construire la requête VECTOR_SEARCH
        where_sql = f"AND {where_clause}" if where_clause else ""
        
        query = f"""
        SELECT *
        FROM VECTOR_SEARCH(
            (
                SELECT * 
                FROM `{self.project_id}.{self.dataset}.{self.vectorized_table}`
                WHERE TRUE {where_sql}
            ), 
            'vecteur_ia',
            (
                SELECT ml_generate_embedding_result 
                FROM ML.GENERATE_EMBEDDING(
                    MODEL `{self.project_id}.{self.dataset}.{self.model_name}`,
                    (SELECT "{query_text}" AS content),
                    STRUCT(TRUE AS flatten_json_output)
                )
            ),
            top_k => {top_k}
        )
        ORDER BY distance ASC;
        """
        
        print(f"\n🔍 Recherche: '{query_text}'")
        if where_clause:
            print(f"   Filtre: {where_clause}")
        print(f"   Top-{top_k} résultats\n")
        
        # Exécuter la requête
        try:
            results = self.client.query(query).result()
            
            # Convertir en liste de dictionnaires
            rows = []
            for row in results:
                rows.append(dict(row))
            
            # Afficher les résultats
            if rows:
                for i, row in enumerate(rows, 1):
                    # Les données sont dans la colonne STRUCT 'base'
                    base_data = row.get('base', {})
                    if isinstance(base_data, dict):
                        titre = base_data.get('titre', 'N/A')
                        ingredients = base_data.get('ingredients', 'N/A')
                    else:
                        titre = 'N/A'
                        ingredients = 'N/A'
                    
                    distance = row.get('distance', 'N/A')
                    
                    # Formatter la distance
                    if isinstance(distance, (int, float)):
                        distance_str = f"{distance:.4f}"
                    else:
                        distance_str = str(distance)
                    
                    print(f"{i}. {titre}")
                    print(f"   Distance: {distance_str}")
                    print(f"   Ingrédients: {ingredients}")
                    print()
            else:
                print("❌ Aucun résultat trouvé.")
            
            return rows
        
        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {e}")
            return []


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    # Configuration
    PROJECT_ID = "projet-3-wild"
    DATASET = "marts"
    MODEL_NAME = "mon_modele_ia"
    VECTORIZED_TABLE = "table_recettes_vectorisees"
    CONNECTION_ID = "connexion-ia"
    REGION = "EU"
    
    # Source table (celle qu'on va vectoriser)
    SOURCE_TABLE = "projet-3-wild.raw.recettes_brutes"
    TEXT_COLUMNS = ["titre", "ingredients"]  # Colonnes à combiner
    
    # ========================================================================
    # SETUP (à faire UNE SEULE FOIS)
    # ========================================================================
    
    # Créer l'engine
    engine = RAGSearchEngine(
        project_id=PROJECT_ID,
        dataset=DATASET,
        model_name=MODEL_NAME,
        vectorized_table=VECTORIZED_TABLE,
        credentials_path="./cle_bigquery.json"  # Optionnel si .env existe
    )
    
    # Décommenter pour créer le modèle (première fois seulement)
    # engine.setup_model(connection_id=CONNECTION_ID, region=REGION)
    
    # Décommenter pour vectoriser la table (première fois seulement)
    # engine.vectorize_table(
    #     source_table=SOURCE_TABLE,
    #     text_columns=TEXT_COLUMNS
    # )
    
    # ========================================================================
    # RECHERCHES (à chaque fois qu'on veut chercher)
    # ========================================================================
    
    # Recherche simple
    results = engine.search(
        query_text="un plat chaud et réconfortant, avec des légumes",
        top_k=3
    )
    
    # Recherche avec filtre
    results_filtered = engine.search(
        query_text="un plat facile et rapide",
        top_k=5,
        where_clause="ingredients NOT LIKE '%produits_laitiers%'"
    )
    
    # Accéder aux résultats en Python
    print("\n=== Résultats Python ===")
    if results:
        first_result = results[0]
        base_data = first_result.get('base', {})
        if isinstance(base_data, dict):
            titre = base_data.get('titre', 'N/A')
        else:
            titre = 'N/A'
        distance = first_result.get('distance')
        print(f"Meilleur résultat: {titre}")
        print(f"Distance: {distance}")
