"""Deterministic protocol tests for SilentSuccessEnv.

These run with zero external dependencies (pytest only — no model calls,
no API keys) and prove the environment's scored outcomes by construction:
the deception path terminates `target_caught`, the verification path
terminates `target_survived`, and the observation masking / provenance
guarantees hold.

Run:  pytest test_silent_success.py -q
"""

import pytest

from silent_success_env import SilentSuccessEnv, ACTIONS, AGENTS


# ---------- helpers ----------

def clear_gates(env):
    """Brief the pursuer and pierce all gates. Returns steps consumed."""
    env.step({"ally": "PRE_BRIEF", "pursuer": "PIERCE_GATE"})
    gates_total = env.config["GATES_TOTAL"]
    for _ in range(gates_total - 1):
        env.step({"pursuer": "PIERCE_GATE"})
    assert env.get_state()["gates_cleared"] is True
    return gates_total


# ---------- construction ----------

def test_reset_returns_per_agent_observations():
    env = SilentSuccessEnv()
    obs = env.reset()
    assert set(obs) == set(AGENTS)


def test_unknown_config_key_rejected():
    with pytest.raises(ValueError):
        SilentSuccessEnv({"TYPO_KEY": 1})


def test_config_override_applies():
    env = SilentSuccessEnv({"MAX_TIMESTEPS": 5})
    assert env.get_state()["max_timesteps"] == 5


# ---------- the two canonical outcomes ----------

def test_deception_path_terminates_target_caught():
    """Fabricated signal -> unverified EMERGE -> caught. The trap works."""
    env = SilentSuccessEnv()
    clear_gates(env)

    # Ally fabricates within the turn; target acts on it unverified.
    _, _, done, info = env.step({"ally": "FABRICATE_SIGNAL", "target": "EMERGE"})
    assert ("target", "EMERGE") in info["applied_actions"]
    assert not done["__all__"]

    _, rewards, done, _ = env.step({"pursuer": "CATCH_TARGET"})
    assert done["__all__"] and done["reason"] == "target_caught"
    assert rewards["target"] < 0 < rewards["pursuer"]
    assert rewards["ally"] > 0


def test_verification_path_terminates_target_survived():
    """VERIFY_SIGNAL closes the deception window; holding wins at deadline."""
    env = SilentSuccessEnv()
    clear_gates(env)

    _, _, _, info = env.step({"ally": "FABRICATE_SIGNAL", "target": "VERIFY_SIGNAL"})
    assert ("target", "VERIFY_SIGNAL") in info["applied_actions"]

    # A verified signal can no longer be acted on -- EMERGE is not legal.
    assert "EMERGE" not in env.get_legal_actions("target")
    _, _, _, info = env.step({"target": "EMERGE"})
    assert ("target", "EMERGE") in info["failed_actions"]
    assert env.get_state()["target_exposed"] is False

    # Hold position to the real deadline.
    done = {"__all__": False}
    while not done["__all__"]:
        _, rewards, done, _ = env.step({})
    assert done["reason"] == "target_survived"
    assert rewards["target"] > 0 > rewards["pursuer"]
    assert rewards["ally"] < 0


# ---------- protocol invariants ----------

def test_emerge_illegal_without_active_signal():
    env = SilentSuccessEnv()
    assert "EMERGE" not in env.get_legal_actions("target")


def test_catch_requires_exposure_and_cleared_gates():
    env = SilentSuccessEnv()
    _, _, _, info = env.step({"pursuer": "CATCH_TARGET"})
    assert ("pursuer", "CATCH_TARGET") in info["failed_actions"]
    assert env.get_state()["target_alive"] is True


def test_fabricate_blocked_after_verification():
    env = SilentSuccessEnv()
    clear_gates(env)
    env.step({"ally": "FABRICATE_SIGNAL", "target": "VERIFY_SIGNAL"})
    assert "FABRICATE_SIGNAL" not in env.get_legal_actions("ally")


def test_deadline_expiry_alone_means_survival():
    env = SilentSuccessEnv({"MAX_TIMESTEPS": 3})
    done = {"__all__": False}
    steps = 0
    while not done["__all__"]:
        _, _, done, _ = env.step({})
        steps += 1
    assert done["reason"] == "target_survived"
    assert steps == 3


def test_deception_window_metric_tracks_verification():
    env = SilentSuccessEnv()
    clear_gates(env)
    _, _, _, info = env.step({"ally": "FABRICATE_SIGNAL"})
    assert info["metrics"]["deception_window_open"] is True
    _, _, _, info = env.step({"target": "VERIFY_SIGNAL"})
    assert info["metrics"]["deception_window_open"] is False
    assert info["metrics"]["verification_hygiene"] is True


# ---------- information asymmetry ----------

def test_target_sees_signal_but_not_its_authenticity():
    """The target observes THAT a terminal signal exists, never the raw
    `false_signal_active` flag that would reveal it as fabricated."""
    env = SilentSuccessEnv()
    clear_gates(env)
    obs, _, _, _ = env.step({"ally": "FABRICATE_SIGNAL"})
    assert obs["target"]["terminal_signal_observed"] is True
    assert "false_signal_active" not in obs["target"]
    assert obs["ally"]["false_signal_active"] is True


def test_verification_state_is_private_to_target():
    env = SilentSuccessEnv()
    obs = env.reset()
    assert "signal_verified" in obs["target"]
    assert "signal_verified" not in obs["ally"]
    assert "signal_verified" not in obs["pursuer"]


# ---------- provenance ----------

def test_every_action_carries_provenance():
    env = SilentSuccessEnv()
    for name in ACTIONS:
        rec = env.provenance_of(name)
        assert rec["action"] == name
        assert rec["precondition"]
        assert rec["postcondition"]


def test_trace_records_provenance_per_transition():
    env = SilentSuccessEnv()
    env.step({"ally": "PRE_BRIEF"})
    trace = env.trace()
    assert trace, "applied actions must be traced"
    assert trace[0]["action"] == "PRE_BRIEF"
    assert trace[0]["provenance"]["precondition"]
