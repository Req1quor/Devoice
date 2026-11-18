# Changelog

Tous les changements notables de ce projet seront documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.0.0] - 2026-XX-XX

### Ajouté

- Séparation vocale haute qualité propulsée par Demucs (htdemucs et htdemucs_ft)
- Interface graphique moderne avec thème sombre et glisser-déposer
- Détection automatique GPU (CUDA) pour l'accélération matérielle
- Traitement par lot de plusieurs fichiers audio
- Prévisualisation intégrée des pistes vocales et instrumentales
- Export en WAV (16-bit, 24-bit), MP3 (320 kbps) et FLAC
- Sélection du dossier de sortie personnalisé
- Barre de progression en temps réel
- Support des formats d'entrée : MP3, WAV, FLAC, OGG, M4A, AAC, WMA, OPUS
- Build automatisé avec PyInstaller pour Windows
- CI/CD avec GitHub Actions (tests, linting, releases)
