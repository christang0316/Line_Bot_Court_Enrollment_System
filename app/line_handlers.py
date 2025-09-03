# app/line_handlers.py
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from linebot import LineBotApi
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FollowEvent, JoinEvent,
)
from .models import GroupBotState, AdminPermission, QueueEntry, CourtEnum
import json


# ---------- MAIN HANDLER (converted from your snippet) ----------
def handle_message_event(event: MessageEvent, db: Session, line_bot_api: LineBotApi) -> None:
    
    # Only process text messages
    if not isinstance(event.message, TextMessage):
        return

    # Only reply if the message is from a group
    group_id = getattr(event.source, "group_id", None)
    print("group_id:", group_id)
    if not group_id:
        return

    # Fetch necessary data
    bot_state = db.query(GroupBotState).filter(GroupBotState.group_id == group_id).first()
    user_id = event.source.user_id
    user_name = get_user_name(line_bot_api, user_id=user_id, group_id=group_id)
    user_msg = (event.message.text or "").strip().upper()

    # Reply generation
    reply_message = "🤖"  # robot emoji prefix

    
    if user_msg == "SHOW GROUP ID": # Special command to show group ID, no any permission needed
        reply_message += f"Group ID: {group_id}"

    elif bot_state is None: # Group not registered
        reply_message += "This group is not registered to use the bot."

    elif user_msg == "START": # Start the bot (needs permission)
        reply_message += start_bot(db, group_id) if have_permission(db, user_id, group_id, "START") else "No permission"
    
    elif user_msg == "END": # End the bot (needs permission)
        reply_message += end_bot(db, group_id) if have_permission(db, user_id, group_id, "END") else "No permission"
    
    elif user_msg == "CLEAR": # Clear all queues (needs permission)
        reply_message += clear_sheet(db) if have_permission(db, user_id, group_id, "CLEAR") else "No permission"
        
    elif get_bot_state(db, group_id) is True: # Bot is started
        reply_message += "\n" + switch_msg(user_name, user_id, user_msg, group_id, db).strip()
    
    else:
        # Bot not started and no START command => do nothing
        return


    msg = TextSendMessage(
        text=reply_message,
        quick_reply=QuickReply(
            items=[
                QuickReplyButton(action=MessageAction(label="報A場", text="A+1")),
                QuickReplyButton(action=MessageAction(label="報B場", text="B+1")),
                QuickReplyButton(action=MessageAction(label="報C場", text="C+1")),
                QuickReplyButton(action=MessageAction(label="報D場", text="D+1")),
                QuickReplyButton(action=MessageAction(label="查看各場人數", text="Status")),
                QuickReplyButton(action=MessageAction(label="取消我的報隊", text="Cancel")),
                QuickReplyButton(action=MessageAction(label="呼叫A場下一隊", text="A Next")),
                QuickReplyButton(action=MessageAction(label="呼叫B場下一隊", text="B Next")),
                QuickReplyButton(action=MessageAction(label="呼叫C場下一隊", text="C Next")),
                QuickReplyButton(action=MessageAction(label="呼叫D場下一隊", text="D Next")),
            ]
        )
    )

    # 5) Send reply
    line_bot_api.reply_message(event.reply_token, msg)


def handle_follow_event(event: FollowEvent, db: Session, line_bot_api: LineBotApi) -> None:
    """Send a welcome message when a user adds the bot as a friend."""
    user_id = event.source.user_id
    user_name = get_user_name(line_bot_api, user_id=user_id)
    msg = (
        f"Hi！{user_name}\n"
        f"我是中山羽球場報隊機器人🤖\n\n"
        f"⚠️不要在其他地方使用我⚠️\n"
        f"我現在只為中山羽球場報隊群組工作，"
        f"若在別的群組使用我會導致資料亂掉！\n\n"
        f"希望未來能為其他群組工作🦾"
    )
    message = TextSendMessage(text=msg)
    line_bot_api.reply_message(event.reply_token, message)


def handle_join_event(event: JoinEvent, db: Session, line_bot_api: LineBotApi) -> None:
    """Send a message when the bot joins a group."""
    msg = (
        f"🤖中山羽球場報隊機器人 V0.1.0\n\n"
        f"⚠️無法在其他群組使用我⚠️\n"
        f"在非服務的群組中我會呈現死機狀態，"
        f"我現在只為中山羽球報隊群組工作！"
    )
    message = TextSendMessage(text=msg)
    line_bot_api.reply_message(event.reply_token, message)



# ---------------- profiles ----------------
def get_user_name(line_bot_api: LineBotApi, user_id: str, group_id: str | None = None) -> str:
    try:
        if group_id:
            prof = line_bot_api.get_group_member_profile(group_id, user_id)
        else:
            prof = line_bot_api.get_profile(user_id)
        return prof.display_name or "User"
    except Exception:
        return "User"


# ---------------- queue helpers ----------------
def parse_court_from_msg(user_msg: str) -> CourtEnum | None:
    msg = user_msg.strip().upper()
    if msg in ("A+1", "A NEXT", "A"):
        return CourtEnum.A
    if msg in ("B+1", "B NEXT", "B"):
        return CourtEnum.B
    if msg in ("C+1", "C NEXT", "C"):
        return CourtEnum.C
    if msg in ("D+1", "D NEXT", "D"):
        return CourtEnum.D
    return None


# ---------------- main functions: switch message ----------------
def switch_msg(user_name: str, user_id: str, user_msg: str, group_id: str, db: Session) -> str:
    msg = user_msg.strip().upper()

    # General command
    if msg in ("A+1", "B+1", "C+1", "D+1"):
        return enroll(db, msg, user_name, user_id)
    elif msg in ("A NEXT", "B NEXT", "C NEXT", "D NEXT"):
        court = parse_court_from_msg(msg)
        return call_next(db, court) if court else unknown_command()
    elif msg == "CHECK":
        return check_if_enrolled(db, user_id)
    elif msg in ("A", "B", "C", "D"):
        court = parse_court_from_msg(msg)
        return show_list(db, court) if court else unknown_command()
    elif msg == "STATUS":
        return show_status(db)
    elif msg == "CANCEL":
        return delete_user(db, user_name, user_id)
    elif msg == "SHOW USER ID":
        return show_user_id(user_id)
        """
        # Need permission
        elif msg == "CLEAR":
            return clear_sheet(db) if have_permission(db, user_id, group_id) else "No permission"
        elif msg == "START":
            return start_bot(db) if have_permission(db, user_id, group_id) else "No permission"
        elif msg == "END":
            return end_bot(db) if have_permission(db, user_id, group_id) else "No permission"
        elif msg == "SHOW GROUP ID":
            return group_id if have_permission(db, user_id, group_id) else "No permission"
        """
    else:
        return unknown_command()


# ------------ core message operations -> str ------------
def enroll(db: Session, user_msg: str, user_name: str, user_id: str) -> str:
    court = parse_court_from_msg(user_msg)
    if court is None:
        return "無法辨識場地。"

    enrolled_court = find_user_in_court(db, user_id)
    if enrolled_court and enrolled_court != court:
        return f"您已經報隊 {enrolled_court.value} 場地了，無法重複報隊\n\n" + show_list(db, enrolled_court)
    
    idx = waiting_index(db, user_id, court)
    if idx == 0:
        return f"您應正在 {court.value} 場地打球，請下場後再報隊"
    elif idx == -1:
        # First person to enroll, so they get added to the queue
        db.add(QueueEntry(court=court, user_id=user_id, user_name=user_name))
        db.commit()
        return f"{user_name} 報 {court.value} 場成功！\n無人在場，可以直接上\n\n" + show_list(db, court)
    else:
        return f"您已經報隊 {court.value} 場地了\n前方還有 {idx - 1} 組\n\n" + show_list(db, court)

def call_next(db: Session, court: CourtEnum, additional_msg: str = "") -> str:
    """
    Pop head; new head becomes current.
    Concurrency-safe with SELECT ... FOR UPDATE (optional but recommended).
    """
    # Lock the head row if your MySQL engine supports it (InnoDB)
    stmt = (
        select(QueueEntry)
        .where(QueueEntry.court == court)
        .order_by(QueueEntry.id.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    head = db.execute(stmt).scalar_one_or_none()
    if not head:
        return f"{additional_msg}\n{court.value} 場地尚未有人報隊"

    # Pop head
    db.delete(head)
    db.commit()

    # Peek new head
    rows = _ordered_queue_rows(db, court)
    next_name = rows[0][1] if rows else None
    if next_name:
        return f"{additional_msg}\n請 {next_name} 上 {court.value} 場地"
    else:
        return f"{additional_msg}\n{court.value} 場地目前無人報隊"

def check_if_enrolled(db: Session, user_id: str) -> str:
    for c in [CourtEnum.A, CourtEnum.B, CourtEnum.C, CourtEnum.D]:
        idx = waiting_index(db, user_id, c)
        if idx == 0:
            return f"您應正在 {c.value} 場地打球，請下場後再報隊"
        if idx > 0:
            return f"您已經報 {c.value} 場了\n前方還有 {idx - 1} 組\n\n" + show_list(db, c)
    return "您還尚未報隊"

def delete_user(db: Session, user_name: str, user_id: str) -> str:
    court = find_user_in_court(db, user_id)
    if court is None:
        return "未找到您的報隊紀錄"

    rows = _ordered_queue_rows(db, court)
    ids = [r[2] for r in rows]
    pos = ids.index(user_id)  # must exist

    # Delete the row at that position
    row_id = rows[pos][0]
    db.execute(delete(QueueEntry).where(QueueEntry.id == row_id))
    db.commit()

    if pos == 0:
        # Canceled current → immediately promote next head (no message push here; list reflects it)
        return call_next(db, court, additional_msg=f"已取消{user_name}在{court.value}場的報隊")

    return f"已取消 {user_name} 在 {court.value} 場的報隊\n\n" + show_list(db, court)

def show_list(db: Session, court: CourtEnum) -> str:
    rows = _ordered_queue_rows(db, court)
    names = [r[1] for r in rows]

    head = f"{court.value}場地名單：\n\n"
    if not names:
        current = "【現正在場】\n  無人在場上\n\n"
        waiting = ""
    else:
        current = f"【現正在場】\n  {names[0]}\n\n"
        if len(names) > 1:
            waiting = "【等候名單】\n" + "\n".join(f"  {i}. {nm}" for i, nm in enumerate(names[1:], start=1))
        else:
            waiting = ""

    return head + current + waiting


# ---------------- queue query helpers ----------------
def _ordered_queue_rows(db: Session, court: CourtEnum):
    """Return list of (id, user_name, user_id) in FIFO order."""
    stmt = (
        select(QueueEntry.id, QueueEntry.user_name, QueueEntry.user_id)
        .where(QueueEntry.court == court)
        .order_by(QueueEntry.id.asc())
    )
    return db.execute(stmt).all()

def last_row(db: Session, court: CourtEnum) -> int:
    # "cell index" analog = number of rows currently in the sheet
    return db.query(func.count(QueueEntry.id)).filter(QueueEntry.court == court).scalar() or 0

def waiting_index(db: Session, user_id: str | None, court: CourtEnum) -> int:
    """
    0 => current player
    -1 => first to enroll (if no one on court)
    >=1 => waiting position
    """
    rows = _ordered_queue_rows(db, court)  # Fetch all current queue entries
    if user_id is None:
        # When no user is passed, return -total length as the waiting index
        return -len(rows)  # indicates how many are waiting, not including current player
    
    if len(rows) == 0:
        return -1  # First person to enroll (empty court)

    if rows[0][2] == user_id:
        return 0  # User is the current player

    # For other users in the queue, return their index + 1 (1-based)
    for i, row in enumerate(rows[1:], start=1):
        if row[2] == user_id:
            return i  # User is in the waiting list

    return -len(rows)  # User not found in queue, return negative length

def find_user_in_court(db: Session, user_id: str) -> CourtEnum | None:
    for c in [CourtEnum.A, CourtEnum.B, CourtEnum.C, CourtEnum.D]:
        rows = _ordered_queue_rows(db, c)
        if any(r[2] == user_id for r in rows):
            return c
    return None

def is_enrolled(db: Session, user_id: str, court: CourtEnum | None = None) -> bool:
    
    if court is None:
        return find_user_in_court(db, user_id) is not None

    # Check if the user is enrolled in the specified court
    return waiting_index(db, user_id, court) >= 0

def show_status(db: Session) -> str:
    parts = []
    for c in [CourtEnum.A, CourtEnum.B, CourtEnum.C, CourtEnum.D]:
        rows = _ordered_queue_rows(db, c)
        waiting = max(len(rows) - 1, 0)  # exclude the head (current)
        parts.append(f"{c.value}. {waiting} waiting")
    return "\n".join(parts)


# ---------------- permission and bot control ----------------
def have_permission(db: Session, user_id: str, group_id: str, action: str) -> bool:
    """Check if the user has permission to perform a specific action."""
    permission = db.query(AdminPermission).filter(
        AdminPermission.user_id == user_id,
        AdminPermission.group_id == group_id
    ).first()

    if not permission:
        return False  # No permission record found

    # Check specific action
    if action == "START":
        return permission.can_start_bot == 1
    elif action == "END":
        return permission.can_end_bot == 1
    elif action == "CLEAR":
        return permission.can_clear == 1
    return False  # Default: no permission for unknown actions

def get_bot_state(db: Session, group_id: str) -> bool:
    """Return the bot state for the given group. Returns True if bot is ON, False if OFF."""
    state = db.query(GroupBotState).filter(GroupBotState.group_id == group_id).first()
    if state and state.bot_state == 1:
        return True
    return False

def set_bot_state(db: Session, group_id: str, state: bool) -> None:
    """Set the bot state for the given group."""
    bot_state = 1 if state else 0  # Convert boolean to integer (1 = ON, 0 = OFF)

    # Check if the group already has an entry, if not, create it
    existing_state = db.query(GroupBotState).filter(GroupBotState.group_id == group_id).first()
    if existing_state:
        existing_state.bot_state = bot_state
    else:
        new_state = GroupBotState(group_id=group_id, bot_state=bot_state)
        db.add(new_state)
    db.commit()

def start_bot(db: Session, group_id: str) -> str:
    set_bot_state(db, group_id, True)
    reply_message = (
        "中山羽球場報隊機器人 V0.1.0\n\n"
        "🏸現在開始報隊！\n"
        "系統將以各位的Line名稱報隊\n\n"
        "🗣️指令（A可替換成B~D）\n"
        f"{'A+1':<9}：在A場地報隊\n"
        f"{'A':<11}：顯示A場地的名單\n"
        f"{'A Next':<6}：A場換下一組上場\n"
        f"{'Status':<7}：查看等候組數\n"
        f"{'Cancel':<6}：取消報隊\n\n"
        "👇歡迎善用快速指令"
    )
    return reply_message

def end_bot(db: Session, group_id: str) -> str:
    set_bot_state(db, group_id, False)
    return "Bot has been shut down, type 'start' to start again."

def clear_sheet(db: Session) -> str:
    """Clears the queue (SHOULD CHECK IS PERMITTED BEFORE CALLING)."""
    
    # Clear all queues (all courts)
    for court in [CourtEnum.A, CourtEnum.B, CourtEnum.C, CourtEnum.D]:
        # Clear the queue entries for the given court
        db.query(QueueEntry).filter(QueueEntry.court == court).delete()

    db.commit()

    return "所有場地的報隊已清空。"


# ---------------- misc ----------------
def show_user_id(user_id: str) -> str:
    return user_id

def unknown_command() -> str:
    return "未知的指令"

