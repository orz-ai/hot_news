import logging
import os

import requests
import telegram.constants
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.helpers import escape_markdown

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

supported_sites = {
    "百度": "baidu",
    "少数派": "shaoshupai",
    "微博": "weibo",
    "知乎": "zhihu",
    "36氪": "36kr",
    "吾爱破解": "52pojie",
    "哔哩哔哩": "bilibili",
    "豆瓣": "douban",
    "虎扑": "hupu",
    "贴吧": "tieba",
    "掘金": "juejin",
    "抖音": "douyin",
    "V2EX": "v2ex",
    "今日头条": "jinritoutiao"
}


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send a message when the command /news is issued.
    """

    user = update.effective_user
    response_message = f"哈喽！ {user.first_name} {user.last_name if user.last_name else ''}, 我是一个新闻机器人。 请选择想要了解的站点热榜:\n\n"

    # Create the inline keyboard layout
    reply_markup = build_reply_makeup()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response_message,
        reply_markup=reply_markup
    )


async def selected_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Return the selected site's news.
    """
    query = update.callback_query
    await query.answer()

    news_url = f"https://orz.ai/dailynews/?platform={supported_sites[query.data]}"

    resp = requests.get(news_url)

    if resp.status_code != 200:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Failed to get news from {query.data}, please try again later.",
        )
        return

    response_message = f"下面是来自*{query.data}*的最新热榜：\n\n"

    news_datas = resp.json()['data']
    for i, news_data in enumerate(news_datas):
        if i >= 10:
            break

        response_message += f"{i + 1}\. [{escape_markdown(news_data['title'], version=2)}]({escape_markdown(news_data['url'], version=2)})\n\n"

    reply_markup = build_reply_makeup()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response_message,
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )


def build_reply_makeup():
    """
    Build the inline keyboard markup.
    """
    keyboard = []
    row = []
    i = 0
    for k in supported_sites.keys():
        row.append(InlineKeyboardButton(k, callback_data=k))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
        i += 1

    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


if __name__ == '__main__':
    # bot token
    token = os.getenv('TG_BOT_TOKEN')
    if not token:
        logging.error("Please set the environment variable 'TG_BOT_TOKEN'")
        exit(1)

    # if you want to use proxy
    # proxy_url = 'http://127.0.0.1:7890'
    # app = ApplicationBuilder().token(token).proxy(proxy_url).get_updates_proxy_url(proxy_url).build()

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler(['start', 'news'], news))
    app.add_handler(telegram.ext.CallbackQueryHandler(selected_news))

    # use polling mode
    app.run_polling()
