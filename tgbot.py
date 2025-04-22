import logging
from telegram import Update, InputMediaPhoto, InputMediaDocument, InputMediaVideo, InputMediaAudio
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, JobQueue
import config

# 配置日志
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储用户的消息记录
user_messages = {}

def start(update: Update, context: CallbackContext) -> None:
    """发送消息，介绍机器人的功能"""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'嗨，{user.mention_markdown_v2()}！\n'
        '我是一个可以接收和发送消息的机器人，可以用于各种场景，如定时消息推送、关键词回复等。'
    )

def echo(update: Update, context: CallbackContext) -> None:
    """回复用户发送的消息"""
    user_id = update.effective_user.id
    message_text = update.message.text

    # 存储用户的消息记录
    user_messages[user_id] = message_text

    # 检查是否包含特定关键词并回复
    if '你好' in message_text:
        update.message.reply_text('你好！很高兴为你服务。')
    else:
        update.message.reply_text(f'你发送的消息是：{message_text}')

def send_message(update: Update, context: CallbackContext) -> None:
    """向指定用户发送消息"""
    if len(context.args) < 2:
        update.message.reply_text('使用方法：/send_message [用户ID] [消息内容]')
        return

    user_id = context.args[0]
    message_text = ' '.join(context.args[1:])

    try:
        context.bot.send_message(chat_id=user_id, text=message_text)
        update.message.reply_text(f'消息已发送给用户 {user_id}')
    except Exception as e:
        update.message.reply_text(f'发送消息失败：{str(e)}')

def send_photo(update: Update, context: CallbackContext) -> None:
    """向指定用户发送图片"""
    if len(context.args) < 2:
        update.message.reply_text('使用方法：/send_photo [用户ID] [图片URL]')
        return

    user_id = context.args[0]
    photo_url = context.args[1]

    try:
        context.bot.send_photo(chat_id=user_id, photo=photo_url)
        update.message.reply_text(f'图片已发送给用户 {user_id}')
    except Exception as e:
        update.message.reply_text(f'发送图片失败：{str(e)}')

def send_document(update: Update, context: CallbackContext) -> None:
    """向指定用户发送文件"""
    if len(context.args) < 2:
        update.message.reply_text('使用方法：/send_document [用户ID] [文件URL]')
        return

    user_id = context.args[0]
    document_url = context.args[1]

    try:
        context.bot.send_document(chat_id=user_id, document=document_url)
        update.message.reply_text(f'文件已发送给用户 {user_id}')
    except Exception as e:
        update.message.reply_text(f'发送文件失败：{str(e)}')

def send_media_group(update: Update, context: CallbackContext) -> None:
    """向指定用户发送媒体组"""
    if len(context.args) < 3:
        update.message.reply_text('使用方法：/send_media_group [用户ID] [媒体URL1] [媒体URL2] ...')
        return

    user_id = context.args[0]
    media_urls = context.args[1:]

    try:
        media = []
        for url in media_urls:
            if url.lower().endswith(('.png', '.jpg', '.jpeg')):
                media.append(InputMediaPhoto(url))
            elif url.lower().endswith(('.mp4', '.avi')):
                media.append(InputMediaVideo(url))
            elif url.lower().endswith(('.mp3', '.wav')):
                media.append(InputMediaAudio(url))
            else:
                media.append(InputMediaDocument(url))

        if not media:
            update.message.reply_text('未找到有效的媒体文件')
            return

        context.bot.send_media_group(chat_id=user_id, media=media)
        update.message.reply_text(f'媒体组已发送给用户 {user_id}')
    except Exception as e:
        update.message.reply_text(f'发送媒体组失败：{str(e)}')

def timer(update: Update, context: CallbackContext) -> None:
    """接收定时任务的命令"""
    chat_id = update.message.chat_id
    try:
        # 获取定时时间（秒）
        due = int(context.args[0])
        if due < 0:
            update.message.reply_text('定时时间必须为正整数！')
            return

        # 获取定时发送的消息内容
        if len(context.args) < 2:
            update.message.reply_text('使用方法：/timer [时间（秒）] [消息内容]')
            return
        message_text = ' '.join(context.args[1:])

        # 添加定时任务
        context.job_queue.run_once(send_timer_message, due, context=(chat_id, message_text), name=str(chat_id))
        update.message.reply_text(f'定时任务已设置，将在 {due} 秒后发送消息')
    except (IndexError, ValueError):
        update.message.reply_text('定时任务设置失败，请检查参数是否正确！')

def send_timer_message(context: CallbackContext) -> None:
    """定时任务发送消息的回调函数"""
    job = context.job
    context.bot.send_message(chat_id=job.context[0], text=job.context[1])

def error_handler(update: Update, context: CallbackContext) -> None:
    """处理错误"""
    logger.warning(f'更新 {update} 引发错误 {context.error}')

def main() -> None:
    """启动机器人"""
    # 创建 Updater 并传递 bot 的 token
    updater = Updater(config.API_KEY)

    # 获取 dispatcher 来注册 handlers
    dp = updater.dispatcher

    # 添加命令处理器
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("send_message", send_message))
    dp.add_handler(CommandHandler("send_photo", send_photo))
    dp.add_handler(CommandHandler("send_document", send_document))
    dp.add_handler(CommandHandler("send_media_group", send_media_group))
    dp.add_handler(CommandHandler("timer", timer))

    # 添加消息处理器，处理普通文本消息
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # 添加错误处理器
    dp.add_error_handler(error_handler)

    # 启动机器人，开始轮询
    updater.start_polling()

    # 等待 Ctrl+C 停止机器人
    updater.idle()

if __name__ == '__main__':
    main()
