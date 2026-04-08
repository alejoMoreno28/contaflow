---
name: automatic-skill-fetcher
description: "Automatically analyzes a new project's stack and injects the best matching skills from the global vault."
---

# Automatic Skill Fetcher

## When to use this skill
- ANY TIME you are setting up a new project or analyzing an existing codebase for the first time.
- When the human partner asks to "initialize the skills" or gives you the context of a new application.

## How to execute it

1. Determine the core technologies of the human partner's project (e.g., react, python, fastapi, docker, typescript, clerk, next).
2. Run the provided JavaScript installer using the `run_command` tool.
   Command format: `node .agents/skills/automatic-skill-fetcher/scripts/skill-selector.js [tech1] [tech2] [tech3]`
   Example: `node .agents/skills/automatic-skill-fetcher/scripts/skill-selector.js react typescript fastapi`
3. The script will automatically scan the global Master Vault (`skills_abril`) and copy the Top 10 most relevant `.agents/skills` to the current project's workspace.
4. Once the script finishes printing `✅ Instalada`, read the newly fetched skills and use them as your foundation for the next steps!
