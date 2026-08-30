"""FREK Registry — catalogue officiel des objets culturels CVLN (Bloc 1).

Namespaces couverts (v1) : frek.artist, frek.track, frek.album, frek.work,
frek.certificate, frek.organization, frek.wallet, frek.event.

Ce module est additif et sans etat (pas de dependance MongoDB) : il charge
des schemas JSON versionnes depuis le disque et les sert / valide contre eux.
"""
