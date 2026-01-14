"""
Automated Clash Royale match watcher.

This worker polls the Clash Royale battlelog API for players that still have
unfinished matches in Supabase and marks winners without any manual admin
interaction. It respects the documented 10 requests/second API limit by using
a simple leaky-bucket rate limiter and per-player scheduling so each tag is
checked roughly every 25–30 seconds until the match finishes.

Environment variables (.env):
    CR_API_KEY                – Clash Royale API key (Bearer token)
    SUPABASE_URL              – Supabase project URL (e.g. https://xyz.supabase.co)
    SUPABASE_SERVICE_ROLE_KEY – Service-role key with RLS bypass privileges
    POLL_INTERVAL_SECONDS     – Optional override for the polling interval (default 25)
    ACTIVE_REFRESH_SECONDS    – Optional frequency for reloading the active match list (default 60)
"""

from __future__ import annotations

import heapq
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# Utility functions


def _ts() -> float:
    return time.monotonic()


def parse_battle_time(value: str) -> float:
    """
    Convert Clash Royale battleTime (e.g. 20240101T101234.000Z) into epoch seconds.
    """
    try:
        dt = datetime.strptime(value, "%Y%m%dT%H%M%S.%fZ")
    except ValueError:
        # Fallback without milliseconds
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ")
    return dt.replace(tzinfo=timezone.utc).timestamp()


def normalize_tag(tag: str) -> str:
    return tag.replace("#", "").strip().upper()


# --------------------------------------------------------------------------- #
# Supabase REST client


class SupabaseRESTClient:
    def __init__(self, base_url: str, service_key: str):
        self.rest_url = base_url.rstrip("/") + "/rest/v1"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            }
        )

    def fetch_active_matches(self) -> List[Dict]:
        """
        Return unfinished matches along with player tags and tournament created_at.
        """
        params = {
            "select": "id,player_a_id,player_b_id,round_number,created_at,"
            "playersA:player_a_id(tag),playersB:player_b_id(tag),"
            "tournaments:tournament_id(created_at)",
            "completed": "is.false",
        }
        resp = self.session.get(f"{self.rest_url}/matches", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def mark_match_complete(
        self, match_id: str, winner_id: str, extra: Optional[Dict] = None
    ) -> Dict:
        payload = {"winner_id": winner_id, "completed": True}
        if extra:
            payload.update(extra)
        resp = self.session.patch(
            f"{self.rest_url}/matches",
            params={"id": f"eq.{match_id}"},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()[0] if resp.json() else {}


# --------------------------------------------------------------------------- #
# Clash Royale API


class ClashRoyaleAPI:
    def __init__(self, api_key: str, max_rps: float = 8.0):
        self.base = "https://api.clashroyale.com/v1"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            }
        )
        self.min_interval = 1.0 / max_rps
        self.last_request = 0.0

    def _rate_limit(self):
        delta = time.time() - self.last_request
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)

    def battlelog(self, player_tag: str) -> List[Dict]:
        self._rate_limit()
        encoded = requests.utils.quote(f"#{normalize_tag(player_tag)}", safe="")
        resp = self.session.get(
            f"{self.base}/players/{encoded}/battlelog", timeout=15
        )
        self.last_request = time.time()
        if resp.status_code == 429:
            raise RuntimeError("Rate limited by Clash Royale API (429)")
        resp.raise_for_status()
        return resp.json()


# --------------------------------------------------------------------------- #
# Worker data models


@dataclass(order=True)
class QueueEntry:
    next_poll: float
    priority: int = field(compare=False)
    match_id: str = field(compare=False)
    player_tag: str = field(compare=False)
    opponent_tag: str = field(compare=False)
    player_id: str = field(compare=False)
    opponent_id: str = field(compare=False)
    tournament_start: float = field(compare=False)
    misses: int = field(default=0, compare=False)

    def reschedule(self, interval: float, priority_counter: int):
        self.next_poll = _ts() + interval
        self.priority = priority_counter
        self.misses += 1


class MatchWatcher:
    def __init__(
        self,
        supabase: SupabaseRESTClient,
        cr_api: ClashRoyaleAPI,
        poll_interval: float,
        refresh_interval: float,
    ):
        self.supabase = supabase
        self.cr_api = cr_api
        self.poll_interval = poll_interval
        self.refresh_interval = refresh_interval
        self.entries: Dict[str, QueueEntry] = {}
        self.queue: List[QueueEntry] = []
        self.priority_counter = 0
        self.last_refresh = 0.0

    def refresh_matches(self):
        now = _ts()
        if self.queue and now - self.last_refresh < self.refresh_interval:
            return
        self.last_refresh = now
        matches = self.supabase.fetch_active_matches()
        seen_ids = set()
        for match in matches:
            match_id = str(match["id"])
            seen_ids.add(match_id)
            players_a = (match.get("playersA") or {}) or {}
            players_b = (match.get("playersB") or {}) or {}
            tag_a = players_a.get("tag")
            tag_b = players_b.get("tag")
            if not tag_a or not tag_b:
                continue
            tournament = match.get("tournaments") or {}
            start_str = tournament.get("created_at") or match.get("created_at")
            try:
                start_ts = datetime.fromisoformat(start_str.replace("Z", "+00:00")).timestamp()
            except Exception:
                start_ts = time.time() - 3600
            if match_id not in self.entries:
                entry = QueueEntry(
                    next_poll=_ts(),
                    priority=self._next_priority(),
                    match_id=match_id,
                    player_tag=tag_a,
                    opponent_tag=tag_b,
                    player_id=str(match["player_a_id"]),
                    opponent_id=str(match["player_b_id"]),
                    tournament_start=start_ts,
                )
                self.entries[match_id] = entry
                heapq.heappush(self.queue, entry)
        # Remove entries for matches that are no longer active
        for stale_id in list(self.entries.keys()):
            if stale_id not in seen_ids:
                del self.entries[stale_id]

    def _next_priority(self) -> int:
        self.priority_counter += 1
        return self.priority_counter

    def run_forever(self):
        print("Match watcher started", flush=True)
        while True:
            self.refresh_matches()
            if not self.queue:
                print("No active matches. Sleeping 10s.", flush=True)
                time.sleep(10)
                continue
            entry = heapq.heappop(self.queue)
            now = _ts()
            if entry.next_poll > now:
                sleep_time = entry.next_poll - now
                time.sleep(sleep_time)
            try:
                completed = self.poll_entry(entry)
            except RuntimeError as err:
                print(f"Rate limited ({err}). Backing off.", flush=True)
                entry.reschedule(interval=self.poll_interval, priority_counter=self._next_priority())
                heapq.heappush(self.queue, entry)
                time.sleep(1)
                continue
            except Exception as exc:
                print(f"Error polling {entry.player_tag}: {exc}", flush=True)
                entry.reschedule(interval=self.poll_interval * 1.5, priority_counter=self._next_priority())
                heapq.heappush(self.queue, entry)
                continue
            if completed:
                print(f"Match {entry.match_id} resolved.", flush=True)
                self.entries.pop(entry.match_id, None)
            else:
                # Alternate player tags every few misses to hedge against stale logs
                if entry.misses % 4 == 3:
                    entry.player_tag, entry.opponent_tag = entry.opponent_tag, entry.player_tag
                    entry.player_id, entry.opponent_id = entry.opponent_id, entry.player_id
                entry.reschedule(interval=self.poll_interval, priority_counter=self._next_priority())
                heapq.heappush(self.queue, entry)

    def poll_entry(self, entry: QueueEntry) -> bool:
        log = self.cr_api.battlelog(entry.player_tag)
        target = normalize_tag(entry.opponent_tag)
        newest_battle = None
        for battle in log:
            opp_list = battle.get("opponent") or []
            team_list = battle.get("team") or []
            if not opp_list or not team_list:
                continue
            opponent = opp_list[0]
            opp_tag = normalize_tag(opponent.get("tag", ""))
            if opp_tag != target:
                continue
            battle_ts = parse_battle_time(battle["battleTime"])
            if battle_ts < entry.tournament_start:
                continue
            newest_battle = battle
            break
        if not newest_battle:
            return False

        crowns_team = newest_battle["team"][0].get("crowns", 0)
        crowns_opponent = newest_battle["opponent"][0].get("crowns", 0)
        if crowns_team == crowns_opponent:
            # Tie or best-of-n scenario – skip for next poll
            return False
        winner_id = entry.player_id if crowns_team > crowns_opponent else entry.opponent_id
        battle_iso = datetime.utcfromtimestamp(parse_battle_time(newest_battle["battleTime"])).isoformat() + "Z"
        extra = {
            "auto_verified_at": datetime.utcnow().isoformat() + "Z",
            "last_battle_time": battle_iso,
            "last_battle_raw": newest_battle.get("battleTime")
        }
        self.supabase.mark_match_complete(entry.match_id, winner_id, extra=extra)
        return True


# --------------------------------------------------------------------------- #
# Entrypoint


DEFAULT_SUPABASE_URL = "https://izmzpnfpcdxdqwgghsyq.supabase.co"
DEFAULT_SUPABASE_ANON_KEY = "sb_publishable_4kW-ZwFSbzqPkWz63jYcGw_Kldfdp7R"


def main():
    load_dotenv()
    cr_key = os.getenv("CR_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL", DEFAULT_SUPABASE_URL)
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase_key = service_key or anon_key or DEFAULT_SUPABASE_ANON_KEY
    key_source = "service role" if service_key else ("anon env" if anon_key else "bundled anon")
    if not cr_key:
        print("Missing CR_API_KEY in environment (see .env).")
        sys.exit(1)

    poll_interval = float(os.getenv("POLL_INTERVAL_SECONDS", "25"))
    refresh_interval = float(os.getenv("ACTIVE_REFRESH_SECONDS", "60"))

    print(f"Using Supabase {key_source} key for {supabase_url}", flush=True)
    supabase_client = SupabaseRESTClient(supabase_url, supabase_key)
    clash_api = ClashRoyaleAPI(cr_key, max_rps=8.0)
    watcher = MatchWatcher(
        supabase=supabase_client,
        cr_api=clash_api,
        poll_interval=poll_interval,
        refresh_interval=refresh_interval,
    )
    watcher.run_forever()


if __name__ == "__main__":
    main()
