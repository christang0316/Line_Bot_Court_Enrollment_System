from fastapi import APIRouter, Request, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, FollowEvent, JoinEvent
from linebot.exceptions import InvalidSignatureError
from .line_handlers import handle_message_event, handle_follow_event, handle_join_event

from .deps import settings, get_db

router = APIRouter()

# LINE SDK clients (sync)
line_bot_api = LineBotApi(settings.CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.CHANNEL_SECRET)

@router.post("/callback")
async def line_callback(
    request: Request,
    x_line_signature: str = Header(..., alias="X-Line-Signature"),
    db: Session = Depends(get_db),
):
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        events = parser.parse(body_str, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")


    for event in events:
        if isinstance(event, MessageEvent):
            handle_message_event(event, db, line_bot_api)
        elif isinstance(event, FollowEvent):
            handle_follow_event(event, db, line_bot_api)
        elif isinstance(event, JoinEvent):
            handle_join_event(event, db, line_bot_api)
        

    return "OK"
