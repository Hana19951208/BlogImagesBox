# 🖼️ Blog Images Box

个人博客专属图床项目，集成图片自动压缩、CDN 预热以及每日壁纸自动存档功能。

## ✨ 特性

- **增量压缩**：改用高效的 Linux 原生工具（jpegoptim, optipng）对新增/修改图片进行针对性压缩。解决第三方 Action 全量扫描导致的资源浪费。
- **公众号同步**：自动将新图片同步至微信公众号素材库（利用腾讯云中转方案绕过 IP 白名单）。
- **针对性预热**：仅对本次新增或修改的图片进行预热，避免全量扫描，提高效率。
- **并发控制**：内置并发冲突防护，确保多图连续上传时的 Git 提交安全。
- **CDN 预热**：图片压缩提交后，自动请求 CDN 节点触发缓存。
- **自动化存档**：集成 Bing 和 Unsplash 每日壁纸自动抓取与分类存档。
- **结构化存储**：按照日期和来源清晰组织图片目录，方便管理和直接引用。

## 📂 目录结构

```text
.
├── .github/workflows/      # GitHub Actions 自动化流水线
├── blog/                   # 通用博客图片存储（按日期分类）
│   └── 2026-01/
├── wallpapers/             # 壁纸存档
│   ├── bing/               # 必应每日壁纸（包含 meta.json 和故事）
│   └── unsplash/           # Unsplash 精选壁纸
└── README.md
```

## 🚀 自动化流程

项目托管于 GitHub，通过 `.github/workflows/compress-images.yml` 驱动：

1. **触发条件**：推送图片或手动触发。内置 `concurrency` 并发控制，排队执行，彻底杜绝 Git 提交冲突。
2. **精准筛选**：通过 `git diff --diff-filter=AM` 仅提取本次变动的文件，不扫描无关目录。
3. **针对性压缩**：
   - **JPG/JPEG**：使用 `jpegoptim` 限制大小在 400KB 以内。
   - **PNG**：使用 `optipng` 执行无损逻辑优化。
   - **WebP**：默认跳过二次优化以保持画质。
4. **自动回写**：动态感知变更文件并提交回仓库，修复了因固定匹配规则（pathspec）导致的报错。
5. **CDN 预热**：
   - 10s 延迟等待：确保 GitHub 文件节点完成状态切换。
   - 实时输出预热结果（✅ 状态码 - URL）。

## 🛠️ 配置说明

### GitHub Secrets / Variables

- `GITHUB_TOKEN`: 默认提供。
- `CDN_DOMAIN` (Optional): CDN 访问域名。在 **Settings -> Secrets -> Actions** 中配置，默认回退为 `img.fangenwu.cn`。

### 微信公众号同步 (可选)
需配置以下 Secrets 以启用同步功能（使用中转服务器方案）：
- `WECHAT_APP_ID`: 公众号 AppID
- `WECHAT_APP_SECRET`: 公众号 AppSecret
- `SERVER_HOST`: 中转服务器 IP (150.158.24.67)
- `SERVER_USER`: SSH 用户名 (root)
- `SERVER_PASSWORD`: SSH 登录密码

#### 💡 SSH 连接失败排查 (Handshake Failed)
如果您在本地 Mac 可以登录但在 GitHub Actions 失败，请检查：
1. **密码尾部空格**：请确保在 GitHub Secrets 中粘贴密码时，末尾没有多余的空格或换行符。
2. **腾讯云安全拦截**：部分云服务器会限制海外 IP 的高频 SSH 访问，建议在腾讯云后台防火墙将端口 22 设为全开放。
3. **推荐使用密钥**：若密码登录持续失败，建议更换为 `SERVER_KEY` (SSH Key) 方式，稳定性更高。

#### ⚙️ 同步逻辑细节：
- **注册表模式 (Registry Pattern)**：在服务器端维护 `sync_history.json`，通过 MD5 校验文件是否变动，避免重复上传素材，节省微信素材库额度。
- **路径扁平化**：原始路径 `blog/2026/img.jpg` 会自动转义为 `blog_2026_img.jpg` 作为微信素材标题，方便后台管理和搜索。
- **持久化脚本**：同步脚本持久化存放于服务器 `~/blog-sync/` 目录下，每次执行前会自动检查并从 GitHub 获取最新版本。






## 📝 调试与志

我们在 Workflow 中增加了详细的日志输出，您可以在 GitHub Actions 的运行日志中查看：
- **[日志]**: 流程开始与结束。
- **[信息]**: 发现的待处理图片列表。
- **[调试]**: 单个图片的预热全路径及响应状态码。


---

**Proudly powered by GitHub Actions & Cloudflare.**
