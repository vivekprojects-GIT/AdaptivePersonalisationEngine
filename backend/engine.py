"""In-memory per-user conversation state.

Holds the rolling chat history and last-turn pointers used to assemble prompts,
plus the APE bookkeeping for the adaptive lane:

- session_id            APE's conversation key. Minted per thread; re-minted on
                        clear/reset so reward attribution can't cross threads.
- pending_signals       UI signals (thumbs via /api/rate) queued to ride the
                        NEXT /turn call to APE.
- last_widget_present   whether the previous adaptive answer rendered a widget —
                        context for the signal lane router ("as a table" etc.).
- last_strategy /       what APE picked last turn; reused (sticky) on
  last_format_rule      widget_redraw turns, which skip the APE call.
"""

import uuid


class UserStore:
    def __init__(self):
        self.users: dict[str, dict] = {}

    def _new_user(self) -> dict:
        return {
            "history": [],
            "last_message": "",
            "last_response": "",
            "msg_count": 0,
            # --- APE integration state ---
            "session_id": uuid.uuid4().hex,
            "pending_signals": [],
            "last_widget_present": False,
            "last_strategy": "",
            "last_format_rule": "",
        }

    def get_user(self, uid: str) -> dict:
        if uid not in self.users:
            self.users[uid] = self._new_user()
        else:
            # Users created before the APE fields existed (or restored state).
            self.users[uid].setdefault("session_id", uuid.uuid4().hex)
            self.users[uid].setdefault("pending_signals", [])
            self.users[uid].setdefault("last_widget_present", False)
            self.users[uid].setdefault("last_strategy", "")
            self.users[uid].setdefault("last_format_rule", "")
        return self.users[uid]

    def reset_user(self, uid: str) -> None:
        self.users.pop(uid, None)

    def clear_conversation_thread(self, uid: str) -> None:
        """Drop chat history and last-turn pointers. Starts a NEW APE session:
        signals after a clear must not reward answers from the old thread."""
        u = self.get_user(uid)
        u["history"] = []
        u["last_message"] = ""
        u["last_response"] = ""
        u["session_id"] = uuid.uuid4().hex
        u["pending_signals"] = []
        u["last_widget_present"] = False
        u["last_strategy"] = ""
        u["last_format_rule"] = ""


engine = UserStore()
