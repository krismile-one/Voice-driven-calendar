# GitHub 两人协作指南

## 仓库地址
```
https://github.com/krismile-one/Voice-driven-calendar.git
```

## 1. 克隆仓库（每人只需执行一次）

```bash
git clone https://github.com/krismile-one/Voice-driven-calendar.git
cd Voice-driven-calendar
```

## 2. 日常工作流程

### 每次开始工作前：拉取最新代码
```bash
git pull origin main
```

### 创建自己的分支进行开发
```bash
# 创建并切换到新分支（用自己的名字命名）
git checkout -b dev/你的名字
这是一种常见的分支命名约定，用来区分不同用途的分支：

  - dev/名字 — 开发分支，按开发者区分，避免多人在同一个分支上冲突
  - feature/功能名 — 功能分支
  - bugfix/描述 — 修复分支
  - release/版本号 — 发布分支

```

### 提交代码
```bash
git add .
git commit -m "描述你做了什么"
```

### 推送你的分支到远程
```bash
git push origin dev/你的名字
```

### 合并到 main 分支
```bash
# 切换回 main
git checkout main

# 拉取最新代码（确保 main 是最新的）
git pull origin main

# 合并你的分支
git merge dev/你的名字

# 推送合并后的 main
git push origin main
```

## 3. 解决冲突

如果推送时提示冲突：

```bash
# 1. 先拉取最新代码
git pull origin main


当两个分支修改了同一个文件的同一区域，Git 无法自动判断保留哪个，就会报冲突。

  #冲突长什么样？

  Git 会在文件中用标记标出冲突区域：

  <<<<<<< HEAD
  你当前分支的内容
  =======
  要合并进来的分支的内容
  >>>>>>> 另一个分支

  解决步骤

  1. 手动编辑 — 打开冲突文件，删掉标记符号，保留你想要的内容
  2. git add <文件> — 标记冲突已解决
  3. git commit — 完成合并提交

  举个例子

  # main 分支写了：
  print("hello")

  # dev/xzh 分支同一行改成：
  print("hi")

  合并时 Git 不知道保留哪个，就产生冲突。你需要手动选择保留 hello 还是
  hi，或者两个都保留。

  核心原则

  - Git 只负责发现冲突，不负责决定保留哪个
  - 冲突解决是人工决策，Git 只是提供工具
  - 解决后记得 git add + git commit 才算完成

# 2. 打开冲突文件，手动修改冲突部分
#    冲突标记：<<<<<<< HEAD ... ======= ... >>>>>>> 分支名

# 3. 保存后提交
git add .
git commit -m "解决冲突"
git push origin main
```

## 4. 分支命名规范

| 分支名 | 用途 |
|--------|------|
| `main` | 主分支，保持稳定 |
| `dev/xzh` | xzh的开发分支 |
| `dev/xxx` | 另一个人的开发分支 |

## 5. 注意事项

- **提交前先 pull**：避免冲突
- **不要直接在 main 上开发**：用分支隔离工作
- **写清楚 commit 信息**：方便他人了解改动
- **及时合并**：不要长时间不同步

## 6. 常用命令速查

```bash
git status          # 查看当前状态
git log --oneline   # 查看提交历史
git branch          # 查看本地分支
git branch -a       # 查看所有分支（包括远程）
git diff            # 查看修改内容
```
