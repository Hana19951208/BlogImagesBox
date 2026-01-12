import os
import requests
import json
import sys
import time
import hashlib

# 配置
APP_ID = os.environ.get('WECHAT_APP_ID')
APP_SECRET = os.environ.get('WECHAT_APP_SECRET')
WORKSPACE_DIR = os.path.expanduser("~/blog-sync")
HISTORY_FILE = os.path.join(WORKSPACE_DIR, "sync_history.json")

# 文件列表 (命令行参数)
if len(sys.argv) > 1:
    IMAGES_LIST = sys.argv[1].split()
else:
    IMAGES_LIST = []

def load_history():
    """加载同步历史记录"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history(history):
    """保存同步历史记录"""
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def calculate_md5(file_path):
    """计算文件 MD5"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_access_token():
    if not APP_ID or not APP_SECRET:
        print("❌ 错误：未配置 WECHAT_APP_ID 或 WECHAT_APP_SECRET")
        return None
    
    # 简单的 Token 缓存逻辑
    token_file = os.path.join(WORKSPACE_DIR, "access_token.json")
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                data = json.load(f)
                if data.get('expires_at', 0) > time.time():
                    return data['token']
        except:
            pass

    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if 'access_token' in data:
            # 提前 5 分钟过期
            expires_at = time.time() + data['expires_in'] - 300
            with open(token_file, 'w') as f:
                json.dump({'token': data['access_token'], 'expires_at': expires_at}, f)
            return data['access_token']
        else:
            print(f"❌ 获取 Access Token 失败: {data}")
            return None
    except Exception as e:
        print(f"❌ 网络请求异常: {e}")
        return None

def upload_image(token, file_path, original_path):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    
    # 路径扁平化：blog/2026/img.jpg -> blog_2026_img.jpg
    # 替换 / 为 _，确保文件名合法且保留目录信息
    file_name = original_path.replace("/", "_")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'media': (file_name, f)}
            res = requests.post(url, files=files, timeout=30)
            return res.json()
    except Exception as e:
        return {"errcode": -1, "errmsg": str(e)}

def main():
    print(">>> [WeChat Sync] 开始同步...")
    
    if not IMAGES_LIST:
        print(">>> 没有需要同步的文件。")
        return

    # 初始化工作区
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    
    token = get_access_token()
    if not token:
        sys.exit(1)

    history = load_history()
    success_count = 0
    skip_count = 0
    fail_count = 0

    for img_rel_path in IMAGES_LIST:
        # img_rel_path 是 GitHub 仓库相对路径，如 blog/2024/01/a.jpg
        # 脚本运行时，cwd 下会有下载好的同名文件(经过扁平化处理) 或者 保持原始结构？
        # 根据 Workflow 逻辑，我们会下载到当前目录，且命名为 flattened
        
        # 修正：Workflow 中我们是这样下载的：
        local_filename = img_rel_path.replace("/", "_")
        
        if not os.path.exists(local_filename):
            print(f"⚠️ 本地文件丢失: {local_filename}")
            continue

        # 计算 MD5 检查重复
        file_md5 = calculate_md5(local_filename)
        
        # 注册表 Key: 使用原始路径作为唯一标识 (或者用 MD5，但路径更直观)
        # 考虑到用户可能修改图片内容但保持文件名，用 MD5 双重校验最好
        # 这里为了简单且防重，如果 History 中该路径对应的 MD5 一致，则跳过
        
        if img_rel_path in history:
            if history[img_rel_path].get('md5') == file_md5:
                print(f"⏩ [跳过] 已同步且未变更: {img_rel_path}")
                skip_count += 1
                continue
            else:
                print(f"🔄 [更新] 检测到文件变更: {img_rel_path}")
        
        print(f"🚀 [上传] {img_rel_path} -> {local_filename}")
        result = upload_image(token, local_filename, img_rel_path)
        
        if 'media_id' in result:
            print(f"✅ 同步成功: MediaID={result['media_id']}")
            history[img_rel_path] = {
                'media_id': result['media_id'],
                'url': result.get('url'),
                'md5': file_md5,
                'time': time.time()
            }
            success_count += 1
            # 实时保存，防止崩溃丢失
            save_history(history)
        else:
            print(f"❌ 同步失败: {result}")
            fail_count += 1
            
        time.sleep(1)

    print(f"\n>>> [同步总结] 成功: {success_count}, 跳过: {skip_count}, 失败: {fail_count}")

if __name__ == "__main__":
    main()
