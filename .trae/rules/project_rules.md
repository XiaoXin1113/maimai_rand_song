# maimai_rand_song 项目硬规则

> 这些规则为本项目的硬规则，务必遵守。只要用户没有特别提到某一次可以不遵守这些规则，就默认在每一轮对话中都存在这些规则。

## 规则列表

### 1. 代码变动同步规则
每当代码发生变动，必须执行以下同步操作：
- **上传至GitHub码仓**：使用 `git add`、`git commit`、`git push` 命令
- **上传至云服务器**：使用 scp 方式上传文件到 `ubuntu@119.45.34.254`

### 2. 服务重启规则
每当代码发生变化，按需重启变化端的服务：
- **Windows Software**：如有变动，提示用户手动重启
- **Android Software**：如有变动，提示用户重新编译
- **QQ Bot**：如有变动，重启云服务器上的 bot 服务
- **Web**：如有变动，重启云服务器上的 web 服务

### 3. 云服务器进程启动规则
在云服务器启动进程时：
- 使用 `screen` 启动进程
- 启动后使用 `ctrl+a+d` 来 detach（因为某些进程没有输出，如果一直等输出的话会卡住）
- 示例命令：
  ```bash
  screen -dmS service_name bash -c 'cd /path/to/project && python3 main.py 2>&1 | tee /tmp/service.log'
  ```

### 4. 文件上传规则
将文件上传到服务器时：
- **必须使用 scp 方式**，不要从 github fetch
- 原因：服务器在中国，连接 github 很慢
- 示例命令：
  ```bash
  scp local_file.py ubuntu@119.45.34.254:~/maimai_rand_song/path/to/
  ```

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
