#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
webhostmost 自动登录脚本
使用 Playwright 模拟登录 https://client.webhostmost.com/login
可选 Telegram 通知
"""

import os
import asyncio
import aiohttp
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


# --- Telegram 通知函数 ---
async def tg_notify(message: str):
    token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    if not token or not chat_id:
        print("⚠️ 未配置 Telegram 通知，跳过。")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, data={"chat_id": chat_id, "text": message})
        except Exception as e:
            print("⚠️ Telegram 通知失败:", e)


# --- 主逻辑 ---
async def login_webhost():
    email = os.environ.get("WEBHOST_EMAIL")
    password = os.environ.get("WEBHOST_PASSWORD")
    login_url = "https://client.webhostmost.com/login"

    if not email or not password:
        print("❌ 缺少 WEBHOST_EMAIL 或 WEBHOST_PASSWORD 环境变量。")
        return

    print("🚀 启动浏览器进行登录...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(login_url, timeout=60000)
            await page.wait_for_selector("input[type=email]", timeout=20000)
            await page.fill("input[type=email]", email)
            await page.fill("input[type=password]", password)

            # 点击登录按钮
            await page.click("button[type=submit]")
            await page.wait_for_load_state("networkidle", timeout=20000)

            # 检查是否成功登录
            if "dashboard" in page.url or "clientarea" in page.url:
                msg = "✅ 登录成功：https://client.webhostmost.com/"
            else:
                msg = f"⚠️ 登录后跳转异常，当前 URL：{page.url}"

            print(msg)
            await tg_notify(msg)

        except PlaywrightTimeoutError:
            msg = "❌ 登录超时，网站可能无响应。"
            print(msg)
            await tg_notify(msg)
        except Exception as e:
            msg = f"❌ 登录脚本异常: {e}"
            print(msg)
            await tg_notify(msg)
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(login_webhost())
