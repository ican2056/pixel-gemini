# Pixel Gemini Offer Checker

单文件 Replit 版本。程序通过可见的 Chromium 登录 Google，并检查 Google One 页面中的 Gemini Offer。

## 在 Replit 使用

1. 导入仓库，等待 `requirements.txt` 和 `replit.nix` 中的依赖完成安装。
2. 点击 **Run**。
3. 在 Console 输入 Google 邮箱和密码；密码输入时不显示。
4. 如果出现身份验证器页面，在 Console 输入当前六位验证码。
5. 如果出现验证码、设备确认或其他特殊页面，在 Replit VNC 中手动处理，然后回到 Console 按回车继续。

Chromium 以有界面模式运行。根据 Replit 的机制，原生窗口打开时会自动显示 VNC 面板。

账号、密码和验证码不会写入文件，也不会发送到 Telegram。浏览器会在流程结束后自动关闭。
