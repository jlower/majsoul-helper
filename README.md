# majsoul-helper

> ~~从 [majsoul-helper](https://github.com/lqgl/majsoul-helper) 改造而成的~~，更改了 ```requirements.txt``` 与 Akagi 的一样，并同步更改了bot中的文件适配，不用手动下载 libriichi 了，pip时自动到 [riichi](https://github.com/shinkuan/Akagi/releases/expanded_assets/v0.1.1-libriichi) 这里下载，添加了随机延迟和随机出牌
>
> **改用edge** 直接使用电脑**自带**的**不用再下载**chromium了

## 现有功能

- [x] 支持[Akagi](https://github.com/shinkuan/Akagi)
- [x] 自动打牌，自动随机出牌
- [ ] 自动连续打牌

## 欢迎 PR

## 用前须知

> _魔改千万条，安全第一条。_
>
> _使用不规范，账号两行泪。_
>
> _本插件仅供学习参考交流，_
>
> _请使用者于下载 24 小时内自行删除，不得用于商业用途，否则后果自负。_

## 支持平台

- 雀魂网页端

## 使用方法

需求 Python >= 3.10

同步仓库

```bash
git clone https://github.com/lqgl/majsoul-helper.git && cd majsoul-helper
```

配置国内镜像源（可选）

```bash
python -m pip config set global.index-url https://mirror.nju.edu.cn/pypi/web/simple
```

安装依赖

```bash
python pip install --upgrade pip
python pip install -r requirements.txt
```

> 不用 ```python playwright install chromium``` 自己改成**使用edge**的了

使用 Akagi

> 到 [Discord](https://discord.gg/Z2wjXUK8bN) 下载 Akagi 提供的 bot.zip。 注: 网盘中除 v2 版本均可用，任选一个下载。解压获取 **mortal.pth** 文件，放置到 bot 文件夹中。
>
> https://pan.baidu.com/s/1pENphNS2DPH9m5I0uJnShg?pwd=b9zq 提取码: b9zq
>
> https://cloud.189.cn/web/share?code=ZFFBFjZrqiyi 访问码: eku6
>
> 自己在百度网盘和天翼网盘上也存了，在 **Akagi_雀魂_BOT** 文件夹中
>
> 注: 3p 的 mortal.pth 文件需捐赠 Akagi 进行获取.

启动

```bash
python main.py
```

## 特别感谢

- [Akagi](https://github.com/shinkuan/Akagi)

## 交流群

[Discord](https://discord.gg/)
