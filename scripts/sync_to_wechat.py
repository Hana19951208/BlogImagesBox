import os
import requests
import json
import sys
import time
import hashlib

def load_env():
    """本地调试：从 .env 文件加载环境变量"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("💡 [Info] 已从本地 .env 加载配置")
    else:
        # 生产环境通常直接从系统环境变量读取
        pass

# 在生产环境，变量由 Action 注入；本地调试从 .env 加载
load_env()

# 配置
APP_ID = os.environ.get('WECHAT_APP_ID')
APP_SECRET = os.environ.get('WECHAT_APP_SECRET')
GITHUB_REPO = os.environ.get('GITHUB_REPOSITORY')

WORKSPACE_DIR = os.path.expanduser("~/blog-sync")
HISTORY_FILE = os.path.join(WORKSPACE_DIR, "sync_history.json")

# 文件列表 (命令行参数)
if len(sys.argv) > 1:
    IMAGES_LIST = sys.argv[1].split()
else:
    IMAGES_LIST = []

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except: return {}
    return {}

def save_history(history):
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_image(img_rel_path):
    """从 GitHub 下载图片到本地"""
    if not GITHUB_REPO:
        print("❌ 错误：未配置 GITHUB_REPOSITORY 环境变量")
        return None
        
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{img_rel_path}"
    local_filename = img_rel_path.replace("/", "_")
    local_path = os.path.join(os.getcwd(), local_filename)
    
    print(f">>> [Download] 正在下载: {img_rel_path}")
    try:
        # 增加 10s 连接超时和 30s 总超时，防止 hang 住
        res = requests.get(raw_url, timeout=(10, 30), stream=True)
        if res.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            return local_path
        else:
            print(f"❌ 下载失败 (HTTP {res.status_code}): {raw_url}")
    except Exception as e:
        print(f"❌ 下载异常: {e}")
    return None

def get_access_token():
    token_file = os.path.join(WORKSPACE_DIR, "access_token.json")
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                data = json.load(f)
                if data.get('expires_at', 0) > time.time():
                    return data['token']
        except: pass

    print(f">>> [Auth] 正在向微信请求新的 Access Token (AppID: {APP_ID[:4]}***)")
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if 'access_token' in data:
            expires_at = time.time() + data['expires_in'] - 300
            os.makedirs(WORKSPACE_DIR, exist_ok=True)
            with open(token_file, 'w') as f:
                json.dump({'token': data['access_token'], 'expires_at': expires_at}, f)
            print("✅ Access Token 刷新成功")
            return data['access_token']
        else:
            print(f"❌ 获取 Access Token 失败，微信返回结果: {data}")
            if data.get('errcode') == 40164:
                print("💡 提示：这通常是因为您的本地 IP 不在微信公众号的【IP白名单】中。")
                print("   请在 GitHub Actions 中测试，或者前往微信后台添加本地 IP。")
            return None
    except Exception as e:
        print(f"❌ 网络请求异常 (无法连接微信 API): {e}")
        return None


def upload_to_wechat(token, file_path, original_path):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    file_name = original_path.replace("/", "_")
    try:
        with open(file_path, 'rb') as f:
            files = {'media': (file_name, f)}
            res = requests.post(url, files=files, timeout=30)
            return res.json()
    except Exception as e:
        return {"errcode": -1, "errmsg": str(e)}

def main():
    if not IMAGES_LIST:
        print(">>> 无需处理的任务")
        return

    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    token = get_access_token()
    if not token:
        print("❌ 无法获取 Access Token，同步终止")
        sys.exit(1)

    history = load_history()
    
    for img_rel_path in IMAGES_LIST:
        local_path = None
        try:
            # 1. 下载图片
            local_path = download_image(img_rel_path)
            if not local_path or not os.path.exists(local_path):
                continue

            # 2. 幂等检查 (MD5)
            file_md5 = calculate_md5(local_path)
            if img_rel_path in history and history[img_rel_path].get('md5') == file_md5:
                print(f"⏩ [Skip] 已存在且无变更: {img_rel_path}")
                continue
            
            # 3. 上传微信
            print(f"🚀 [Sync] 上传中: {img_rel_path}")
            result = upload_to_wechat(token, local_path, img_rel_path)
            
            if 'media_id' in result:
                print(f"✅ 成功! MediaID: {result['media_id']}")
                history[img_rel_path] = {
                    'media_id': result['media_id'],
                    'md5': file_md5,
                    'time': time.ctime()
                }
                save_history(history)
            else:
                print(f"❌ 失败: {result}")
                
        except Exception as e:
            print(f"❌ 处理过程中出现异常: {e}")
        finally:
            # 4. 无论成功、失败还是跳过，都清理本地临时文件
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
        
        time.sleep(1)

if __name__ == "__main__":
    main()

