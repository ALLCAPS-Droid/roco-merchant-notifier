import os
import requests
import asyncio
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

# ================= 1. 配置区域 =================
ROCOM_API_KEY = os.environ.get("ROCOM_API_KEY")
IMGBB_KEY = os.environ.get("IMGBB_KEY")
NOTIFYME_UUID = os.environ.get("NOTIFYME_UUID")
BARK_KEY = os.environ.get("BARK_KEY")

GAME_API_URL = "https://wegame.shallow.ink/api/v1/games/rocom/merchant/info?refresh=true"
NOTIFYME_SERVER = "https://notifyme-server.wzn556.top/api/send"

# 模板文件夹路径
ASSETS_DIR = os.path.abspath("assets/yuanxing-shangren")
HTML_TEMPLATE_FILE = "index.html"
TEMP_RENDER_FILE = "temp_render.html"

# ================= 2. 数据获取与处理 =================
async def get_merchant_data():
    """获取远行商人 JSON 数据"""
    if not ROCOM_API_KEY: 
        return None, "错误：未配置 API Key (ROCOM_API_KEY)"
    
    headers = {"X-API-Key": ROCOM_API_KEY}
    try:
        resp = requests.get(GAME_API_URL, headers=headers, timeout=30)
        resp.raise_for_status()
        res_json = resp.json()
        if res_json.get("code") != 0:
            return None, f"接口返回错误: {res_json.get('message')}"
        return res_json.get("data", {}), None
    except Exception as e:
        return None, f"获取数据异常: {e}"

def process_data_for_template(data):
    """将原始 JSON 加工成 HTML 模板(Jinja2)需要的格式"""
    if not data: return {}
    
    activities = data.get("merchantActivities") or []
    activity = activities[0] if activities else {}
    props = activity.get("get_props") or []
    pets = activity.get("get_pets") or []
    products = props + pets
    
    # 构建模板变量
    template_data = {
        "title": activity.get("name", "远行商人"),
        "subtitle": activity.get("start_date", "每日 08:00 / 12:00 / 16:00 / 20:00 刷新"),
        "product_count": len(products),
        "round_info": {
            "current": "当前", 
            "total": 4,
            "countdown": "请抓紧时间兑换" 
        },
        "products": []
    }
    
    # 填充商品列表
    for p in products:
        template_data["products"].append({
            "name": p.get("name", "未知"),
            # 直接使用接口返回的网络图片地址！不需要本地资源！
            "image": p.get("icon_url", ""), 
            "time_label": "本轮商品" 
        })
        
    return template_data

# ================= 3. 图像渲染与图床上传 =================
async def render_to_image(processed_data):
    """使用 Jinja2 渲染 HTML 并用 Playwright 截图"""
    if not processed_data: return None
    
    screenshot_file = "merchant_render.jpg"
    temp_html_path = os.path.join(ASSETS_DIR, TEMP_RENDER_FILE)
    
    try:
        # 1. 使用 Jinja2 替换 HTML 里的占位符
        env = Environment(loader=FileSystemLoader(ASSETS_DIR))
        template = env.get_template(HTML_TEMPLATE_FILE)
        rendered_html_string = template.render(processed_data)
        
        # 2. 将渲染好的 HTML 写入临时文件（确保相对路径的 CSS/图片能加载）
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(rendered_html_string)
            
        # 3. 启动浏览器截图
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1600, "height": 1200})
            
            # 访问刚才生成的本地临时文件
            await page.goto(f"file://{temp_html_path}")
            await page.wait_for_load_state("networkidle")
            
            await page.screenshot(path=screenshot_file, type="jpeg", quality=90, full_page=True)
            await browser.close()
            
        print(f"✅ 图片渲染成功: {screenshot_file}")
        return screenshot_file
        
    except Exception as e:
        print(f"❌ 渲染图片失败: {e}")
        return None
    finally:
        # 4. 无论成功失败，销毁临时文件保持仓库干净
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)

async def upload_to_imgbb(image_path):
    """上传截图到 ImgBB 图床"""
    if not image_path or not IMGBB_KEY: return None
    url = "https://api.imgbb.com/1/upload"
    try:
        with open(image_path, "rb") as f:
            payload = {"key": IMGBB_KEY}
            files = {"image": f}
            res = requests.post(url, data=payload, files=files, timeout=30)
            json_data = res.json()
            if json_data.get("status") == 200:
                img_url = json_data["data"]["url"]
                print(f"✅ ImgBB 上传成功: {img_url}")
                return img_url
            else:
                print(f"❌ ImgBB 上传失败: {json_data.get('error', {}).get('message')}")
                return None
    except Exception as e:
        print(f"❌ 图床请求异常: {e}")
        return None

# ================= 4. 消息推送分发 =================
def push_notifyme(title, body, image_url):
    if not NOTIFYME_UUID: return
    payload = {
        "data": {
            "uuid": NOTIFYME_UUID,
            "ttl": 86400,
            "priority": "high",
            "data": {
                "title": title,
                "body": body,
                "group": "洛克王国",
                "bigText": True,
                "record": 1
            }
        }
    }
    if image_url: 
        payload["data"]["data"]["markdown"] = f"![render]({image_url})"
        
    try:
        requests.post(NOTIFYME_SERVER, json=payload, timeout=10)
        print("✅ NotifyMe 推送已发送")
    except Exception as e: 
        print(f"❌ NotifyMe 推送失败: {e}")

def push_bark(title, body, image_url):
    if not BARK_KEY: return
    bark_url = f"https://api.day.app/{BARK_KEY}"
    payload = {
        "title": title,
        "body": body,
        "group": "洛克王国",
        "image": image_url,  
        "isArchive": 1
    }
    try:
        requests.post(bark_url, data=payload, timeout=10)
        print("✅ Bark 推送已发送")
    except Exception as e: 
        print(f"❌ Bark 推送失败: {e}")

# ================= 5. 主程序入口 =================
async def main():
    raw_data, err = await get_merchant_data()
    
    if err:
        push_title = "⚠️ 远行商人监控异常"
        push_body = err
        hosted_img_url = None
    else:
        push_title = "📢 洛克王国：远行商人已刷新 (合成图)"
        push_body = "商人带货列表见详情大图"
        
        processed_data = process_data_for_template(raw_data)
        local_image_file = await render_to_image(processed_data)
        hosted_img_url = await upload_to_imgbb(local_image_file)
    
    push_notifyme(push_title, push_body, hosted_img_url)
    push_bark(push_title, push_body, hosted_img_url)

if __name__ == "__main__":
    asyncio.run(main())
