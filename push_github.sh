#!/bin/bash
cd /c/Users/tipha/Documents/json_to_bigquery

echo "=== Initialisation git ==="
git init
echo "OK: git init"

echo "=== Config utilisateur ==="
git config user.name "Tiph"
git config user.email "tiph@example.com"
echo "OK: config user"

echo "=== Vérification .gitignore ==="
ls -la .gitignore
echo "OK: .gitignore existe"

echo "=== Ajout des fichiers ==="
git add .
echo "OK: git add"

echo "=== Commit ==="
git commit -m "docs: ajout guide dbt et config initiale"
echo "OK: commit"

echo "=== Renommage branche ==="
git branch -M main
echo "OK: main branch"

echo "=== Ajout remote ==="
git remote add origin https://github.com/TiphaineInData/exemple_json_bquery_eleves.git
echo "OK: remote add"

echo "=== Push vers GitHub ==="
git push -u origin main
echo "OK: push complété"

echo "=== Vérification finale ==="
git log --oneline
git remote -v
