# simplify-documentation

Un skill Claude Code qui reprend la documentation existante d'un projet et la confronte au code.

Deux traitements, selon le destinataire du fichier :

- **fichiers agent** (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`) — réduits au strict nécessaire. Tout ce que l'agent peut déduire en lisant le code disparaît ; ne restent que les conventions, les pièges et les interdits avec leur raison.
- **fichiers humains** (`README.md`, `docs/**`) — reformulés plus simplement, condensés, illustrés d'un schéma Mermaid quand ça clarifie, et vérifiés commande par commande.

Dans les deux cas, le code fait foi : le skill lit le code avant de juger la doc, présente un rapport des corrections, et n'écrit qu'après ton accord.

## Utilisation

```bash
/simplify-documentation
```

Le skill liste les fichiers de doc du dépôt courant et demande lesquels traiter. Tu peux aussi le viser directement : « simplifie le CLAUDE.md », « le README est obsolète depuis le refacto ».

## Installation

```bash
ln -s "$PWD" ~/.claude/skills/simplify-documentation
```

## Contenu

| Fichier | Rôle |
|---|---|
| [SKILL.md](SKILL.md) | le workflow en 5 phases et les garde-fous |
| [references/agent-docs.md](references/agent-docs.md) | quoi couper, quoi garder dans un fichier agent |
| [references/human-docs.md](references/human-docs.md) | réécriture, structure, et patrons Mermaid |
| [references/verification.md](references/verification.md) | où vérifier chaque type d'affirmation dans le code |
| [evals/](evals/) | cas de test et projet d'exemple à doc volontairement périmée |
