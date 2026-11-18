# 🤝 Guide de contribution

Merci de votre intérêt pour contribuer à Devoice ! Ce guide vous aidera à démarrer.

## 🐛 Signaler un bug

1. Vérifiez que le bug n'a pas déjà été signalé dans les [Issues](https://github.com/USERNAME/devoice/issues)
2. Créez une nouvelle issue en utilisant le template **Bug Report**
3. Décrivez le problème avec le plus de détails possible :
   - Étapes pour reproduire le bug
   - Comportement attendu vs comportement observé
   - Captures d'écran ou logs si applicable
   - Votre environnement (OS, GPU, version de Devoice, version de Python)

## 💡 Proposer une fonctionnalité

1. Vérifiez que la fonctionnalité n'a pas déjà été proposée
2. Créez une nouvelle issue en utilisant le template **Feature Request**
3. Décrivez clairement :
   - La fonctionnalité souhaitée
   - Le cas d'utilisation
   - Les alternatives envisagées

## 🛠️ Environnement de développement

### Prérequis

- Python 3.10 ou supérieur
- Git

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/USERNAME/devoice.git
cd devoice

# Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux / macOS

# Installer en mode développement
pip install -e .
pip install -e ".[dev]"
```

## ✅ Tests

Lancez les tests avec pytest :

```bash
pytest
```

Pour exécuter les tests avec le rapport de couverture :

```bash
pytest --verbose
```

## 🧹 Linting

Le projet utilise [Ruff](https://github.com/astral-sh/ruff) pour le linting et le formatage :

```bash
# Vérifier le code
ruff check .

# Formater le code
ruff format .
```

## 📝 Workflow de Pull Request

1. **Forkez** le dépôt
2. **Créez une branche** pour votre fonctionnalité ou correction :
   ```bash
   git checkout -b feat/ma-fonctionnalite
   ```
3. **Faites vos modifications** en suivant les conventions du projet
4. **Testez** vos changements :
   ```bash
   pytest
   ruff check .
   ```
5. **Commitez** en suivant les [Conventional Commits](https://www.conventionalcommits.org/) :
   ```bash
   git commit -m "feat: ajouter le support du format AAC"
   git commit -m "fix: corriger le crash lors du drag-and-drop"
   git commit -m "docs: mettre à jour le README"
   ```
6. **Poussez** votre branche et créez une Pull Request

## 📏 Conventions de commits

Nous utilisons les [Conventional Commits](https://www.conventionalcommits.org/fr/) :

| Préfixe | Description |
|---|---|
| `feat:` | Nouvelle fonctionnalité |
| `fix:` | Correction de bug |
| `docs:` | Documentation uniquement |
| `style:` | Formatage, points-virgules manquants, etc. |
| `refactor:` | Refactorisation du code |
| `test:` | Ajout ou modification de tests |
| `chore:` | Maintenance, dépendances, CI |

## ❤️ Code de conduite

Soyez respectueux et bienveillant envers les autres contributeurs. Toute forme de harcèlement ou de comportement toxique ne sera pas tolérée.

---

Merci pour votre contribution ! 🎉
