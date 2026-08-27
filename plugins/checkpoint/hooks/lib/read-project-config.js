// Shared project-config reader for checkpoint hooks.
//
// Reads the optional `hooks_enabled` / `stop_cooldown_minutes` fields from
// `.checkpoint/config.md`'s frontmatter (written by the `save` skill's
// scope resolution — see `references/scope-and-role.md`). Fails toward the
// pre-existing defaults (hooks enabled, 20-minute cooldown) on any missing
// file, read error, or malformed value — a config problem must never make
// a hook behave worse than it did before this file existed.

const fs = require('fs');
const path = require('path');

const DEFAULT_HOOKS_ENABLED = true;
const DEFAULT_STOP_COOLDOWN_MINUTES = 20;

function resolveConfigPath(cwd) {
  return process.env.CHECKPOINT_CONFIG_FILE || path.join(cwd || process.cwd(), '.checkpoint', 'config.md');
}

function readProjectConfig(cwd) {
  const result = {
    hooksEnabled: DEFAULT_HOOKS_ENABLED,
    stopCooldownMinutes: DEFAULT_STOP_COOLDOWN_MINUTES,
  };

  let raw;
  try {
    raw = fs.readFileSync(resolveConfigPath(cwd), 'utf8');
  } catch {
    return result;
  }

  const frontmatterMatch = raw.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!frontmatterMatch) return result;
  const frontmatter = frontmatterMatch[1];

  const enabledMatch = frontmatter.match(/^hooks_enabled:\s*(true|false)\s*$/m);
  if (enabledMatch) {
    result.hooksEnabled = enabledMatch[1] === 'true';
  }

  const cooldownMatch = frontmatter.match(/^stop_cooldown_minutes:\s*(-?\d+(?:\.\d+)?)\s*$/m);
  if (cooldownMatch) {
    const value = Number(cooldownMatch[1]);
    if (Number.isFinite(value) && value >= 0) {
      result.stopCooldownMinutes = value;
    }
  }

  return result;
}

module.exports = { readProjectConfig, DEFAULT_HOOKS_ENABLED, DEFAULT_STOP_COOLDOWN_MINUTES };
