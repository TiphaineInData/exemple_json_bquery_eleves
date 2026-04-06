# 🔗 Liaison GitHub x Discord via Webhook

Ce guide explique comment connecter ton dépôt GitHub à un salon Discord pour recevoir des notifications en temps réel (Commits, Pushes, etc.).

---

## 🛠️ 1. Configuration sur Discord (Le Récepteur)

C'est ici qu'on crée "l'antenne" qui va recevoir les messages.

1.  Ouvre les **Paramètres du serveur** (ou les paramètres d'un salon spécifique).
2.  Va dans l'onglet **Intégrations**.
3.  Clique sur **Webhooks**, puis sur **Nouveau Webhook**.
4.  **Configuration du Webhook :**
    * **Nom :** Donne-lui un nom (ex: `Bot FDJ GitHub`).
    * **Salon :** Choisis le salon précis où les messages doivent s'afficher (ex: `#logs-projet`).
5.  Clique sur **Copier l'URL du webhook**.
6.  Clique sur **Enregistrer**.

---

## ⚙️ 2. Configuration sur GitHub (L'Émetteur)

C'est ici qu'on branche ton code sur l'antenne Discord.

1.  Va sur ton dépôt GitHub, puis clique sur l'onglet **Settings** (Paramètres).
2.  Dans le menu latéral gauche, clique sur **Webhooks**.
3.  Clique sur le bouton vert **Add webhook**.
4.  **Champs à remplir (ATTENTION ICI) :**
    * **Payload URL :** Colle l'URL copiée sur Discord.
    * ⚠️ **Étape CRUCIALE :** Ajoute `/github` à la toute fin de l'URL.
        > *Exemple :* `https://discord.com/api/webhooks/12345/ABCDE.../github`
    * **Content type :** Sélectionne impérativement `application/json`.
    * **SSL verification :** Laisse sur `Enable SSL verification`.
5.  **Événements :** * Choisis `Just the push event` pour ne pas être spammé.
    * Ou `Send me everything` si tu veux voir toute l'activité.
6.  Vérifie que la case **Active** est cochée et clique sur **Add webhook**.

---

## ✅ 3. Vérification & Débogage

### Comment savoir si ça marche ?
Fais un `git push` de ton code. Si tout est bon, un message apparaît instantanément sur Discord.

### Ça ne marche pas ?
Retourne dans GitHub > **Settings** > **Webhooks** et regarde la section **Recent Deliveries** en bas :

* 🟢 **Code 204 / 200** : Tout est parfait. Cherche le message dans le salon Discord sélectionné.
* 🔴 **Code 400 / 404** : Tu as probablement oublié de rajouter `/github` à la fin de l'URL ou tu n'as pas mis le format `application/json`.

---

> [!IMPORTANT]
> **Sécurité :** Ne partage jamais l'URL de ton Webhook publiquement. Si quelqu'un l'a, il peut envoyer n'importe quel message sur ton serveur Discord.