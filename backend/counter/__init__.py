"""FREK Counter — Compteur souverain universel.

Module additif, namespace `/api/core/count*` (sans toucher core/).

Doctrine integree :
  - Le Porteur ne paie jamais et ne voit jamais de transaction.
  - Le Pro (kiltikonet, KORA, FMS, CFA MANS, Cook & Food, Good Mood,
    CVL Agro, CIP Foundation, Laurent.ia) consomme du JCC par appel.
  - Comptage universel : tout flux humain (presence, ecoute, formation,
    vote, achat traceable, archive...) entre par ce point unique.

Sources reconnues :
  kiltikonet, kora, fms, cfa_mans, cook_food, good_mood, cvl_agro,
  cip_foundation, laurent_ia.

L'endpoint POST /api/core/count :
  - Genere un FREK-ID si external_ref inconnu (mapping deterministe via hash)
  - Incremente le score selon la regle (action, context, source)
  - Idempotent sur idempotency_key
  - Ne retourne jamais de PII
"""
