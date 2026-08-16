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
