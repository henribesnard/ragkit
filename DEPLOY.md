# Guide de Déploiement

Pour générer l'exécutable (.exe) via GitHub Actions :

1.  **Committez** tous les changements :
    ```bash
    git add .
    git commit -m "Feat: Ingestion Slice ready"
    ```

2.  **Taguez** une nouvelle version (ex: v3.0.0-alpha1) :
    ```bash
    git tag v3.0.0-alpha1
    ```

3.  **Pushez** le code et le tag :
    ```bash
    git push origin ragkit_v3 --tags
    ```

4.  **Vérifiez** sur GitHub :
    - Allez dans l'onglet **Actions** du repo.
    - Une workflow "Release" devrait démarrer.
    - Une fois fini, l'exécutable sera disponible dans l'onglet **Releases**.
