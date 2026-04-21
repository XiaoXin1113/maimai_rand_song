# maimai_rand_song 项目硬规则

> 这些规则为本项目的硬规则，务必遵守。只要用户没有特别提到某一次可以不遵守这些规则，就默认在每一轮对话中都存在这些规则。

## 规则列表

### 1. 代码变动同步规则
每当代码发生变动，必须执行以下同步操作：
- **上传至GitHub码仓**：使用 `git add`、`git commit`、`git push` 命令
- **上传至云服务器**：使用 scp 方式上传文件到 `ubuntu@119.45.34.254`

### 2. 服务重启规则
每当代码发生变化，按需重启变化端的服务：
- **QQ Bot**：如有变动，重启云服务器上的 bot 服务
- **Web**：如有变动，重启云服务器上的 web 服务

### 3. 云服务器进程启动规则
在云服务器启动进程时：
- 使用 `screen` 启动进程
- 启动后使用 `ctrl+a+d` 来 detach（因为某些进程没有输出，如果一直等输出的话会卡住）

### 4. 文件上传规则
将文件上传到服务器时：
- **必须使用 scp 方式**，不要从 github fetch
- 原因：服务器在中国，连接 github 很慢

### 5. 功能验证规则
更改代码后对于相关功能进行验证，如验证不成功则返回修改代码：
- **验证方法**：通过测试命令或功能操作进行验证
- **验证标准**：功能正常运行，无错误提示
- **失败处理**：如验证失败，立即回滚或修改代码直至验证成功

### 6. 服务器命令执行规则
在远端云服务器上运行指令时，不同的指令分开运行，不要使用分号或者&&这类的：
- **执行方式**：每次只执行一个命令
- **操作步骤**：完成一个命令后再执行下一个命令
- **避免使用**：分号(;)、&&、|| 等命令连接符

### 7. Screen 操作规则
在使用 screen 指令对某个 socket 里面的服务进行操作之前，务必先进行 screen -ls 检查是否存在该 screen：
- **操作前检查**：执行 `screen -ls` 确认目标 screen 是否存在
- **操作步骤**：先检查，再执行相应的 screen 命令
- **安全操作**：避免对不存在的 screen 执行操作

### 8. Screen 脱离规则
在使用 `screen -dmS xxx bash` 指令时，执行完指令后使用 ctrl+c 脱离 screen：
- **执行方式**：使用 `screen -dmS` 启动后台 screen 进程
- **脱离方法**：执行完指令后，使用 `Ctrl+C` 组合键脱离 screen
- **注意事项**：确保进程在后台正常运行

### 9. Debug和测试文件管理规则
运行debug和测试、创造临时文件时：
- **执行目录**：在 `debug` 目录下运行和创造文件
- **文件组织**：测试文件放在 `debug/tests` 目录，脚本放在 `debug/scripts` 目录
- **临时文件**：临时文件应放在 `debug` 目录下，避免污染项目根目录

## 服务器信息

- **SSH地址**：`ubuntu@119.45.34.254`
- **项目路径**：`~/maimai_rand_song`
- **服务端口**：
  - Web服务：8000
  - Bot服务：8080

## 服务管理命令

### 查看服务状态
```bash
ssh ubuntu@119.45.34.254 "screen -ls; ps aux | grep python | grep -v grep"
```

### 重启Web服务
```bash
ssh ubuntu@119.45.34.254 "screen -S web -X quit; screen -dmS web bash -c 'cd /home/ubuntu/maimai_rand_song && python3 -m web.backend.main 2>&1 | tee /tmp/web.log'"
```

### 重启Bot服务
```bash
ssh ubuntu@119.45.34.254 "cd ~/maimai_rand_song/bot && screen -dmS bot bash -c 'python3 main.py 2>&1 | tee /tmp/bot.log'"
```

### 查看服务日志
```bash
ssh ubuntu@119.45.34.254 "cat /tmp/web.log | tail -20"
ssh ubuntu@119.45.34.254 "cat /tmp/bot.log | tail -20"
```
