/*
 * @Author: KBD
 * @Date: 2022-12-26 13:45:30
 * @LastEditors: KBD
 * @LastEditTime: 2022-12-26 14:49:43
 * @Description: 用于初始化手机动态页面的样式以及图片大小
 */
async function getMobileStyle() {
    // 删除关注dom
    const followDom = document.querySelector(".dyn-header__following");
    followDom && followDom.remove();

    // 删除分享dom
    const shareDom = document.querySelector(".dyn-share");
    shareDom && shareDom.remove();

    // 删除打开程序dom
    const openAppBtnDom = document.querySelector(".dynamic-float-btn");
    openAppBtnDom && openAppBtnDom.remove();

    // 设置字体格式
    const cardDom = document.querySelector(".dyn-card");
    if (cardDom) {
        cardDom.style.fontFamily = "Noto Sans CJK SC, sans-serif";
        cardDom.style.overflowWrap = "break-word";
    }

    // 找到图标容器dom
    const containerDom = document.querySelector(".bm-pics-block__container");
    if (containerDom) {
        // 先把默认padding-left置为0
        containerDom.style.paddingLeft = "0";
        // 先把默认padding-right置为0
        containerDom.style.paddingRight = "0";
        // 设置padding与单图片一致
        containerDom.style.padding = "0 3.2vmin";
        // 设置flex模式下以列形式排列
        containerDom.style.flexDirection = "column";
        // 设置flex模式下每个容器间隔15px
        containerDom.style.gap = "15px";
        // flex - 垂直居中
        containerDom.style.justifyContent = "center";
        // flex - 水平居中
        containerDom.style.alignItems = "center";
    }

    // 定义异步方法获取图片原尺寸(仅限于dom上的src路径的图片原尺寸)
    const getImageSize = (url) => {
        return new Promise((resolve, reject) => {
            const image = new Image();
            image.onload = () => {
                // 图片加载成功返回对象(包含长宽)
                resolve({
                    width: image.width, height: image.height,
                });
            };
            image.onerror = () => {
                reject(new Error("error"));
            };
            image.src = url;
        });
    };

    // 获取图片容器的所有dom
    const imageItemDoms = document.querySelectorAll(".bm-pics-block__item");

    // 异步遍历图片dom
    await Promise.all(Array.from(imageItemDoms).map(async (item) => {
        // 获取屏幕比例的90%宽度
        const clientWidth = window.innerWidth * 0.9;

        // 先把默认margin置为0
        item.style.margin = "0";
        // 宽度默认撑满屏幕宽度90%;
        item.style.width = `${clientWidth}px`;
        try {
            // 初始化url
            let imageTrueUrl;

            // 获取原app中图片的src
            const imgSrc = item.firstChild.src;
            // 判断是否有@符
            const imgSrcAtIndex = imgSrc.indexOf("@");

            // 将所有图片转换为.webp格式节省加载速度
            imageTrueUrl = imgSrcAtIndex !== -1 ? imgSrc.slice(0, imgSrcAtIndex + 1) + ".webp" : imgSrc;

            // 需要将真实的路径返回给image标签上(否则会失真)
            item.firstChild.src = imageTrueUrl;

            // 获取图片原尺寸对象
            const obj = await getImageSize(imageTrueUrl);
            // 图片大小判断逻辑部分(以屏幕宽度90%的1:1为基准)
            if (obj.width / obj.height !== 1) {
                item.style.height = `${(clientWidth / obj.width) * obj.height}px`;
            } else {
                item.style.height = "auto";
            }
        } catch (err) {
            item.style.height = "auto";
        }
    }))
}