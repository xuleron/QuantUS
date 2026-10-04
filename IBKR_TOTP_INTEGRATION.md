# IBKR ib_async TOTP 自动登陆集成

## 概述

本集成为 xQQQ 项目添加了 TOTP（Time-based One-Time Password）2FA 自动登陆支持。**IB Gateway 运行在 Docker 容器内（gnzsnz/ib-gateway），通过 localhost:4001 对交易系统可用**，两者共享 host 网络模式。

## 架构

```
┌──────────────────────────────────────────┐
│  Docker Container (host network mode)    │
├──────────────────────────────────────────┤
│  IB Gateway Service                      │
│  (ghcr.io/gnzsnz/ib-gateway)            │
│  - Listens on localhost:4001 (paper:4002)│
│  - TOTP auto-login support               │
│         ▲                                 │
│         │ localhost:4001                  │
│         │                                 │
│  xQQQ Trader (ib_async)                  │
│  - Connects to localhost:4001            │
│  - Auto-generates TOTP for 2FA           │
└──────────────────────────────────────────┘
```

## 集成内容

### 1. 依赖更新
- 添加 `pyotp>=2.8` 到 `requirements-live.txt`（用于生成 TOTP 代码）
- ib_async 已在要求中（维护版本的 ib_insync）
- Java + IB Gateway 通过 Docker 镜像提供（gnzsnz/ib-gateway）

### 2. 配置变量
**`.env.example` 更新：**
```bash
# IBKR（IB Gateway 集成在容器内）
IBKR_HOST=127.0.0.1                # 容器内部连接
IBKR_PORT=4001                     # 实盘端口（模拟用 4002）
IBKR_USERNAME=your_ibkr_username   # Interactive Brokers 用户名
IBKR_PASSWORD=your_ibkr_password   # Interactive Brokers 密码
IBKR_2FA_DEVICE=Mobile Authenticator app  # 2FA 设备名称
IBKR_TOTP_SECRET=                  # TOTP 密钥（可选）- 用于自动 2FA 登陆
IBKR_TRADING_MODE=paper            # paper | live（影响 Gateway 启动）
```

**环境变量传递流程：**
```
.env: IBKR_TOTP_SECRET, IBKR_HOST, IBKR_PORT
  ↓
docker-compose.yml (trader + ib-gateway 服务, host network mode)
  ↓
trader 容器内
  ↓
vtlive/config.py: load_settings()
  ↓
Settings.ibkr_totp_secret, Settings.ibkr["host"], Settings.ibkr["port"]
  ↓
vtlive/brokers/__init__.py: make_broker()
  ↓
IBKRBroker(host=127.0.0.1, port=4001, totp_secret=...)
```

### 3. 核心实现

#### IBKRBroker 增强（`vtlive/brokers/ibkr.py`）

**新增属性：**
```python
self.totp_secret  # 从参数或环境变量读取
```

**新增方法：**
- `_generate_totp()` - 从密钥生成当前 TOTP 代码
- `_handle_2fa()` - 处理 2FA 挑战（备用方法）

**增强连接流程：**
```python
connect():
  1. 检查已连接 → 返回
  2. 创建 IB() 实例
  3. 若配置 TOTP_SECRET：
     - 生成 TOTP 代码
     - 注册错误事件处理器
     - 在检测到 "2FA" 挑战时自动发送代码
  4. 连接到 IBKR Gateway
  5. 自动检测账户（若未指定）
```

### 4. Docker 支持

**docker-compose.yml `ib-gateway` 服务：**
```yaml
environment:
  IBKR_TOTP_SECRET: ${IBKR_TOTP_SECRET:-}
  # 其他 2FA 相关配置已存在
```

## 使用指南

### 获取 TOTP 密钥

1. **启用 2FA（Authenticator App）**
   - 登录 Interactive Brokers 账户
   - Security → Two-Factor Authentication
   - 选择 Authenticator App（如 Google Authenticator, Microsoft Authenticator）
   - 扫描二维码或输入密钥
   - **记下设备名称**（如 "Mobile Authenticator app"）- 用于 `IBKR_2FA_DEVICE`

2. **保存密钥**
   - 记录 TOTP 密钥（通常是 32 个大写字母/数字）
   - **安全存储**（这是恢复码）

### 配置环境

**.env 文件配置：**
```bash
cp .env.example .env
# 编辑 .env

# IBKR Gateway 连接
IBKR_HOST=127.0.0.1                # localhost (容器内)
IBKR_PORT=4001                     # 实盘端口（模拟用 4002）
IBKR_CLIENT_ID=31
IBKR_ACCOUNT=                      # 可选：多账户时必填

# IBKR 凭证
IBKR_USERNAME=your_ibkr_username
IBKR_PASSWORD=your_ibkr_password

# 2FA 配置
IBKR_2FA_DEVICE=Mobile Authenticator app  # 如有多个2FA设备时指定
IBKR_TOTP_SECRET=YOUR_32_CHAR_TOTP_SECRET_HERE  # TOTP 密钥用于自动登陆
IBKR_TRADING_MODE=paper            # paper | live
```

**启动流程：**
```bash
# 1. 编辑 .env（见上面）
# 2. 构建镜像
./docker/ibkr.sh build

# 3. 启动（自动启动 IB Gateway + trader）
./docker/ibkr.sh start

# 4. 查看日志
./docker/ibkr.sh logs
```

### 验证配置

**连接检查（需要在 .env 文件配置完整后）：**
```bash
./docker/ibkr.sh check
```

**构建并启动：**
```bash
./docker/ibkr.sh build
./docker/ibkr.sh start
./docker/ibkr.sh logs
```

**预期日志输出：**
```
Connecting to IBKR host.docker.internal:4002 (client_id=31)
Generated TOTP code for 2FA
Connected to IBKR Gateway
Auto-detected account: U1234567
```

## 技术细节

### TOTP 生成原理

- **基于时间的 OTP**：使用 SHA-1 HMAC 和 30 秒时间窗口
- `pyotp.TOTP(secret).now()` 生成当前 6 位数字代码
- 每 30 秒刷新一次（与 Google Authenticator 同步）

### 2FA 事件处理

```python
# IB 连接时自动处理 2FA
if hasattr(self.ib, 'errorEvent'):
    self.ib.errorEvent += on_error  # 注册错误处理器
    
# 当错误消息包含 "2FA" 或 "code" 时：
if "2FA" in str(error):
    send TOTP code → self.ib.sendRawMessage(code.encode())
```

### 安全考虑

⚠️ **注意：**
- TOTP 密钥 = IBKR 账户的二次认证因素
- 不要在代码中硬编码或提交到 Git
- 使用环境变量或密钥管理系统
- Docker 容器应在安全网络环境运行

**建议做法：**
```bash
# 使用 .env（本地，不提交）
IBKR_TOTP_SECRET=ABCDEFGHIJKLMNOP...

# 或使用环境变量导入
export IBKR_TOTP_SECRET=<secret>
docker compose up -d trader
```

## 故障排除

### 问题 1：连接超时
```
BrokerError: cannot connect to IBKR at host.docker.internal:4002
```

**原因：** IB Gateway 未运行或地址不正确

**解决：**
```bash
# 检查 IB Gateway 状态（宿主机）
lsof -i :4001  # 实盘
lsof -i :4002  # 模拟

# 或启动容器版本
./docker/ibkr.sh gateway-start
docker compose ps  # 查看 ib-gateway 容器
```

### 问题 2：2FA 代码未发送
```
2FA challenge detected but TOTP not configured
```

**原因：** IBKR_TOTP_SECRET 为空或格式错误

**解决：**
```bash
# 验证 .env
grep IBKR_TOTP_SECRET .env

# 确认密钥是 32 个字符（Base32 编码）
# 如果从二维码扫描，确保完整性
```

### 问题 3：TOTP 代码无效
```
Received 2FA validation failure
```

**原因：** 
- 容器时钟与系统时钟不同步（时差 > 30 秒）
- TOTP 密钥输入错误

**解决：**
```bash
# 同步容器时间
docker exec xqqq-vt25-ibkr ntpdate -s time.nist.gov

# 或使用 systemd-timesyncd
timedatectl set-timezone America/New_York
```

## 测试清单

- [ ] `.env` 配置完整（IBKR_TOTP_SECRET, IBKR_HOST 等）
- [ ] `docker/ibkr.sh check` 通过
- [ ] 容器日志显示 "Connected to IBKR Gateway"
- [ ] 账户信息正确识别
- [ ] 可成功获取持仓和账户余额

## 参考文档

- [ib_async GitHub](https://github.com/ib-api-reloaded/ib_async)
- [pyotp 文档](https://github.com/pyca/pyotp)
- [gnzsnz ib-gateway-docker](https://github.com/gnzsnz/ib-gateway-docker)
- [IB API 配置指南](https://ibkrservices.com/downloads/GatewayInstall.pdf)

## 版本信息

- **ib_async**: ≥ 1.0
- **pyotp**: ≥ 2.8
- **Python**: 3.11+
- **集成日期**: 2026-10-04
