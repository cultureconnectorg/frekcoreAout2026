# FREK — Guide de Publication sur les Stores

## Configuration Capacitor ✅

L'application FREK a été configurée avec Capacitor pour être publiée sur iOS et Android.

### Structure créée
```
/app/frontend/
├── android/          # Projet Android Studio
├── ios/              # Projet Xcode
├── capacitor.config.json
└── dist/             # Build web
```

---

## 📱 Publication Google Play (Android)

### Prérequis
- Compte Google Play Developer (25€ une fois) : https://play.google.com/console
- Android Studio installé sur votre machine

### Étapes

#### 1. Télécharger le projet Android
```bash
# Depuis ce pod, compresser le dossier android
cd /app/frontend
zip -r frek-android.zip android/
```
Téléchargez `frek-android.zip` et extrayez-le sur votre machine.

#### 2. Ouvrir dans Android Studio
- Ouvrez Android Studio
- File → Open → Sélectionnez le dossier `android`

#### 3. Créer les icônes (dans Android Studio)
- Clic droit sur `res` → New → Image Asset
- Importez votre logo FREK (1024x1024 PNG recommandé)
- Générez les icônes pour toutes les densités

#### 4. Générer le fichier signé (AAB)
- Build → Generate Signed Bundle / APK
- Créez une nouvelle keystore (gardez-la précieusement !)
- Choisissez "Android App Bundle"
- Build type: release

#### 5. Publier sur Google Play
- Connectez-vous à Google Play Console
- Créez une nouvelle application
- Uploadez le fichier `.aab`
- Remplissez les informations (description, screenshots, etc.)
- Soumettez pour révision

---

## 🍎 Publication App Store (iOS)

### Prérequis
- Mac avec Xcode installé
- Compte Apple Developer (99€/an) : https://developer.apple.com
- Certificat de distribution iOS

### Étapes

#### 1. Télécharger le projet iOS
```bash
cd /app/frontend
zip -r frek-ios.zip ios/
```
Téléchargez et extrayez sur votre Mac.

#### 2. Ouvrir dans Xcode
- Ouvrez `ios/App/App.xcworkspace`
- Sélectionnez votre Team dans Signing & Capabilities
- Configurez le Bundle Identifier: `com.frekcore.app`

#### 3. Installer les dépendances CocoaPods
```bash
cd ios/App
pod install
```

#### 4. Créer les icônes
- Assets.xcassets → AppIcon
- Importez votre icône 1024x1024

#### 5. Archiver et publier
- Product → Archive
- Distribute App → App Store Connect
- Upload

#### 6. App Store Connect
- Connectez-vous à App Store Connect
- Configurez les métadonnées
- Soumettez pour révision

---

## 🖼️ Assets requis pour les stores

### Google Play
- Icône: 512x512 PNG
- Feature Graphic: 1024x500 PNG
- Screenshots: min 2 (téléphone), recommandé tablette aussi
- Description courte: 80 caractères max
- Description complète: 4000 caractères max

### App Store
- Icône: 1024x1024 PNG (sans transparence, sans coins arrondis)
- Screenshots iPhone 6.5" (1284x2778) - min 2
- Screenshots iPhone 5.5" (1242x2208) - min 2
- Screenshots iPad 12.9" (2048x2732) - optionnel
- Description: 4000 caractères max
- Mots-clés: 100 caractères max

---

## 📝 Texte suggéré pour les stores

### Titre
FREK — Certification Audio

### Description courte
Certifiez vos créations audio avec une preuve fréquentielle unique.

### Description complète
FREK est un système de certification fréquentielle pour les créateurs audio.

**Comment ça marche:**
• Sélectionnez votre fichier audio
• FREK génère une empreinte fréquentielle unique
• Recevez un FREK-ID vérifiable

**Caractéristiques:**
• Certification instantanée
• Aucun fichier audio stocké
• QR Code de vérification
• Standard ouvert CC BY 4.0

**Confidentialité:**
• Pas de cookies
• Pas de tracking
• Identifiants anonymes

Développé par CVLN Group.

---

## 🔄 Mise à jour de l'application

Pour chaque nouvelle version :

```bash
cd /app/frontend

# 1. Build le web
yarn build

# 2. Synchroniser avec les projets natifs
npx cap sync

# 3. Télécharger et rebuild dans Android Studio / Xcode
```

---

## ⚠️ Notes importantes

1. **Keystore Android** : Ne perdez JAMAIS votre keystore. Sans elle, vous ne pourrez plus mettre à jour l'app.

2. **Certificats iOS** : Renouvelez vos certificats avant expiration.

3. **Versions** : Incrémentez `versionCode` (Android) et `CFBundleVersion` (iOS) à chaque mise à jour.

4. **Politique de confidentialité** : Les stores exigent une URL de politique de confidentialité → Utilisez `/privacy`

---

© 2026 CVLN Group — frekcore.com
