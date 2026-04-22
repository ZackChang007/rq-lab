# RQSDK 使用手册

> 米筐量化工具套件总入口

## 一、系统要求

### Python 版本支持矩阵

| 系统 | Python 3.7 | Python 3.8 | Python 3.9 | Python 3.10 | Python 3.11 | Python 3.12 | Python 3.13 |
|------|-----------|-----------|-----------|-------------|-------------|-------------|-------------|
| Linux | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Windows | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Mac(Apple Silicon) | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Mac(Intel) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |

**要求**: 64-bit, Python 3.6+ 运行环境，需商业授权

---

## 二、安装步骤

### 2.1 安装 Ricequant SDK

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple rqsdk
```

安装成功后输入 `rqsdk` 命令会显示帮助信息。

### 2.2 配置代理（可选）

```bash
rqsdk proxy
rqsdk proxy info  # 查看配置信息
```

### 2.3 配置许可证

```bash
rqsdk license      # 交互式配置
rqsdk license info # 查看许可证信息
```

许可证格式示例（类似乱码的字符串）。

### 2.4 安装产品组件

| 安装代码 | 产品名 | 用途及依赖 |
|---------|--------|-----------|
| rqdatac | RQData | 金融数据 API，**默认已安装** |
| rqoptimizer | RQOptimizer | 股票优化器，依赖 rqdatac |
| rqfactor | RQFactor | 因子投研工具，依赖 rqdatac |
| rqalpha_plus | RQAlpha Plus | 回测引擎，依赖 rqoptimizer 及 rqfactor |

```bash
rqsdk install <安装代码>
# 例如：rqsdk install rqalpha_plus
```

### 2.5 更新版本

```bash
rqsdk update
```

---

## 三、回测准备

### 3.1 准备历史数据

**试用客户专用命令**:
```bash
rqsdk download-data --sample
```

**生产环境命令**:
```bash
rqsdk update-data --base --minbar 000001.XSHE
```

数据缓存位置: `<用户目录>\.rqalpha-plus\bundle`

### 3.2 生成策略样例

```bash
rqalpha-plus examples
```

---

## 四、策略代码示例

### buy_and_hold.py 策略

```python
from rqalpha.api import *

def init(context):
    context.s1 = "000001.XSHE"
    update_universe(context.s1)
    context.fired = False
    logger.info("RunInfo: {}".format(context.run_info))

def before_trading(context):
    pass

def handle_bar(context, bar_dict):
    if not context.fired:
        logger.info("order_percent:{}".format(order_percent(context.s1, 1)))
        context.fired = True

def after_trading(context):
    pass
```

---

## 五、运行回测

```bash
rqalpha-plus run -f examples/buy_and_hold.py -s 2018-01-01 -e 2018-12-31 -fq 1m --plot --account stock 100000
```

**参数说明**:
- `-f`: 策略文件路径
- `-s`: 起始日期
- `-e`: 结束日期
- `-fq`: 频率 (1m=分钟线)
- `--plot`: 显示结果图表
- `--account`: 账户类型和资金

---

## 六、Anaconda 环境配置

### 下载 Miniconda
- 国内镜像: [清华大学 Miniconda 镜像](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/)
- 官方: [Miniconda 官网](https://docs.conda.io/en/latest/miniconda.html)

### Conda 基本操作

```bash
conda --version                    # 查看版本
conda update conda                 # 更新 conda
conda create -n rqsdk python=3.9   # 创建虚拟环境
conda activate rqsdk               # 激活环境
conda env list                     # 列出环境
conda deactivate                   # 退出环境
conda remove --name rqsdk --all    # 删除环境
```

### 配置国内镜像加速

```bash
conda activate base
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 七、IDE 配置

### PyCharm 运行回测配置

1. 点击 `Add Configuration`
2. 将 `Script path` 改为 `Module name`
3. 设置 `Module name` 为 `rqalpha_plus`
4. 设置 `Parameters`:
```
run -f buy_and_hold.py -s 20190101 -e 20191231 -a stock 20000 --plot
```

### VS Code launch.json 配置

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: 模块",
      "type": "python",
      "request": "launch",
      "module": "rqalpha-plus",
      "args": [
        "run", "-f", "examples\\buy_and_hold.py",
        "-s", "2018-01-01", "-e", "2018-05-31",
        "-fq", "1m", "--plot",
        "--account", "stock", "1000000"
      ]
    }
  ]
}
```

---

## 八、AI 编程工具配置

### Claude Code
创建 `.claude\commands\ricequant-doc-index.md` 文件，复制文档索引内容。

### Cursor
在 User Rules 中添加:
```
检查项目根目录下是否有 CLAUDE.md 文件，如果有则先阅读其内容作为开发指引。
```

### VS Code + Copilot
创建 `.github/copilot-instructions.md` 和 `.vscode/snippets.code-snippets` 文件。

### Cline
创建 `docs/document_index.md` 和 `docs/index_guide.md` 文件，以及 `.cline/system_prompt.md` 文件。

### Trae
创建智能体 "RicequantSDK"，配置提示词和调用条件。

---

## 九、文档链接

| 产品 | 资源 |
|------|------|
| RQData - 金融数据 API | [使用说明](/doc/rqdata/python/index-rqdatac) |
| RQAlpha Plus - 策略回测引擎 | [使用教程](/doc/rqalpha-plus/doc/index-rqalphaplus) |
| RQFactor - 因子编写及检验 | [使用教程](/doc/rqfactor/manual/index-rqfactor) |
| RQOptimizer - 股票多因子优化器 | [使用说明](/doc/rqoptimize/doc/index-rqoptimize) |
| 文档索引 | https://www.ricequant.com/doc/document-index.txt |

---

## 十、关键命令速查

```bash
# 安装
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple rqsdk

# 试用数据
rqsdk download-data --sample

# 生产数据
rqsdk update-data --minbar 000001.XSHE

# 生成样例
rqalpha-plus examples

# 运行回测
rqalpha-plus run -f examples/buy_and_hold.py -s 2018-01-01 -e 2018-12-31 -fq 1m --plot --account stock 100000
```
