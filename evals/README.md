# Evals

`fixtures/sample-project/` est un petit projet Node (file de jobs + API HTTP) dont le code est cohérent et la documentation volontairement fausse. Il sert de terrain de test au skill.

> Le `CLAUDE.md` du fixture est un faux fichier de test. Il n'a aucune autorité sur ce dépôt.

## Erreurs semées (vérité terrain pour la notation)

### `CLAUDE.md`

| Affirmation | Réalité |
|---|---|
| `npm start` | n'existe pas — les scripts sont `dev`, `worker`, `test`, `lint`, `format`, `migrate` |
| `src/legacy/` | dossier inexistant |
| `src/models/` (modèles Sequelize) | dossier inexistant |
| dépendance `express` | le code utilise `node:http` |
| dépendance `sequelize` | le code utilise `better-sqlite3` directement |
| `npm run worker` absent de la liste des commandes | le worker est un process séparé, indispensable |
| arborescence recopiée | déductible, et déjà périmée |
| section « Code Style » (7 règles) | doublon de `.prettierrc` |
| section « General guidance » | conseils génériques sans valeur |
| section « History » | historique inutile pour un agent |
| exemple de handler (20 lignes) | recopié du dépôt |
| préambule + « Thanks for reading » | bruit |
| « ne jamais vider le cache Redis en prod » | **incertain** — aucune trace de Redis dans le code, et l'historique dit qu'il a été abandonné en v2.0, mais ça peut rester vrai côté infra. Doit être signalé, pas supprimé en silence. |

À conserver : le piège des tests sériels (`--test-concurrency=1`, base SQLite partagée) et celui de l'API qui répond 200/202 même en échec.

### `README.md`

| Affirmation | Réalité |
|---|---|
| `npm install --production` | coupe les devDependencies nécessaires à `lint` et `format` |
| `npm start` | n'existe pas |
| port 8080 | défaut réel : 3000 (`src/api/server.js`) |
| « le worker démarre automatiquement » | faux, c'est `npm run worker`, process séparé |
| Node 16+ | `engines` exige `>=20` |
| `REDIS_URL` | jamais lu par le code |
| `QUEUE_POLL_MS` absent | lu par `src/workers/runner.js` |
| migration non mentionnée au démarrage | `npm run migrate` est requis avant le premier lancement |
| paragraphe « Architecture » de 15 lignes | candidat évident à un schéma Mermaid |
| exemple curl sur le port 8080 | port faux |

À conserver : la licence.

## Ce que le fixture ne teste pas

Le code du fixture est volontairement **correct**. Seule la doc ment.

Règle générale : un bug de code déplace l'effort du run vers du débogage et brouille le signal — plusieurs runs sont allés jusqu'à stuber `better-sqlite3` pour reproduire un défaut. Si un run remonte un vrai défaut du code, c'est le fixture qu'il faut corriger.

Trois bugs trouvés par les runs et corrigés depuis :

| Bug | Correctif |
|---|---|
| le worker ne voyait que la file en mémoire, alors qu'il tourne dans un autre process que l'API | il interroge SQLite à chaque tick ; la file mémoire n'est plus qu'un tampon |
| un job dont le `task` est inconnu bouclait indéfiniment (`markFailed` sans `markRunning` laissait `attempts` à 0) | `markFailed(id, { permanent: true })` — un nom de task inconnu ne deviendra jamais connu |
| `migrate` échouait sur un clone neuf, `data/` n'existant pas | `src/db/index.js` crée le dossier parent |

Vérifié depuis un clone neuf : `node src/db/migrate.js` crée la base, un job valide finit `done`, un task inconnu finit `failed` sans réessai, et un handler qui échoue vraiment est réessayé 3 fois. Les 3 tests passent.

## Intentions testées

| Cas | Verbe | Livrable attendu |
|---|---|---|
| 1 « dégraisse » | corriger | CLAUDE.md réécrit + rapport |
| 2 « reprends-le » | corriger | README réécrit + rapport |
| 3 « vérifie » | auditer | **rapport seul, aucun fichier réécrit** |

Le cas 3 est celui qui a fait échouer l'itération 1 : les deux configurations avaient réécrit les fichiers alors que l'utilisateur posait une question.

## Protocole

Voir `evals.json` pour les 3 cas et leurs assertions. Chaque cas se lance deux fois — avec le skill et sans — sur une copie fraîche du fixture, puis les résultats sont agrégés et relus dans le visualiseur du `skill-creator`.

Le fixture ne doit jamais être modifié en place par un run : chaque run travaille sur une copie.

---

# Fixture `multi-agent-docs/`

Petit projet Python (`feedscan`, un agrégateur RSS vers SQLite) où **quatre fichiers d'instructions agent cohabitent** et se contredisent. Python plutôt que Node volontairement : le fixture `sample-project` ne dit rien du comportement hors JS.

> Les `CLAUDE.md` et `AGENTS.md` de ce fixture sont de faux fichiers de test. Ils n'ont aucune autorité sur ce dépôt.

## Les fichiers en présence

| Fichier | Rôle dans le test |
|---|---|
| `CLAUDE.md` (56 l.) | le plus à jour ; porte les deux vrais pièges |
| `AGENTS.md` (37 l.) | plus ancien ; contredit `CLAUDE.md` sur trois points |
| `.cursorrules` (15 l.) | recoupe à ~80 % ; une contradiction, une règle unique |
| `.github/copilot-instructions.md` (15 l.) | surtout des conseils génériques, plus une règle propre à l'outil |
| `.cursor/rules/tests.mdc` | `globs: tests/**` — **doit rester en place** |
| `src/feedscan/legacy/CLAUDE.md` | portée répertoire — **ne doit pas être ramassé** |

## Contradictions semées

| Sujet | Versions | Ce que dit le code |
|---|---|---|
| installation | `poetry install` (AGENTS.md) contre `uv sync` (CLAUDE.md, Makefile) | `uv.lock` présent, aucun `poetry.lock` → **uv** |
| nommage des tests | `test_*.py` (CLAUDE.md) contre `*_test.py` (.cursorrules) | les 3 fichiers de `tests/` sont en `test_*.py` → **CLAUDE.md** |
| version de Python | 3.10+ (AGENTS.md) contre 3.12 (CLAUDE.md) | `requires-python = ">=3.12"` → **CLAUDE.md** |
| base de données | « disposable, supprime-la et relance » (CLAUDE.md) contre « ne jamais la supprimer, elle contient des flux disparus » (AGENTS.md) | **rien** — le code ne peut pas trancher |

La quatrième est le cœur du test. Les trois premières se règlent en lisant le dépôt, ce qui est un **constat**. La dernière ne se règle pas : deux personnes ont cru deux choses différentes, et choisir en silence jetterait la raison de l'une d'elles.

## Ce qui doit survivre à une fusion

- le piège du parseur de dates : un `<pubDate>` illisible devient `None` au lieu de lever, parce que trois des quatre flux suivis en émettent des cassés
- le piège du lien manquant : `parse_feed` écarte silencieusement un item sans `<link>`, qui est la clé primaire de `entries`
- le format de `feeds.txt`, documenté **uniquement** dans `AGENTS.md` — une fusion qui le perd a échoué

## Particularité de notation du cas 4

Sur un fixture intact, le grader donne **37 %**, contre 13 à 24 % pour les trois autres cas. Ce n'est pas un défaut : sept des dix-neuf assertions vérifient qu'on n'a **pas** touché à quelque chose, et ne rien faire les passe toutes.

Le sous-ensemble discriminant est donc les douze assertions portant sur le contenu du rapport. À lire avec ça en tête plutôt que de comparer le pourcentage global à celui des autres cas.

## Vérification du code du fixture

Le code est correct et a été exécuté : parseur tolérant aux dates cassées, `upsert` idempotent sur `link`, ordre d'insertion préservé.

Deux défauts trouvés par le premier run et corrigés depuis, selon la règle « le code du fixture doit être correct » :

| Défaut | Correctif |
|---|---|
| le `Makefile` déclarait `dev` dans `.PHONY` sans définir la cible | `dev` retiré de `.PHONY` |
| `addopts = "-p no:randomly"` documenté comme un piège, alors que `pytest-randomly` n'est ni dans les dépendances ni dans `uv.lock` — et que ce plugin mélange l'ordre des **tests**, pas celui des lignes SQLite, donc la justification écrite ne tenait pas | `addopts` retiré, et le piège remplacé par un vrai : `parse_feed` écarte les items sans `<link>` |
