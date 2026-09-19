"""Friends list, follower lists and the messaging inbox."""
from __future__ import annotations

from ..http import router as R
from ..http.router import Request
from ..models import users
from ..social import follows, friends, messages
from .base import (api_error, api_ok, flash_redirect, login_required, render,
                   router)


@router.get("/friends")
@login_required
def friends_page(req: Request):
    uid = int(req.user["id"])
    tab = req.query.get("tab", "friends")
    return render(req, "friends.html", tab=tab,
                  friends_list=friends.list_friends(uid, 200),
                  incoming=friends.incoming_requests(uid),
                  outgoing=friends.outgoing_requests(uid),
                  followers=follows.followers(uid, 100),
                  following=follows.following(uid, 100),
                  counts=follows.counts(uid),
                  online_fn=users.is_online)


@router.get("/messages")
@login_required
def inbox(req: Request):
    uid = int(req.user["id"])
    box = req.query.get("box", "inbox")
    rows = messages.sent(uid) if box == "sent" else messages.inbox(uid)
    view = []
    for row in rows:
        view.append({
            "id": int(row["id"]),
            "who": row["recipient_name"] if box == "sent" else row["sender_name"],
            "subject": row["subject"],
            "preview": messages.preview(row["body"]),
            "created_at": int(row["created_at"]),
            "unread": box == "inbox" and not row["read_at"],
        })
    return render(req, "messages.html", box=box, rows=view,
                  unread=messages.unread_count(uid))


def _safe_back(value: str, fallback: str = "/messages") -> str:
    """Where "Send" should land.

    Only same-site paths are honoured, so the parameter cannot be used to
    bounce somebody off the site after they press Send.
    """
    value = (value or "").strip()
    if not value.startswith("/") or value.startswith("//"):
        return fallback
    return value


def _referring_page(req: Request, fallback: str = "/messages") -> str:
    """The page the compose form was opened from, for the Back/After-send trip."""
    explicit = req.query.get("back", "")
    if explicit:
        return _safe_back(explicit, fallback)
    referer = req.headers.get("referer", "")
    if referer:
        try:
            from urllib.parse import urlsplit
            parts = urlsplit(referer)
            host = req.headers.get("host", "")
            if not parts.netloc or not host or parts.netloc == host:
                path = parts.path + (("?" + parts.query) if parts.query else "")
                if not path.startswith("/messages/compose"):
                    return _safe_back(path, fallback)
        except ValueError:
            pass
    return fallback


@router.get("/messages/compose")
@login_required
def compose(req: Request):
    return render(req, "compose.html", to=req.query.get("to", ""),
                  subject=req.query.get("subject", ""), body="", error="",
                  back=_referring_page(req))


@router.post("/messages/compose")
@login_required
def compose_post(req: Request):
    form = req.data()
    back = _safe_back(str(form.get("back", "")))
    try:
        messages.send(int(req.user["id"]), str(form.get("to", "")),
                      str(form.get("subject", "")), str(form.get("body", "")))
    except messages.MessageError as exc:
        return render(req, "compose.html", to=str(form.get("to", "")),
                      subject=str(form.get("subject", "")),
                      body=str(form.get("body", "")), error=str(exc),
                      back=back)
    # Back to wherever they were -- a profile, the home page, the inbox --
    # rather than always dropping them in the inbox.
    return flash_redirect(back, "Message sent.")


@router.get("/messages/<message_id:int>")
@login_required
def read_message(req: Request, message_id: str = "0"):
    uid = int(req.user["id"])
    message = messages.get(int(message_id), uid)
    if message is None:
        return R.not_found("That message is not in your mailbox.")
    messages.mark_read(int(message_id), uid)
    return render(req, "message.html", message=message,
                  thread=messages.thread_for(message, uid),
                  other=(message["sender_name"]
                         if int(message["recipient_id"]) == uid
                         else message["recipient_name"]))


@router.post("/messages/<message_id:int>/delete")
@login_required
def delete_message(req: Request, message_id: str = "0"):
    messages.delete(int(message_id), int(req.user["id"]))
    return flash_redirect("/messages", "Message deleted.")


@router.post("/api/messages/send")
@login_required
def api_send(req: Request):
    data = req.data()
    try:
        message_id = messages.send(int(req.user["id"]),
                                   str(data.get("to", "")),
                                   str(data.get("subject", "")),
                                   str(data.get("body", "")))
    except messages.MessageError as exc:
        return api_error(str(exc))
    return api_ok(id=message_id)


@router.get("/api/messages/recent")
@login_required
def api_recent(req: Request):
    return api_ok(rows=messages.recent(int(req.user["id"]), 8))


@router.get("/api/messages/thread")
@login_required
def api_thread(req: Request):
    """The conversation with one player, for the floating messenger."""
    uid = int(req.user["id"])
    other = users.get_by_username(req.query.get("with", ""))
    if other is None:
        return api_error("No such player.", 404)
    rows = messages.conversation(uid, int(other["id"]), 20)
    messages.mark_thread_read(uid, int(other["id"]))
    return api_ok(other=other["username"], rows=rows,
                  unread=messages.unread_count(uid))


@router.get("/api/users/suggest")
@login_required
def api_user_suggest(req: Request):
    """Type-ahead for any "who do you mean" box (the compose To field)."""
    return api_ok(users=users.suggest(req.query.get("q", ""), 8,
                                      int(req.user["id"])))


@router.post("/api/settings/prefs")
@login_required
def api_prefs(req: Request):
    data = req.data()
    values = {}
    if "messenger" in data:
        values["messenger"] = bool(data.get("messenger"))
    return api_ok(prefs=users.set_prefs(int(req.user["id"]), values))


@router.get("/api/social/counts")
@login_required
def counts(req: Request):
    """One poll drives every live element in the chrome.

    Credits and the theme come back too so a second device signed into the
    same account catches up without a reload.
    """
    uid = int(req.user["id"])
    fresh = users.get_by_id(uid) or req.user
    return api_ok(unread=messages.unread_count(uid),
                  requests=friends.pending_count(uid),
                  friends=friends.count_friends(uid),
                  credits=int(fresh["credits"]),
                  theme=users.theme_of(fresh))
