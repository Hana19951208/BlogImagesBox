# 🖼️ Blog Images Box

个人博客专属图床项目，集成图片自动压缩、CDN 预热以及每日壁纸自动存档功能。

## ✨ 特性

- **自动压缩**：利用 GitHub Actions 自动对上传的图片进行无损/近无损压缩，优化访问速度并节省流量。
- **CDN 预热**：图片压缩并提交后，自动请求 CDN 节点进行缓存预热。
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

1. **触发条件**：当有新图片（`.jpg`, `.png`, `.webp` 等）推送到仓库时，或通过 GitHub Actions 界面**手动触发**（处理最近一次提交）。
2. **图片压缩**：使用高效 Action 对图片执行无损/近无损压缩。
3. **自动提交**：压缩后的图片会自动回写到仓库。
4. **CDN 预热**：
   - 提取本次提交中变更的图片列表。
   - 依次请求 `https://{CDN_DOMAIN}/{path}` 触发 CDN 缓存。
   - 打印详细日志及 HTTP 状态码，方便监控预热情况。

## 🛠️ 配置说明

### GitHub Secrets / Variables

- `GITHUB_TOKEN`: 默认提供，用于压缩后的代码提交。
- `CDN_DOMAIN` (Optional): 在 **Settings -> Secrets and variables -> Actions -> Secrets** 中配置。


## 📝 调试与志

我们在 Workflow 中增加了详细的日志输出，您可以在 GitHub Actions 的运行日志中查看：
- **[日志]**: 流程开始与结束。
- **[信息]**: 发现的待处理图片列表。
- **[调试]**: 单个图片的预热全路径及响应状态码。


---

**Proudly powered by GitHub Actions & Cloudflare.**
