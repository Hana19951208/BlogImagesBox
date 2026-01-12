# 🖼️ Blog Images Box

个人博客专属图床项目，集成图片自动压缩、CDN 预热以及每日壁纸自动存档功能。

## ✨ 特性

- **增量压缩**：改用高效的 Linux 原生工具（jpegoptim, optipng）对新增/修改图片进行针对性压缩。解决第三方 Action 全量扫描导致的资源浪费。
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



## 📝 调试与志

我们在 Workflow 中增加了详细的日志输出，您可以在 GitHub Actions 的运行日志中查看：
- **[日志]**: 流程开始与结束。
- **[信息]**: 发现的待处理图片列表。
- **[调试]**: 单个图片的预热全路径及响应状态码。


---

**Proudly powered by GitHub Actions & Cloudflare.**
