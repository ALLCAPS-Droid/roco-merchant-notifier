# 洛克王国世界：远行商人自动提醒助手 🛒

![License](https://img.shields.io/github/license/ALLCAPS-Droid/Roco-Merchant)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Actions](https://img.shields.io/badge/GitHub-Actions-orange)

这是一个基于 **GitHub Actions** 的轻量化自动化工具，专门用于监控《洛克王国世界》中“远行商人”的刷新状态。每当商人带着道具刷新时，系统会自动抓取图文数据，并精准推送到你的手机（支持 iOS 和 Android）。

### ✨ 特性

* **精准过滤**：内置北京时间校准，自动计算当前商人轮次（1-4轮）与倒计时，彻底过滤上一轮过期商品。
* **完美 UI 渲染**：结合 `Jinja2` 模板引擎与 `Playwright` 无头浏览器，直接读取本地字体和背景图，实现与原版完全一致的极致视觉效果（精准去除多余留白）。
* **极速图床托管**：集成 ImgBB API，自动将高质量截图转化为网络链接，减轻推送通道压力。
* **双通道推送**：
  * 🍏 **iOS**: 通过 [Bark](https://github.com/Finb/Bark) 实现带大图的系统级通知。
  * 🤖 **Android**: 通过 NotifyMe 实现高优先级通知推送。
* **防拥堵机制**：GitHub Actions 定时任务设置“提前 5 分钟”排队策略，有效对抗官方节点延迟。

---

### 🚀 快速上手

#### 1. Fork 仓库或创建新仓库
点击页面右上角的 `Fork` 按钮，将本项目复制到你的账号下；或者直接新建一个私有/公开仓库，并上传 `main.py`。

#### 2. 申请 API Key
本项目的数据源由 [Entropy-Increase-Team](https://github.com/Entropy-Increase-Team/) 提供。
你需要前往该项目主页或相关社区，获取用于调用 WeGame 接口的 `ROCOM_API_KEY`。

#### 3. 配置 GitHub Secrets (核心步骤)
进入你的 GitHub 仓库 -> `Settings` -> `Secrets and variables` -> `Actions`，点击 `New repository secret`，依次添加以下 **4 个环境变量**：

| Secret 名称 | 必填 | 说明 | 获取方式 |
| :--- | :---: | :--- | :--- |
| `ROCOM_API_KEY` | ✅ | 游戏数据接口访问凭证 | 社区网关提供 |
| `IMGBB_KEY` | ✅ | 图床上传 API Key | 注册 [ImgBB](https://api.imgbb.com/) 获取 |
| `BARK_KEY` | 选填 | iOS 推送 Key | Bark App 内复制 |
| `NOTIFYME_UUID` | 选填 | Android 推送 UUID | NotifyMe App 内获取 |

*(注：`BARK_KEY` 和 `NOTIFYME_UUID` 至少填入一个即可接收通知，未填写的通道脚本会自动跳过，不会报错。)*

#### 4. 开启 GitHub Actions
点击仓库上方的 `Actions` 选项卡，确保它已启用（点击 `I understand my workflows, go ahead and enable them`）。

---

### ⏰ 定时任务说明

本项目默认在 `.github/workflows/schedule.yml` 中配置了 GitHub 定时任务，对应北京时间 **08:00、12:00、16:00、20:00** 运行。

**💡 进阶技巧：如何保证秒级准时？**
由于 GitHub 官方的 Cron 触发存在排队延迟（可能延迟 5-30 分钟），追求极致准时的玩家可以：
1.  在 [cron-job.org](https://cron-job.org/) 创建任务。
2.  配置 POST 请求通过 GitHub API 远程触发本项目的 `workflow_dispatch`。
3.  详细教程可参考 [新闻联播文字稿自动化推送系统](https://github.com/ALLCAPS-Droid/xin-wen-lian-bo)。

---

### 🛠️ 技术实现

* **Python 3.10**: 核心逻辑编写。
* **Requests**: 数据抓取与网络请求。
* **Playwright**: 驱动 Chromium 浏览器进行 HTML 解析与精准截图。
* **Jinja2**: 将动态商品数据注入到静态 HTML 模板中。

---

### ⚖️ 免责声明
本项目仅供学习交流使用，数据来源于第三方开源社区。作者对接口的稳定性不作保证，请勿用于商业用途。

---

## 🙏 鸣谢

* 数据接口及原始前端 UI 模板设计来自：[Entropy-Increase-Team/astrbot_plugin_rocom](https://github.com/Entropy-Increase-Team/astrbot_plugin_rocom)
