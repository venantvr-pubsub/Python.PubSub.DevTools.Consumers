# Tests de Sequential Processing

Ce répertoire contient plusieurs types de tests pour vérifier le traitement séquentiel des événements.

## 📋 Fichiers de tests

### ✅ `test_queue_logic.py` - **RECOMMANDÉ**

Tests unitaires de la logique de queue **sans dépendances** (Flask/requests).

```bash
python3 -m pytest tests/test_queue_logic.py -v
```

**Avantages :**

- ✅ Pas de dépendances externes
- ✅ Rapide (1-2 secondes)
- ✅ Ne se bloque jamais
- ✅ Teste la logique pure de la queue

**Tests inclus :**

- Ordre de traitement préservé
- Gestion des exceptions dans le handler
- Handlers qui retournent False
- Taille de la queue qui change
- Preuve par le timing que c'est séquentiel

**Résultat : ✅ 5/5 tests passent**

---

### ⚠️ `test_sequential_processing.py` - Nécessite Flask

Tests d'intégration avec le `DevToolsPlayerProxy` complet.

```bash
# Nécessite Flask installé
pip install flask
PYTHONPATH=src python3 -m pytest tests/test_sequential_processing.py -v
```

**Comportement :**

- ✅ Si Flask n'est pas installé : **6 tests skippés** (pas d'erreur)
- ✅ Si Flask est installé : tests d'intégration complets
- ✅ Protection contre les blocages avec timeouts

---

### 🎯 `demo_race_conditions.py` - Démonstration race conditions

Démonstration interactive qui prouve l'efficacité du traitement séquentiel.

```bash
python3 tests/demo_race_conditions.py
```

**Affiche :**

- Comparaison mode parallèle vs séquentiel
- Résultats chiffrés (% de perte)
- Recommandations

**Exemple de sortie :**

```
Mode PARALLÈLE  : 7.2/50 événements traités (85.6% de perte!)
Mode SÉQUENTIEL : 50/50 événements traités (0% de perte)
```

---

### 🐛 `demo_task_done_bug.py` - Démonstration bug task_done()

Démonstration du bug critique où `task_done()` n'était pas appelé pour le signal d'arrêt.

```bash
python3 tests/demo_task_done_bug.py
```

**Montre :**

- Version buggée : Se bloque à `queue.join()` après 3 secondes
- Version corrigée : Succès immédiat
- Explication du bug

**Résultat :**

```
❌ Version BUGGÉE : Se bloque à queue.join()
✅ Version CORRIGÉE : Succès en 0.00s!

RÈGLE D'OR : task_done() doit être appelé pour CHAQUE get() réussi
```

---

### 📝 `test_imports.py` - Tests de base

Tests basiques d'importation et d'instantiation.

```bash
PYTHONPATH=src python3 -m pytest tests/test_imports.py -v
```

Nécessite Flask installé.

---

## 🚀 Quick Start

### Sans installer de dépendances

```bash
# Tests unitaires (recommandé)
python3 -m pytest tests/test_queue_logic.py -v

# Démonstration
python3 tests/demo_race_conditions.py
```

### Avec Flask installé

```bash
# Tous les tests
PYTHONPATH=src python3 -m pytest tests/ -v

# Tests spécifiques
PYTHONPATH=src python3 -m pytest tests/test_imports.py -v
PYTHONPATH=src python3 -m pytest tests/test_sequential_processing.py -v
```

---

## 🔍 Comparaison des tests

| Fichier                         | Dépendances | Durée | Blocage?        | Utilité                  |
|---------------------------------|-------------|-------|-----------------|--------------------------|
| `test_queue_logic.py`           | ✅ Aucune    | ~2s   | ❌ Non           | **Tests unitaires**      |
| `test_task_done_bug.py`         | ✅ Aucune    | ~0.3s | ❌ Non           | **Test bug task_done()** |
| `test_sequential_processing.py` | ⚠️ Flask    | ~0.3s | ❌ Non (skippés) | Tests d'intégration      |
| `demo_race_conditions.py`       | ✅ Aucune    | ~3s   | ❌ Non           | **Démo race conditions** |
| `demo_task_done_bug.py`         | ✅ Aucune    | ~3s   | ⚠️ 3s timeout   | **Démo bug task_done()** |
| `test_imports.py`               | ⚠️ Flask    | ~1s   | ❌ Non           | Tests basiques           |

---

## 💡 Recommandations

### Pour le développement quotidien

Utilisez **`test_queue_logic.py`** :

- Pas de dépendances
- Rapide et fiable
- Teste la logique essentielle

### Pour une démonstration

Utilisez **`demo_race_conditions.py`** :

- Montre visuellement le problème
- Résultats chiffrés
- Impactant pour convaincre

### Pour l'intégration complète

Utilisez **`test_sequential_processing.py`** (avec Flask installé) :

- Teste le player complet
- Vérifie l'intégration Flask
- Plus proche de la production

---

## ❓ FAQ

### Q: Les tests `test_sequential_processing.py` se bloquent ?

**R:** Non, ils sont maintenant protégés :

- Si Flask n'est pas installé → **skippés** automatiquement
- Timeouts ajoutés pour éviter les blocages
- Utilisez `test_queue_logic.py` comme alternative sans dépendances

### Q: Pourquoi deux fichiers de tests pour la même fonctionnalité ?

**R:** Séparation des concerns :

- `test_queue_logic.py` : **Logique pure** (queue + worker) sans dépendances
- `test_sequential_processing.py` : **Intégration** (Flask + queue + worker)

### Q: Dois-je installer Flask pour tester ?

**R:** Non ! `test_queue_logic.py` et `demo_race_conditions.py` fonctionnent **sans Flask**.

---

## 🐛 Dépannage

### Les tests se bloquent encore

```bash
# Tuer les processus bloqués
pkill -f pytest

# Utiliser seulement les tests sans dépendances
python3 -m pytest tests/test_queue_logic.py -v
```

### Flask non disponible

```bash
# Option 1 : Installer Flask
pip install flask

# Option 2 : Utiliser les tests sans dépendances
python3 -m pytest tests/test_queue_logic.py -v
python3 tests/demo_race_conditions.py
```

---

## 📚 Documentation complète

Voir `RACE_CONDITIONS.md` pour la documentation complète sur le traitement séquentiel.
