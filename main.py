import os
import json
import requests
import asyncio
from playwright.async_api import async_playwright

# 1. 配置区域：从 GitHub Secrets 读取环境变量
ROCOM_API_KEY = os.environ.get("ROCOM_API_KEY")
IMGBB_KEY = os.environ.get("IMGBB_KEY")
NOTIFYME_UUID = os.environ.get("NOTIFYME_UUID")
BARK_KEY = os.environ.get("BARK_KEY")

# 接口地址
GAME_API_URL = "https://wegame.shallow.ink/api/v1/games/rocom/merchant/info?refresh=true"
NOTIFYME_SERVER = "https://notifyme-server.wzn556.top/api/send"
# 本地 HTML 模板路径
HTML_TEMPLATE_PATH = os.path.abspath("assets/yuanxing-shangren/index.html")

async def get_merchant_data():
    """获取远行商人 JSON 数据"""
    if not ROCOM_API_KEY:
        return None, "错误：未配置 ROCOM_API_KEY"
    headers = {"X-API-Key": ROCOM_API_KEY}
    try:
        # 使用 requests 获取 JSON
        resp = requests.get(GAME_API_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        res_json = resp.json()
        if res_json.get("code") != 0:
            return None, f"接口返回错误: {res_json.get('message')}"
        return res_json.get("data", {}), None
    except Exception as e:
        return None, f"获取数据异常: {e}"

async def render_to_image(data):
    """使用浏览器渲染 HTML 并截图"""
    if not data:
        return None
    
    screenshot_file = "merchant_render.jpg"
    try:
        async with async_playwright() as p:
            # 启动无头浏览器
            browser = await p.chromium.launch()
            # 创建新页面
            page = await browser.new_page()
            # 设置高分辨率视口，保证图片清晰
            await page.set_viewport_size({"width": 1600, "height": 1200})
            
            # 注入数据到页面 window 变量，供 HTML 模板读取
            # 注意：这里注入的变量名需与你的 index.html 中的读取逻辑一致
            await page.add_init_script(f"window.merchantData = {json.dumps(data)};")
            
            # 加载本地 HTML 文件
            await page.goto(f"file://{HTML_TEMPLATE_PATH}")
            # 等待网络空闲，确保图片资源加载完
            await page.wait_for_load_state("networkidle")
            
            # 截图
            await page.screenshot(path=screenshot_file, type="jpeg", quality=90, full_page=True)
            await browser.close()
            print(f"✅ 图片渲染成功: {screenshot_file}")
            return screenshot_file
    except Exception as e:
        print(f"❌ 渲染图片失败: {e}")
        return None

async def upload_to_imgbb(image_path):
    """将生成的截图上传至 ImgBB"""
    if not image_path or not IMGBB_KEY:
        print("跳过图床上传: 未生成图片或未配置 IMGBB_KEY")
        return None
        
    url = "https://api.imgbb.com/1/upload"
    try:
        with open(image_path, "rb") as f:
            payload = {"key": IMGBB_KEY}
            files = {"image": f}
            res = requests.post(url, data=payload, files=files, timeout=30)
            res.json_data = res.json()
            
            if res.json_data.get("status") == 200:
                img_url = res.json_data["data"]["url"]
                print(f"✅ ImgBB 上传成功: {img_url}")
                return img_url
            else:
                print(f"❌ ImgBB 上传失败: {res.json_data.get('error', {}).get('message')}")
                return None
    except Exception as e:
        print(f"❌ 图床请求异常: {e}")
        return None

def push_notifyme(title, body, markdown, image_url):
    """NotifyMe 推送"""
    if not NOTIFYME_UUID: return
    
    payload = {
        "data": {
            "uuid": NOTIFYME_UUID,
            "ttl": 86400,
            "priority": "high",
            "data": {
                "title": title,
                "body": body,
                "markdown": markdown + (f"\n\n![render]({image_url})" if image_url else ""),
                "group": "洛克王国",
                "bigText": True,
                "record": 1
            }
        }
    }
    try:
        requests.post(NOTIFYME_SERVER, json=payload, timeout=10)
        print("NotifyMe 已发送")
    except Exception as e: print(f"NotifyMe 推送失败: {e}")

def push_bark(title, body, image_url):
    """Bark 推送"""
    if not BARK_KEY: return
    
    bark_url = f"https://api.day.app/{BARK_KEY}"
    payload = {
        "title": title,
        "body": body,
        "group": "洛克王国",
        "image": image_url,  # 通知栏显示大图
        "isArchive": 1
    }
    try:
        requests.post(bark_url, data=payload, timeout=10)
        print("Bark 已发送")
    except Exception as e: print(f"Bark 推送失败: {e}")

async def main():
    # 1. 获取数据
    data, err = await get_merchant_data()
    
    if err:
        title, body, md, img_url = "⚠️ 远行商人监控异常", err, f"**错误：** {err}", None
    else:
        title = "📢 远行商人已刷新"
        # 简单处理 body 文字
        activities = data.get("merchantActivities", [])
        activity = activities[0] if activities else {}
        props = activity.get("get_props", [])
        pets = activity.get("get_pets", [])
        body = f"当前售卖: {'、'.join([i.get('name') for i in props+pets])}"
        md = "### 🛒 远行商人刷新详情"
        
        # 2. 渲染图片并上传
        image_file = await render_to_image(data)
        img_url = await upload_to_imgbb(image_file)
    
    # 3. 执行推送
    push_notifyme(title, body, md, img_url)
    push_bark(title, body, img_url)

if __name__ == "__main__":
    asyncio.run(main())
