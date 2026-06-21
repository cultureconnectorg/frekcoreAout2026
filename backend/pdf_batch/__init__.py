"""FREK PDF Batch — generation badges/cartes PDF self-service.

Module additif, namespace /api/v1/pdf-batch/*. Reutilisable pour evenements
futurs sans intervention developpeur.

Architecture :
  - Lecture seule sur `badges` (existant) — aucune modification de schema
  - Template Twina PDF parametrable (titre, couleurs, footer)
  - Generation ZIP de N PDFs (1 PDF par badge)
  - Telechargement direct, pas de stockage durable cote serveur
"""
