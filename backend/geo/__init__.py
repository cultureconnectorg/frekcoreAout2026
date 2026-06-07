"""FREK Geo — Couche geolocalite souveraine.

Module additif, namespace /api/geo/*. Aucune dependance externe payante.

Stacks :
  - Plus Code (Open Location Code, Apache 2.0, lib openlocationcode)
  - H3 (Uber, Apache 2.0, hex spatial indexing)
  - Geohash (public domain, encoding local)
  - Nominatim (OSM, public free service, reverse-geocoding optionnel)
  - NASA GIBS / EOX Sentinel-2 cloudless (satellite imagery gratuite, no auth)

Stockage :
  - frek_geo_consent : {frek_id, granted_at, level, revoked_at}
  - frek_geo_observations : {frek_id, lat, lon, accuracy_m, plus_code,
                             h3_9, h3_12, geohash_8, country, city,
                             observed_at, source_event_id, idempotency_key}
"""
