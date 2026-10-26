"""Repository over ``storm-web/database.py`` (HANDOFF plan section P5.4).

``database.py`` is a **frozen** legacy module: its public functions are
the only sanctioned persistence API and MUST NOT be edited (HANDOFF
"DO NOT TOUCH").  ``Repository`` is a thin, explicit, 1:1 delegate:
every method forwards to the same-named function with identical
arguments and returns whatever the module returns.

Why a Repository at all:
- services (P4) get a single injectable seam instead of 21 scattered
  ``import database`` statements;
- tests can substitute a fake via ``Repository(db_module=fake)``;
- P6 job workers get a concurrency-safe entry point without touching
  the frozen module.

There is deliberately **no** SQL, caching, or transformation here --
zero behavior drift by construction.
"""
from __future__ import annotations

import sys as _sys
import threading
from pathlib import Path
from typing import Any, Optional

# Sibling import: ``database.py`` lives in storm-web/ (two levels up
# from app/core/db.py), exactly like app/state.py does it.
_HERE = Path(__file__).resolve().parent
_STORM_WEB = str(_HERE.parents[2])
if _STORM_WEB not in _sys.path:
    _sys.path.insert(0, _STORM_WEB)

import database as _database  # noqa: E402

DB_PATH = _database.DB_PATH


class Repository:
    """1:1 delegate over ``database.py`` (frozen module, P5.4)."""

    def __init__(self, db_module: Any = None) -> None:
        self._db = db_module if db_module is not None else _database

    # -- schema / maintenance -------------------------------------------------
    def init_database(self, *args: Any, **kwargs: Any):
        """Forward to ``database.init_database`` (idempotent DDL)."""
        return self._db.init_database(*args, **kwargs)

    def cleanup_old_data(self, *args: Any, **kwargs: Any):
        return self._db.cleanup_old_data(*args, **kwargs)

    # -- mobile sessions -------------------------------------------------------
    def save_mobile_session(self, *args, **kwargs):
        return self._db.save_mobile_session(*args, **kwargs)

    def get_mobile_session(self, *args, **kwargs):
        return self._db.get_mobile_session(*args, **kwargs)

    def get_all_mobile_sessions(self, *args, **kwargs):
        return self._db.get_all_mobile_sessions(*args, **kwargs)

    def update_mobile_last_seen(self, *args, **kwargs):
        return self._db.update_mobile_last_seen(*args, **kwargs)

    def delete_mobile_session(self, *args, **kwargs):
        return self._db.delete_mobile_session(*args, **kwargs)

    # -- c2 sessions ------------------------------------------------------------
    def save_c2_session(self, *args, **kwargs):
        return self._db.save_c2_session(*args, **kwargs)

    def update_c2_last_seen(self, *args, **kwargs):
        return self._db.update_c2_last_seen(*args, **kwargs)

    def get_all_c2_sessions(self, *args, **kwargs):
        return self._db.get_all_c2_sessions(*args, **kwargs)

    # -- mobile capture / command / response / tracking --------------------------
    def save_mobile_capture(self, *args, **kwargs):
        return self._db.save_mobile_capture(*args, **kwargs)

    def get_mobile_captures(self, *args, **kwargs):
        return self._db.get_mobile_captures(*args, **kwargs)

    def add_mobile_command(self, *args, **kwargs):
        return self._db.add_mobile_command(*args, **kwargs)

    def get_mobile_commands(self, *args, **kwargs):
        return self._db.get_mobile_commands(*args, **kwargs)

    def mark_command_executed(self, *args, **kwargs):
        return self._db.mark_command_executed(*args, **kwargs)

    def add_mobile_response(self, *args, **kwargs):
        return self._db.add_mobile_response(*args, **kwargs)

    def get_mobile_response(self, *args, **kwargs):
        return self._db.get_mobile_response(*args, **kwargs)

    def add_tracking_data(self, *args, **kwargs):
        return self._db.add_tracking_data(*args, **kwargs)

    def get_tracking_data(self, *args, **kwargs):
        return self._db.get_tracking_data(*args, **kwargs)

    # -- campaigns -----------------------------------------------------------------
    def create_campaign(self, *args, **kwargs):
        return self._db.create_campaign(*args, **kwargs)

    def get_campaigns(self, *args, **kwargs):
        return self._db.get_campaigns(*args, **kwargs)

    def get_campaign(self, *args, **kwargs):
        return self._db.get_campaign(*args, **kwargs)

    def update_campaign(self, *args, **kwargs):
        return self._db.update_campaign(*args, **kwargs)

    def delete_campaign(self, *args, **kwargs):
        return self._db.delete_campaign(*args, **kwargs)

    def add_campaign_link(self, *args, **kwargs):
        return self._db.add_campaign_link(*args, **kwargs)

    def get_campaign_links(self, *args, **kwargs):
        return self._db.get_campaign_links(*args, **kwargs)

    def increment_campaign_click(self, *args, **kwargs):
        return self._db.increment_campaign_click(*args, **kwargs)

    def increment_campaign_capture(self, *args, **kwargs):
        return self._db.increment_campaign_capture(*args, **kwargs)

    # -- credentials ------------------------------------------------------------------
    def save_credential(self, *args, **kwargs):
        return self._db.save_credential(*args, **kwargs)

    def get_credentials(self, *args, **kwargs):
        return self._db.get_credentials(*args, **kwargs)

    def get_credential_pairs(self, *args, **kwargs):
        return self._db.get_credential_pairs(*args, **kwargs)

    def delete_credential(self, *args, **kwargs):
        return self._db.delete_credential(*args, **kwargs)

    # -- victim profiles -----------------------------------------------------------
    def save_victim_profile(self, *args, **kwargs):
        return self._db.save_victim_profile(*args, **kwargs)

    def get_victim_profiles(self, *args, **kwargs):
        return self._db.get_victim_profiles(*args, **kwargs)

    def get_victim_profile(self, *args, **kwargs):
        return self._db.get_victim_profile(*args, **kwargs)

    def update_victim_tags(self, *args, **kwargs):
        return self._db.update_victim_tags(*args, **kwargs)

    def update_victim_notes(self, *args, **kwargs):
        return self._db.update_victim_notes(*args, **kwargs)

    def update_victim_risk_score(self, *args, **kwargs):
        return self._db.update_victim_risk_score(*args, **kwargs)

    # -- geofences --------------------------------------------------------------------
    def create_geofence(self, *args, **kwargs):
        return self._db.create_geofence(*args, **kwargs)

    def get_geofences(self, *args, **kwargs):
        return self._db.get_geofences(*args, **kwargs)

    def delete_geofence(self, *args, **kwargs):
        return self._db.delete_geofence(*args, **kwargs)

    def check_geofence(self, *args, **kwargs):
        return self._db.check_geofence(*args, **kwargs)

    # -- operator log --------------------------------------------------------------------
    def log_operator_action(self, *args, **kwargs):
        return self._db.log_operator_action(*args, **kwargs)

    def get_operator_log(self, *args, **kwargs):
        return self._db.get_operator_log(*args, **kwargs)

    # -- reports ---------------------------------------------------------------------------
    def save_report(self, *args, **kwargs):
        return self._db.save_report(*args, **kwargs)

    def get_reports(self, *args, **kwargs):
        return self._db.get_reports(*args, **kwargs)

    def get_report(self, *args, **kwargs):
        return self._db.get_report(*args, **kwargs)

    def delete_report(self, *args, **kwargs):
        return self._db.delete_report(*args, **kwargs)

    # -- playbooks ---------------------------------------------------------------------------
    def save_playbook(self, *args, **kwargs):
        return self._db.save_playbook(*args, **kwargs)

    def get_playbooks(self, *args, **kwargs):
        return self._db.get_playbooks(*args, **kwargs)

    def get_playbook(self, *args, **kwargs):
        return self._db.get_playbook(*args, **kwargs)

    def update_playbook(self, *args, **kwargs):
        return self._db.update_playbook(*args, **kwargs)

    def delete_playbook(self, *args, **kwargs):
        return self._db.delete_playbook(*args, **kwargs)

    # -- saved lures ---------------------------------------------------------------------------
    def save_lure(self, *args, **kwargs):
        return self._db.save_lure(*args, **kwargs)

    def get_saved_lures(self, *args, **kwargs):
        return self._db.get_saved_lures(*args, **kwargs)

    def delete_saved_lure(self, *args, **kwargs):
        return self._db.delete_saved_lure(*args, **kwargs)

    # -- network discovery ----------------------------------------------------------------------
    def save_network_discovery(self, *args, **kwargs):
        return self._db.save_network_discovery(*args, **kwargs)

    def get_network_discoveries(self, *args, **kwargs):
        return self._db.get_network_discoveries(*args, **kwargs)

    # -- browser exfil ----------------------------------------------------------------------------
    def save_browser_exfil(self, *args, **kwargs):
        return self._db.save_browser_exfil(*args, **kwargs)

    def get_browser_exfil(self, *args, **kwargs):
        return self._db.get_browser_exfil(*args, **kwargs)

    # -- evasion ------------------------------------------------------------------------------------
    def save_evasion_config(self, *args, **kwargs):
        return self._db.save_evasion_config(*args, **kwargs)

    def get_evasion_configs(self, *args, **kwargs):
        return self._db.get_evasion_configs(*args, **kwargs)

    def delete_evasion_config(self, *args, **kwargs):
        return self._db.delete_evasion_config(*args, **kwargs)

    # -- threat intel ---------------------------------------------------------------------------------
    def save_threat_intel(self, *args, **kwargs):
        return self._db.save_threat_intel(*args, **kwargs)

    def get_threat_intel(self, *args, **kwargs):
        return self._db.get_threat_intel(*args, **kwargs)

    def delete_threat_intel(self, *args, **kwargs):
        return self._db.delete_threat_intel(*args, **kwargs)

    # -- session hijack ---------------------------------------------------------------------------------
    def save_session_hijack(self, *args, **kwargs):
        return self._db.save_session_hijack(*args, **kwargs)

    def get_session_hijacks(self, *args, **kwargs):
        return self._db.get_session_hijacks(*args, **kwargs)

    def delete_session_hijack(self, *args, **kwargs):
        return self._db.delete_session_hijack(*args, **kwargs)

    # -- pivot --------------------------------------------------------------------------------------------
    def save_pivot_record(self, *args, **kwargs):
        return self._db.save_pivot_record(*args, **kwargs)

    def get_pivot_records(self, *args, **kwargs):
        return self._db.get_pivot_records(*args, **kwargs)

    def delete_pivot_record(self, *args, **kwargs):
        return self._db.delete_pivot_record(*args, **kwargs)

    # -- rat -------------------------------------------------------------------------------------------------
    def save_rat_operation(self, *args, **kwargs):
        return self._db.save_rat_operation(*args, **kwargs)

    def get_rat_operations(self, *args, **kwargs):
        return self._db.get_rat_operations(*args, **kwargs)

    def delete_rat_operation(self, *args, **kwargs):
        return self._db.delete_rat_operation(*args, **kwargs)

    def save_rat_shell(self, *args, **kwargs):
        return self._db.save_rat_shell(*args, **kwargs)

    def get_rat_shells(self, *args, **kwargs):
        return self._db.get_rat_shells(*args, **kwargs)

    def delete_rat_shell(self, *args, **kwargs):
        return self._db.delete_rat_shell(*args, **kwargs)

    def save_rat_persistence(self, *args, **kwargs):
        return self._db.save_rat_persistence(*args, **kwargs)

    def get_rat_persistence(self, *args, **kwargs):
        return self._db.get_rat_persistence(*args, **kwargs)

    def delete_rat_persistence(self, *args, **kwargs):
        return self._db.delete_rat_persistence(*args, **kwargs)


# --- module-level singleton ---------------------------------------------------
_repo: Optional[Repository] = None
_repo_lock = threading.Lock()


def get_repository() -> Repository:
    """Process-wide ``Repository`` singleton (lazily created)."""
    global _repo
    if _repo is None:
        with _repo_lock:
            if _repo is None:
                _repo = Repository()
    return _repo


def reset_repository() -> None:
    """Drop the singleton (used by tests)."""
    global _repo
    with _repo_lock:
        _repo = None


__all__ = ["Repository", "get_repository", "reset_repository", "DB_PATH"]


