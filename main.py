import requests

# 接口地址
API_URL = "https://wegame.shallow.ink/api/v1/games/rocom/merchant/info?refresh=true"

# ！！！把下面这行换成你刚才在 PushPlus 复制的真实 Token ！！！
PUSHPLUS_TOKEN = "7096a091cde043978795eff97064971b"

def get_merchant_data():
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        res_json = response.json()

        if res_json.get("code") != 0:
            return f"接口返回错误: {res_json.get('message', '未知错误')}"

        data = res_json.get("data", {})
        activities = data.get("merchantActivities") or data.get("merchant_activities") or []

        if not activities:
            return "当前暂无远行商人数据"

        activity = activities[0]
        props = activity.get("get_props", [])
        pets = activity.get("get_pets", [])

        if not props and not pets:
            return "当前轮次商人没有携带任何商品"

        content_html = f"<h3>商人已刷新，当前售卖：</h3><div style='display: flex; flex-direction: column; gap: 8px;'>"
        for item in props + pets:
            name = item.get("name", "未知商品")
            icon_url = item.get("icon_url", "")
            content_html += f"<div style='display: flex; align-items: center;'><img src='{icon_url}' width='40' height='40' style='margin-right: 10px; border-radius: 5px;'/> <span><b>{name}</b></span></div>"

        content_html += "</div>"
        return content_html

    except Exception as e:
        return f"获取商人数据失败，请检查网络或接口状态: {e}"

def push_to_mobile(content):
    title = "📢 洛克王国：远行商人已刷新" if "刷新" in content else "⚠️ 远行商人监控异常"
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html"
    }
    try:
        requests.post("http://www.pushplus.plus/send", json=payload)
        print("推送触发完成")
    except Exception as e:
        print(f"推送请求异常: {e}")

if __name__ == "__main__":
    html_data = get_merchant_data()
    push_to_mobile(html_data)
