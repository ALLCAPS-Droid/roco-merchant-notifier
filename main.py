import requests

# 洛克王国数据网关 (熵增项目组端点)
API_URL = "https://wegame.shallow.ink/api/v1/games/rocom/merchant/info?refresh=true"

# ！！！1. 在此填入你从项目方申请到的 API Key ！！！
ROCOM_API_KEY = "sk-ff14f964051a5c966564e29b5bd3a768"

# ！！！2. 在此填入你 NotifyMe 设备的真实 UUID ！！！
NOTIFYME_UUID = "jk9JwjyvKZ8FL75eei4c3Z"

# 新版 NotifyMe 官方服务端地址
NOTIFYME_SERVER_URL = "https://notifyme-server.wzn556.top/api/send"

def get_merchant_data():
    try:
        # 这里的 headers 就是出示通行证的关键！
        headers = {
            "X-API-Key": ROCOM_API_KEY
        }
        
        # 发送请求时带上 headers
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        res_json = response.json()
        
        if res_json.get("code") != 0:
            return None, f"接口返回错误: {res_json.get('message', '未知错误')}"
            
        data = res_json.get("data", {})
        activities = data.get("merchantActivities") or data.get("merchant_activities") or []
        
        if not activities:
            return None, "当前暂无远行商人数据"
            
        activity = activities[0]
        props = activity.get("get_props", [])
        pets = activity.get("get_pets", [])
        
        if not props and not pets:
            return None, "当前轮次商人没有携带任何商品"
        
        # 提取商品纯文本名称（用于在手机通知栏简略显示）
        item_names = [item.get("name", "未知") for item in props + pets]
        body_text = f"当前售卖: {'、'.join(item_names)}"
        
        # 拼接 Markdown 格式的内容（用于在 App 内完美渲染图片）
        content_md = "### 🛒 当前售卖道具与精灵\n\n---\n\n"
        for item in props + pets:
            name = item.get("name", "未知商品")
            icon_url = item.get("icon_url", "")
            content_md += f"![{name}]({icon_url}) **{name}**\n\n"
            
        return body_text, content_md

    except Exception as e:
        return None, f"获取商人数据失败: {e}"

def push_via_notifyme(body_text, markdown_text):
    if body_text is None:
        title = "⚠️ 远行商人监控异常"
        body = markdown_text 
        md = markdown_text
    else:
        title = "📢 洛克王国：远行商人已刷新"
        body = body_text
        md = markdown_text

    # NotifyMe 请求体配置
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
    
    # NotifyMe 需要的 Content-Type 请求头
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(NOTIFYME_SERVER_URL, json=payload, headers=headers)
        if res.status_code == 200:
            print("NotifyMe 新版 API 推送成功！")
        else:
            print(f"推送失败，状态码: {res.status_code}, 返回内容: {res.text}")
    except Exception as e:
        print(f"推送请求异常: {e}")

if __name__ == "__main__":
    b_text, md_text = get_merchant_data()
    push_via_notifyme(b_text, md_text)
