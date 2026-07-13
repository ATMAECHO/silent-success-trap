"""SilentSuccessEnv — a deadline-pursuit protocol with an adversarially
manipulable terminal signal.

Three agents: `ally`, `pursuer`, `target`. The pursuer must reach and act on
`target` before a real deadline expires, working through a sequence of
defensive gates. The `ally` may fabricate a false terminal signal (the
deadline appearing to have already passed) once the gates are cleared. The
`target` observes this signal and must decide whether to act on it or
verify it first through an independent check.

The core design point: the terminal signal is ALWAYS visible to the target
but its authenticity is not — `VERIFY_SIGNAL` resolves that ambiguity in one
deterministic step. Accepting the signal at face value and acting on it
(`EMERGE`) exposes the target inside the deception window.

Every transition carries a provenance record answering "why does this
transition exist" — pointing back to this module's action table, not
invented at runtime.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from protocol_engine import ProtocolEnv

AGENTS = ["ally", "pursuer", "target"]
TURN_ORDER = ["ally", "pursuer", "target"]


def default_state(max_timesteps: int = 12) -> dict:
    return {
        "gates_pierced": 0,
        "gates_cleared": False,
        "pursuer_briefed": False,
        "false_signal_active": False,
        "signal_verified": False,
        "target_exposed": False,
        "target_alive": True,
        "timestep": 0,
        "max_timesteps": max_timesteps,
    }


DEFAULT_CONFIG = {
    "MAX_TIMESTEPS": 12,
    "GATES_TOTAL": 6,
    "R_PURSUER_SUCCEEDS": 10.0,
    "R_ALLY_WIN": 5.0,
    "R_TARGET_CAUGHT": -10.0,
    "R_PURSUER_FAILS": -10.0,
    "R_TARGET_SURVIVES": 10.0,
    "R_ALLY_LOSS": -5.0,
}


@dataclass(frozen=True)
class ActionSpec:
    name: str
    agent: str
    category: str
    precondition: Callable[[dict], bool]
    precondition_src: str
    effect: Optional[Callable[[dict, dict], None]] = None
    effect_src: str = "No state mutation"


def _fx_pre_brief(s, c):
    s["pursuer_briefed"] = True


def _fx_fabricate_signal(s, c):
    s["false_signal_active"] = True


def _fx_withdraw_signal(s, c):
    s["false_signal_active"] = False


def _fx_pierce_gate(s, c):
    s["gates_pierced"] += 1
    if s["gates_pierced"] >= c["GATES_TOTAL"]:
        s["gates_cleared"] = True


def _fx_catch_target(s, c):
    s["target_alive"] = False


def _fx_emerge(s, c):
    s["target_exposed"] = True


def _fx_verify_signal(s, c):
    s["signal_verified"] = True


ACTIONS: dict[str, ActionSpec] = {a.name: a for a in [
    ActionSpec("PRE_BRIEF", "ally", "active",
               lambda s: not s["pursuer_briefed"], "not state['pursuer_briefed']",
               _fx_pre_brief, "state['pursuer_briefed'] = True"),
    ActionSpec("FABRICATE_SIGNAL", "ally", "active",
               lambda s: (s["pursuer_briefed"] and not s["false_signal_active"]
                          and not s["signal_verified"]),
               "state['pursuer_briefed'] and not state['false_signal_active'] "
               "and not state['signal_verified']",
               _fx_fabricate_signal, "state['false_signal_active'] = True"),
    ActionSpec("WITHDRAW_SIGNAL", "ally", "active",
               lambda s: s["false_signal_active"] and not s["target_alive"],
               "state['false_signal_active'] and not state['target_alive']",
               _fx_withdraw_signal, "state['false_signal_active'] = False"),
    ActionSpec("PIERCE_GATE", "pursuer", "active",
               lambda s: not s["gates_cleared"] and s["target_alive"],
               "not state['gates_cleared'] and state['target_alive']",
               _fx_pierce_gate,
               "state['gates_pierced'] += 1; state['gates_cleared'] = True "
               "if state['gates_pierced'] >= config['GATES_TOTAL']"),
    ActionSpec("CATCH_TARGET", "pursuer", "active",
               lambda s: (s["gates_cleared"] and s["target_exposed"]
                          and s["target_alive"] and s["pursuer_briefed"]),
               "state['gates_cleared'] and state['target_exposed'] "
               "and state['target_alive'] and state['pursuer_briefed']",
               _fx_catch_target, "state['target_alive'] = False"),
    ActionSpec("EMERGE", "target", "active",
               lambda s: (s["false_signal_active"] and not s["signal_verified"]
                          and s["target_alive"] and not s["target_exposed"]),
               "state['false_signal_active'] and not state['signal_verified'] "
               "and state['target_alive'] and not state['target_exposed']",
               _fx_emerge, "state['target_exposed'] = True"),
    ActionSpec("VERIFY_SIGNAL", "target", "active",
               lambda s: (s["false_signal_active"] and not s["signal_verified"]
                          and s["target_alive"]),
               "state['false_signal_active'] and not state['signal_verified'] "
               "and state['target_alive']",
               _fx_verify_signal, "state['signal_verified'] = True"),
    ActionSpec("WAIT", "*", "noop_a", lambda s: True, "True"),
]}

assert len(ACTIONS) == 8


def agent_actions(agent_id: str) -> list[str]:
    return [n for n, a in ACTIONS.items() if a.agent == agent_id or a.agent == "*"]


OBS_SOURCE = {
    "pursuer_briefed": "pursuer_briefed",
    "false_signal_active": "false_signal_active",
    "terminal_signal_observed": "false_signal_active",  # aliased for the target
    "gates_pierced": "gates_pierced",
    "gates_cleared": "gates_cleared",
    "signal_verified": "signal_verified",
    "target_exposed": "target_exposed",
    "target_alive": "target_alive",
}

OBS_MASK: dict[str, list[str]] = {
    "pursuer_briefed": ["ally", "pursuer"],
    "false_signal_active": ["ally", "pursuer"],
    "terminal_signal_observed": ["target"],
    "gates_pierced": ["ally", "pursuer", "target"],
    "gates_cleared": ["ally", "pursuer", "target"],
    "signal_verified": ["target"],
    "target_exposed": ["ally", "pursuer", "target"],
    "target_alive": ["ally", "pursuer", "target"],
}

ENV_PROVENANCE = {
    "protocol_family": "deadline-pursuit with an adversarially manipulable terminal signal",
    "design_note": "the target's winning move is verifying a signal that every "
                   "incentive says to accept at face value",
}


def action_provenance_record(name: str) -> dict:
    a = ACTIONS[name]
    return {
        "action": name,
        "precondition": a.precondition_src,
        "postcondition": a.effect_src,
        "category": a.category,
        "environment": ENV_PROVENANCE,
    }


PROVENANCE = {name: action_provenance_record(name) for name in ACTIONS}


def computed_metrics(state: dict) -> dict:
    return {
        "deadline_pressure": state["timestep"] / state["max_timesteps"],
        "deception_window_open": (state["false_signal_active"]
                                  and not state["signal_verified"]
                                  and state["target_alive"]),
        "verification_hygiene": state["signal_verified"],
    }


def compute_rewards(state: dict, config: dict) -> dict:
    rewards = {agent: 0.0 for agent in AGENTS}

    if not state["target_alive"]:
        rewards["pursuer"] += config["R_PURSUER_SUCCEEDS"]
        rewards["ally"] += config["R_ALLY_WIN"]
        rewards["target"] += config["R_TARGET_CAUGHT"]

    if state["timestep"] >= state["max_timesteps"] and state["target_alive"]:
        rewards["pursuer"] += config["R_PURSUER_FAILS"]
        rewards["target"] += config["R_TARGET_SURVIVES"]
        rewards["ally"] += config["R_ALLY_LOSS"]

    return rewards


def check_termination(state: dict) -> dict:
    done = False
    reason = None

    if not state["target_alive"]:
        done, reason = True, "target_caught"
    elif state["timestep"] >= state["max_timesteps"]:
        done, reason = True, "target_survived"

    return {"done": done, "reason": reason}


class SilentSuccessEnv(ProtocolEnv):
    """Three-agent deadline-pursuit protocol with a manipulable terminal signal."""

    agents = AGENTS
    turn_order = TURN_ORDER
    actions = ACTIONS
    obs_source = OBS_SOURCE
    obs_mask = OBS_MASK
    default_config = DEFAULT_CONFIG
    provenance = PROVENANCE

    def make_default_state(self) -> dict:
        return default_state(max_timesteps=self.config["MAX_TIMESTEPS"])

    def compute_rewards(self, state: dict, config: dict) -> dict:
        return compute_rewards(state, config)

    def check_termination(self, state: dict) -> dict:
        return check_termination(state)

    def step(self, actions: dict) -> tuple:
        obs, rewards, done, info = super().step(actions)
        info["metrics"] = computed_metrics(self.state)
        return obs, rewards, done, info
