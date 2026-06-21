"""FREK Investor — Pulse cryptographique due diligence.

Endpoint additif `GET /api/v1/investor/pulse` qui aggrege en temps reel :
  - total FREK-IDs + total events + sources actives (depuis core + counter)
  - average_cultural_impact_score (depuis frek_count_subjects)
  - merkle_root / latest_block_hash de la FREK-Chain
  - bitcoin_block confirme (OTS upgraded count)

Ce endpoint est la **preuve cryptographique en temps reel** affichable
en due diligence : pas une slide PowerPoint, un fetch HTTP verifiable.
"""
