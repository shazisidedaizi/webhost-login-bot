import os
import asyncio
import aiohttp
from playwright.async_api import async_playwright

LOGIN_URL = "https://client.webhostmost.com/login"

# ============ Telegram 通知 ============
async def tg_notify(message: str):
    token = os.getenv("TG_BOT_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ 未设置 TG_BOT_TOKEN / TG_CHAT_ID，跳过通知")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, data={"chat_id": chat_id, "text": message})
        except Exception as e:
            print(f"⚠️ Telegram 消息发送失败: {e}")

async def tg_notify_photo(photo_path: str, caption: str = ""):
    token = os.getenv("TG_BOT_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    async with aiohttp.ClientSession() as session:
        try:
            with open(photo_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("chat_id", chat_id)
                data.add_field("photo", f, filename=os.path.basename(photo_path))
                if caption:
                    data.add_field("caption", caption)
                await session.post(url, data=data)
        except Exception as e:
            print(f"⚠️ Telegram 图片发送失败: {e}")

# ============ 登录逻辑 ============
async def login():
    email = os.getenv("LOGIN_EMAIL")
    password = os.getenv("LOGIN_PASSWORD")
    if not email or not password:
        print("❌ 缺少 LOGIN_EMAIL 或 LOGIN_PASSWORD 环境变量")
        await tg_notify("❌ 登录失败：未配置账号或密码")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(60000)

        try:
            print("🌐 打开登录页...")
            await page.goto(LOGIN_URL)
            await page.wait_for_selector('input[name="email"]')

            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')

            # 等待跳转或检查成功标识
            await page.wait_for_timeout(5000)
            current_url = page.url

            # 判断是否登录成功
            if "dashboard" in current_url or "clientarea" in current_url:
                msg = f"✅ 登录成功！账号：{email}"
                print(msg)
                await tg_notify(msg)
            else:
                screenshot = "login_failed.png"
                await page.screenshot(path=screenshot, full_page=True)
                msg = f"❌ 登录失败，当前URL: {current_url}"
                print(msg)
                await tg_notify(msg)
                await tg_notify_photo(screenshot, caption=msg)
        except Exception as e:
            screenshot = "error.png"
            await page.screenshot(path=screenshot, full_page=True)
            msg = f"❌ 执行登录脚本出错: {e}"
            print(msg)
            await tg_notify(msg)
            await tg_notify_photo(screenshot, caption=msg)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(login())
