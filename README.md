# mcp キャプチャツール

mcp server に渡される標準入出力をキャプチャするツールです。

## 使い方

config.json の MCP Server 呼び出しの前に挿入します。
以下の例では省略していますがフォルダやパスはフルパスで記載することをお勧めします。
必ず ``--quite`` オプションを指定してください。

```json
{
    "mcpServers":{
        "demo-app": {
            "command": "python",
            "args": [
                "command-capture.py",
                    "--quiet",
                    "--log-dir",
                        "logs",
                    "mcp",
                        "run",
                        "server.py"
            ]
        }
    }
}
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `--log-dir LOG_DIR` | Directory to store log files (default: "./logs") |
| `--quiet` | Suppress console output from the script itself |
| `COMMAND` | The command to execute (required) |
| `ARGS` | Arguments for the command (optional) |

