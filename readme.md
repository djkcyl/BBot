<div align="center">

# BBot for Ariadne

![!](https://count.getloli.com/get/@BBot-Graia?theme=rule34)

基于 [Graia-Ariadne](../../../../GraiaProject/Ariadne) 搭建的高效、高性能哔哩哔哩推送 [QQ](../../../../project-mirai/mirai-api-http) 机器人

```text
BBot
B，是 26 个英文字母里的第二个，可意为我个人的第二个机器人
B，也代表 BiliBili，这个 Bot 将专注于哔哩哔哩的推送等服务
```

</div>

## BBot 现在能干什么

- 订阅 UP 主 ~~废话~~
- 推送直播（开播及下播）~~废话~~
- 推送动态 ~~废话~~
- 视频链接解析

## 特色

- 大量使用并发 **gRPC 接口**，推送效率远超使用 REST Api 的哔哩哔哩机器人且目前未见有风控（-421）风险
- 使用登录和非登录两种方案，对于财大气粗的用户可以登录后再次提升效率
- 动态使用 Web 端截图，虽然会吃那么点性能，~~但这都是值得的~~
- 可自由配置是否在群内 @全体成员、对于直播和动态的分别控制等
- 可针对不同群聊对订阅的 UP 主进行昵称替换

## 注意

~~如果你想要使用 BBot，那么你需要准备一个 0 关注的哔哩哔哩小号。~~

（现在你什么都不需要注意了

## TODO

- [x] 增加群内配置功能
- [x] 增加菜单（/help 指令）
- [x] 使用数据库存储推送记录
- [x] 增加动态自动点赞功能
- [x] 支持 up 全名搜索
- [x] 增加可选的动态推送样式（App 样式）
- [x] 定时刷新 token，防止过期
- [x] 针对 Windows 和 Linux 平台，增加 Release 打包版本
- [x] 增加非登录式的推送更新逻辑
- [ ] 增加不需要浏览器的动态信息获取方式
- [ ] 增加简单的推送数据分析及报告
- [ ] 丰富管理员指令
- [ ] 增加订阅组（同时订阅多个设定好的 up，如 `和谐有爱五人组`...）
- [ ] 更换 BiliBili 请求库为~~更成熟~~的 [BiliReq](../../../../SK-415/bilireq)
- [ ] ~~可能会增加其他平台的推送~~

More...

## 感谢

- [HarukaBot](../../../../SK-415/HarukaBot) 学习对象
- [bilibili-API-collect](../../../../SocialSisterYi/bilibili-API-collect) 易姐收集的各种 BiliBili Api 及其提供的 gRPC Api 调用方案
- [ABot-Graia](../../../../djkcyl/ABot-Graia) 永远怀念最好的 ABot 🙏
