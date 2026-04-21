import os
import requests

# 1. 基础配置
# 洛克王国数据网关 (由 Entropy-Increase-Team 提供)
API_URL = "https://wegame.shallow.ink/api/v1/games/rocom/merchant/info?refresh=true"
# NotifyMe 新版官方服务器地址
NOTIFYME_SERVER = "https://notifyme-server.wzn556.top/api/send"

# 2. 从环境变量读取敏感配置 (GitHub Secrets)
ROCOM_API_KEY = os.environ.get("ROCOM_API_KEY")
NOTIFYME_UUID = os.environ.get("NOTIFYME_UUID")
BARK_KEY = os.environ.get("BARK_KEY")

def get_merchant_data():
    """从 API 获取商人售卖数据"""
    if not ROCOM_API_KEY:
        return None, None, None, "错误：环境变量中未配置 ROCOM_API_KEY"
    
    headers = {"X-API-Key": ROCOM_API_KEY}
    
    try:
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status()
        res_json = response.json()
        
        if res_json.get("code") != 0:
            return None, None, None, f"接口返回错误: {res_json.get('message', '未知错误')}"
            
        data = res_json.get("data", {})
        activities = data.get("merchantActivities") or data.get("merchant_activities") or []
        
        if not activities:
            return None, None, None, "当前暂无远行商人数据"
            
        activity = activities[0]
        props = activity.get("get_props", [])
        pets = activity.get("get_pets", [])
        items = props + pets
        
        if not items:
            return None, None, None, "当前轮次商人没有携带任何商品"
        
        # --- 数据加工 ---
        # 提取商品纯文本列表 (用于通知栏摘要)
        item_names = [i.get("name", "未知") for i in items]
        body_summary = f"当前售卖: {'、'.join(item_names)}"
        
        # 拼接 Markdown 格式 (用于 NotifyMe 详情展示)
        content_md = "### 🛒 洛克王国：远行商人已刷新\n\n---\n\n"
        for i in items:
            name = i.get("name", "未知")
            icon = i.get("icon_url", "")
            content_md += f"![{name}]({icon}) **{name}**\n\n"
        
        # 提取第一个商品的图片 (用于 Bark 的图标/大图预览)
        first_icon = items[0].get("icon_url") if items else ""
            
        return body_summary, content_md, first_icon, None

    except Exception as e:
        return None, None, None, f"获取数据异常: {e}"

def push_via_notifyme(title, body, md):
    """通过 NotifyMe 推送 (适配新版 UUID 协议)"""
    if not NOTIFYME_UUID:
        print("未配置 NOTIFYME_UUID，跳过此通道")
        return
        
    payload = {
        "data": {
            "uuid": NOTIFYME_UUID,
            "ttl": 86400,
            "priority": "high",
            "data": {
                "title": title,
                "body": body,
                "markdown": md,
                "group": "洛克王国",
                "bigText": True,
                "record": 1
            }
        }
    }
    
    try:
        res = requests.post(NOTIFYME_SERVER, json=payload, headers={"Content-Type": "application/json"})
        print(f"NotifyMe 状态: {res.status_code}, {res.text}")
    except Exception as e:
        print(f"NotifyMe 推送异常: {e}")

def push_via_bark(title, body, icon_url):
    """通过 Bark 推送 (iOS 专用)"""
    if not BARK_KEY:
        print("未配置 BARK_KEY，跳过此通道")
        return
        
    bark_url = f"https://api.day.app/{BARK_KEY}"
    payload = {
        "title": title,
        "body": body,
        "group": "洛克王国",
        "icon": icon_url,      # 设置通知左侧的小图标
        "image": icon_url,     # 在通知右侧显示大图预览
        "isArchive": 1         # 自动保存到历史记录
    }
    
    try:
        res = requests.post(bark_url, json=payload)
        print(f"Bark 状态: {res.status_code}, {res.text}")
    except Exception as e:
        print(f"Bark 推送异常: {e}")

if __name__ == "__main__":
    summary, markdown, icon, error = get_merchant_data()
    
    if error:
        push_title = "⚠️ 远行商人监控异常"
        push_body = error
        push_md = f"**错误详情：**\n{error}"
    else:
        push_title = "📢 远行商人已刷新"
        push_body = summary
        push_md = markdown

    # 并行推送：根据 Secret 配置自动选择通道
    if NOTIFYME_UUID:
        push_via_notifyme(push_title, push_body, push_md)
        
    if BARK_KEY:
        push_via_bark(push_title, push_body, icon)
