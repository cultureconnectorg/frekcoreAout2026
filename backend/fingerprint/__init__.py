"""FREK Cultural Fingerprint Layer (CFL) — Phase 5.

Empreinte culturelle souveraine multi-couche, propriete exclusive CVLN.
Opt-in segmente par couche. Chaque signal capture respecte le consentement
explicite du porteur. Aucune PII civile. Tout hashe/normalise.

Couches :
- cadence    : velocite, frequence, patterns horaires (a partir de frek_events)
- affinity   : vecteur d'affinite culturelle (feature hashing 64-dim)
- device     : empreinte d'appareil (canvas/fonts/WebGL hash, fourni par le client)
- social     : co-presence avec d'autres FREK dans le meme event_id
- anomaly    : detection bot/replay (z-score + collisions device)
- coupling   : couplage online-offline (NFC scan + verification web)
- linguistic : style d'ecriture (stub — pas de texte dans FREKCORE pour le moment)
"""
