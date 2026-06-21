# FREK NFC Physique — Procedure terrain

## Hardware recommande

| Lecteur | Prix | OS | Recommandation |
|---|---|---|---|
| **ACR122U-A9** USB PC/SC | ~30 € | Linux/Windows/macOS | ★★★ Pour batch j-15 |
| **PN532 NFC HAT** Raspberry Pi | ~15 € | Linux | ★★ Pour atelier |
| **iPhone (NFC Tools app)** | gratuit | iOS | ★ Pour spot 1-1 |
| **Android (NFC Tools app)** | gratuit | Android | ★★ Pour spot 1-1 |

## Tags compatibles

| Tag | Capacite | Prix unite | Usage FREK |
|---|---|---|---|
| **NTAG215** | 504 bytes | ~0.30 € | ★★★ Standard FREK Card |
| **NTAG216** | 888 bytes | ~0.40 € | ★★ Si donnees enrichies futures |
| **NTAG213** | 144 bytes | ~0.15 € | Suffisant pour URI courte uniquement |

## URI encodée sur chaque tag

```
https://frekcore.com/card/{frek_id}
```

Au tap sur smartphone (Android Chrome ou iOS Safari iOS 14+) :
- iOS : ouvre directement la FREK Card virtuelle
- Android : notification puis ouverture
- Aucune app a installer

## Workflow batch terrain

### 1. Generer la liste des FREK-IDs a graver

CSV minimal `badges.csv` :

```csv
frek_id
72396222-4acd-41c3-b6f3-a5f14f38c0ef
994a2c47-a66d-4f84-a535-b9f21d9d5b9c
...
```

Astuce : exporter depuis l'API badges :

```bash
curl -s -H "Authorization: Bearer $STAFF_TOKEN" \
  "https://frekcore.com/api/badges/?event=CC2026&size=1000" \
  | jq -r '.badges[] | .frek_id' \
  | (echo "frek_id"; cat) > badges.csv
```

### 2. Dry-run pour verifier le contenu NDEF

```bash
python scripts/nfc_encode.py --batch badges.csv --dry-run
```

Sortie :
- URI cible pour chaque ID
- NDEF hex que le lecteur va ecrire
- Aucune ecriture reelle

### 3. Gravure reelle

```bash
python scripts/nfc_encode.py --batch badges.csv
```

Le script :
- Demande un tag avant chaque ecriture
- Attend appui Entree entre chaque tag
- Affiche le hex de chaque NDEF

### 4. Test apres gravure

Tapper le tag sur un telephone — la FREK Card doit s'ouvrir au bon FREK-ID.

## Lock du tag (optionnel, recommande pour le terrain)

Apres gravure reussie, lock le tag en lecture seule pour eviter
toute modification ulterieure :

```python
# Via nfcpy
tag.ndef.is_writeable = False  # equivaut au lock NTAG
```

⚠️ Le lock est **irreversible**. A faire seulement quand la gravure est validee.

## Aucune dependance backend

Ce processus est 100% offline. Il ne fait :
- aucun appel reseau
- aucune ecriture en base de donnees
- aucune modification de FrekCore

Le seul lien avec FrekCore est l'URI gravee qui pointe vers `/card/{frek_id}`.
