import json
from pathlib import Path


# Geschätzte Kosten in USD. Diese Werte können bei Bedarf angepasst werden.
GPT_COST_PER_REQUEST = 0.01
VOICE_COST_PER_1_000_CHARACTERS = 0.015
IMAGE_COST_PER_IMAGE = 0.04

_pending_gpt_cost = 0.0
_last_cost_file = None


def _get_cost_file(output_folder):
    return Path(output_folder) / "costs.json"


def _load_costs(cost_file):
    if not cost_file.exists():
        return {
            "gpt_cost": 0.0,
            "voice_cost": 0.0,
            "image_cost": 0.0,
            "total_cost": 0.0,
        }

    return json.loads(cost_file.read_text(encoding="utf-8"))


def _save_costs(cost_file, costs):
    costs["total_cost"] = round(
        costs["gpt_cost"] + costs["voice_cost"] + costs["image_cost"],
        4,
    )
    cost_file.write_text(
        json.dumps(costs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _add_cost(output_folder, cost_type, amount):
    global _last_cost_file

    cost_file = _get_cost_file(output_folder)
    costs = _load_costs(cost_file)
    costs[cost_type] = round(costs[cost_type] + amount, 4)
    _save_costs(cost_file, costs)
    _last_cost_file = cost_file


def record_gpt_cost(cost=GPT_COST_PER_REQUEST):
    global _pending_gpt_cost

    _pending_gpt_cost += cost


def _flush_gpt_cost(output_folder):
    global _pending_gpt_cost

    if _pending_gpt_cost:
        _add_cost(output_folder, "gpt_cost", _pending_gpt_cost)
        _pending_gpt_cost = 0.0


def record_voice_cost(output_folder, script):
    _flush_gpt_cost(output_folder)
    estimated_cost = len(script) / 1_000 * VOICE_COST_PER_1_000_CHARACTERS
    _add_cost(output_folder, "voice_cost", estimated_cost)


def record_image_cost(output_folder, image_count):
    _flush_gpt_cost(output_folder)
    _add_cost(output_folder, "image_cost", image_count * IMAGE_COST_PER_IMAGE)


def print_cost_summary():
    if _last_cost_file is None:
        costs = {
            "gpt_cost": 0.0,
            "voice_cost": 0.0,
            "image_cost": 0.0,
            "total_cost": 0.0,
        }
    else:
        costs = _load_costs(_last_cost_file)

    print("Kostenübersicht:")
    print(f"GPT: {costs['gpt_cost']:.4f}")
    print(f"Voice: {costs['voice_cost']:.4f}")
    print(f"Bilder: {costs['image_cost']:.4f}")
    print(f"Gesamt: {costs['total_cost']:.4f}")
