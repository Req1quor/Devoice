<div align="center">

# 🎙️ Devoice

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/v/release/USERNAME/devoice)](https://github.com/USERNAME/devoice/releases)
[![GitHub stars](https://img.shields.io/github/stars/USERNAME/devoice)](https://github.com/USERNAME/devoice/stargazers)

**Sépare les voix de la musique en un clic grâce à l'IA.**

Application de bureau pour extraire les pistes vocales et instrumentales de n'importe quel fichier audio, propulsée par [Demucs](https://github.com/facebookresearch/demucs) de Meta.

[📥 Télécharger](https://github.com/USERNAME/devoice/releases) · [🐛 Signaler un bug](https://github.com/USERNAME/devoice/issues) · [💡 Proposer une fonctionnalité](https://github.com/USERNAME/devoice/issues)

</div>

---

## ✨ Fonctionnalités

- 🎵 **Séparation vocale de haute qualité** — Propulsé par Demucs (Meta AI), le modèle le plus avancé du marché
- ⚡ **Accélération GPU** — Détection automatique CUDA pour un traitement jusqu'à 10x plus rapide
- 🎨 **Interface moderne et intuitive** — Thème sombre élégant avec glisser-déposer de fichiers
- 📦 **Traitement par lot** — Sépare plusieurs fichiers audio en une seule opération
- 🎧 **Prévisualisation intégrée** — Écoute instantanée des pistes vocales et instrumentales extraites
- 💾 **Formats multiples** — Exporte en WAV (16/24-bit), MP3 (320 kbps) ou FLAC

## 🎯 Comparaison

| Fonctionnalité | Sites web | FL Studio | **Devoice** |
|---|---|---|---|
| Qualité de séparation | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Hors-ligne | ❌ | ✅ | ✅ |
| Gratuit | ⚠️ Limité | ❌ | ✅ |
| Traitement par lot | ❌ | ❌ | ✅ |
| Accélération GPU | ❌ | ❌ | ✅ |
| Open source | ❌ | ❌ | ✅ |

## 📥 Installation

### Option 1 : Exécutable (recommandé)

1. Rendez-vous sur la page [Releases](https://github.com/USERNAME/devoice/releases)
2. Téléchargez `Devoice-windows.zip`
3. Décompressez l'archive
4. Lancez `Devoice.exe`

### Option 2 : Depuis les sources

```bash
# Cloner le dépôt
git clone https://github.com/USERNAME/devoice.git
cd devoice

# Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux / macOS

# Installer les dépendances
pip install -r requirements.txt
```

> [!NOTE]
> Pour bénéficier de l'accélération GPU, installez la version CUDA de PyTorch :
> ```bash
> pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
> ```

## 🚀 Utilisation

1. **Lancez l'application** — Exécutez `python main.py` ou double-cliquez sur `Devoice.exe`
2. **Ajoutez vos fichiers** — Glissez-déposez vos fichiers audio dans la zone de dépôt ou cliquez pour parcourir
3. **Configurez** — Choisissez le modèle (Rapide ou Qualité Max) et le format de sortie
4. **Séparez** — Cliquez sur « 🎤 Séparer » et attendez la fin du traitement

## 🤝 Contribuer

Les contributions sont les bienvenues ! Consultez le guide de contribution [CONTRIBUTING.md](CONTRIBUTING.md) pour commencer.

## 📄 Licence

Ce projet est distribué sous la licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Crédits

- [Demucs](https://github.com/facebookresearch/demucs) — Moteur de séparation audio par Meta AI Research
- [PyTorch](https://pytorch.org/) — Framework d'apprentissage profond
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — Framework d'interface graphique
