"""ProtocolEngine — a small, reusable, turn-scheduled multi-agent
environment engine.

A subclass supplies ONLY data:
    agents, turn_order        (list[str])
    actions                   (dict[str, ActionSpec]-like registry)
    obs_source, obs_mask      (observation field wiring + per-agent visibility)
    default_config            (config defaults)
and implements three small hooks:
    make_default_state(), compute_rewards(state, config), check_termination(state)

The engine itself carries no episode-specific logic, and every applied
transition is recorded with a provenance record — so any trajectory can
answer "why does this transition exist" by construction, not by inspection.
"""


class ProtocolEnv:
    """Generic, deterministic, turn-scheduled multi-agent protocol environment."""

    agents: list
    turn_order: list
    actions: dict
    obs_source: dict
    obs_mask: dict
    default_config: dict

    def __init__(self, config: dict = None):
        self.config = dict(self.default_config)
        if config:
            unknown = set(config) - set(self.default_config)
            if unknown:
                # Fail fast: silently accepting unknown keys would hide typos.
                raise ValueError(f"Unknown config keys: {sorted(unknown)}")
            self.config.update(config)
        self.state = None
        self._trace = []
        self.reset()

    # ---- subclass hooks ----

    def make_default_state(self) -> dict:
        raise NotImplementedError

    def compute_rewards(self, state: dict, config: dict) -> dict:
        raise NotImplementedError

    def check_termination(self, state: dict) -> dict:
        raise NotImplementedError

    def action_provenance(self, action_name: str) -> dict:
        return self.provenance.get(action_name, {})

    # ---- API ----

    def reset(self) -> dict:
        self.state = self.make_default_state()
        self._trace = []
        return self._get_observations()

    def step(self, actions: dict) -> tuple:
        """Sequential turn resolution; missing agents default to WAIT; failed
        preconditions are silent no-ops."""
        applied, failed = [], []
        for agent_id in self.turn_order:
            action = actions.get(agent_id, "WAIT")
            spec = self.actions.get(action)
            if spec is None or (spec.agent != "*" and spec.agent != agent_id):
                failed.append((agent_id, action))
                continue
            if spec.precondition(self.state):
                if spec.effect is not None:
                    spec.effect(self.state, self.config)
                applied.append((agent_id, action))
                self._trace.append({
                    "timestep": self.state["timestep"],
                    "agent": agent_id,
                    "action": action,
                    "provenance": self.action_provenance(action),
                })
            else:
                failed.append((agent_id, action))

        self.state["timestep"] += 1
        obs = self._get_observations()
        rewards = self.compute_rewards(self.state, self.config)
        term = self.check_termination(self.state)
        done = {"__all__": term["done"], "reason": term["reason"]}
        info = {
            "timestep": self.state["timestep"],
            "applied_actions": applied,
            "failed_actions": failed,
        }
        return obs, rewards, done, info

    def get_legal_actions(self, agent_id: str) -> list:
        if agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        return [
            n for n, a in self.actions.items()
            if (a.agent == agent_id or a.agent == "*") and a.precondition(self.state)
        ]

    def get_state(self) -> dict:
        """Full state copy — logging/verification only, never for agent policies."""
        return dict(self.state)

    def provenance_of(self, action_name: str) -> dict:
        if action_name not in self.actions:
            raise ValueError(f"Unknown action: {action_name}")
        return self.action_provenance(action_name)

    def trace(self) -> list:
        return list(self._trace)

    def _get_observations(self) -> dict:
        """Masked fields are ABSENT from an agent's dict, not zeroed."""
        obs = {agent: {} for agent in self.agents}
        for fieldname, observers in self.obs_mask.items():
            value = self.state[self.obs_source[fieldname]]
            for agent in observers:
                obs[agent][fieldname] = value
        return obs
