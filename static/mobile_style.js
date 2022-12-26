/*
 * @Author: KBD
 * @Date: 2022-12-26 13:45:30
 * @LastEditors: KBD
 * @LastEditTime: 2022-12-26 14:06:05
 * @Description: 用于初始化手机动态页面的样式以及图片大小
 */
// 检测当前环境是否能使用箭头函数
const testFunction = "var t = () => {};";
try {
    test = new Function(testFunction);                    // 检验是否支持es6
    /*
     * @description: es6语法初始化手机样式
     * @return {*}
    */
    (() => {
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
        cardDom.style.fontFamily = "Noto Sans CJK SC, sans-serif";
        cardDom.style.overflowWrap = "break-word";

        // 找到图标容器dom
        const containerDom = document.querySelector(".bm-pics-block__container");
        containerDom.style.paddingLeft = "0";               // 先把默认padding-left置为0
        containerDom.style.paddingRight = "0";              // 先把默认padding-right置为0
        containerDom.style.padding = "0 3.2vmin";           // 设置padding与单图片一致
        containerDom.style.flexDirection = "column";        // 设置flex模式下以列形式排列
        containerDom.style.gap = "15px";                    // 设置flex模式下每个容器间隔15px
        containerDom.style.justifyContent = "center";       // flex - 垂直居中
        containerDom.style.alignItems = "center";           // flex - 水平居中

        // 定义异步方法获取图片原尺寸(仅限于dom上的src路径的图片原尺寸)
        const getImageSize = async (url) => {
            return new Promise((resolve, reject) => {
                const image = new Image();
                image.onload = () => {
                    // 图片加载成功返回对象(包含长宽)
                    resolve({
                        width: image.width,
                        height: image.height,
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

        // 异步遍历dom进行设置
        imageItemDoms.forEach(async (item) => {
            item.style.margin = "0";                          // 先把默认margin置为0
            item.style.width = "360px";                       // 宽度默认撑满360px;
            try {
                // 获取图片的真实路径(并判断是否有@);
                const imgSrc = item.firstChild.src;             // 获取原app中图片的src
                const imgSrcAtIndex = imgSrc.indexOf("@");      // 判断是否有@符
                const imageTrueUrl =
                    imgSrcAtIndex !== -1 ? imgSrc.slice(0, imgSrcAtIndex) : imgSrc;
                item.firstChild.src = imageTrueUrl;             // 需要将真实的路径返回给image标签上(否则会失真)

                // 获取图片原尺寸对象
                const obj = await getImageSize(imageTrueUrl);
                // 图片大小判断逻辑部分(以长宽360px的1:1为基准)
                if (obj.width / obj.height !== 1) {
                    item.style.height = `${(360 / obj.width) * obj.height}px`;
                } else {
                    item.style.height = "auto";
                }
            } catch (err) {
                item.style.height = "auto";
            }
        });
    })();
} catch (e) {
    /*
     * @description: 初始化手机样式, 理论用不到, 现在浏览器应该都支持上面的方法
     * @return {*}
    */
    (function initMobileStyle() {
        // 删除关注dom
        const followDom = document.getElementsByClassName("dyn-header__following")[0];
        if (followDom) {
            followDom.remove();
        }

        // 删除分享dom
        const shareDom = document.getElementsByClassName("dyn-share")[0];
        if (shareDom) {
            shareDom.remove();
        }

        // 删除打开程序dom
        const openAppBtnDom = document.getElementsByClassName("dynamic-float-btn")[0];
        if (openAppBtnDom) {
            openAppBtnDom.remove();
        }

        // 设置字体格式
        const cardDom = document.getElementsByClassName("dyn-card")[0];
        cardDom.style.fontFamily = "Noto Sans CJK SC, sans-serif";
        cardDom.style.overflowWrap = "break-word";

        // 找到图标容器dom
        const containerDom = document.getElementsByClassName("bm-pics-block__container")[0];
        containerDom.style.paddingLeft = "0";               // 先把默认padding-left置为0
        containerDom.style.paddingRight = "0";              // 先把默认padding-right置为0
        containerDom.style.padding = "0 3.2vmin";           // 设置padding与单图片一致
        containerDom.style.flexDirection = "column";        // 设置flex模式下以列形式排列
        containerDom.style.gap = "15px";                    // 设置flex模式下每个容器间隔15px
        containerDom.style.justifyContent = "center";       // flex - 垂直居中
        containerDom.style.alignItems = "center";           // flex - 水平居中

        // 定义方法获取图片原尺寸(仅限于dom上的src路径的图片原尺寸)
        function getImageSize(url) {
            return new Promise(function (resolve, reject) {
                const image = new Image();
                image.onload = function () {
                    // 图片加载成功返回对象(包含长宽)
                    resolve({
                        width: image.width,
                        height: image.height,
                    });
                };
                image.onerror = function () {
                    reject(new Error("error"));
                };
                image.src = url;
            })
        }

        // 获取图片容器的所有dom
        const imageItemDoms = document.getElementsByClassName("bm-pics-block__item");

        // 遍历dom进行设置
        imageItemDoms.forEach(function (item) {
            item.style.margin = "0";                          // 先把默认margin置为0
            item.style.width = "360px";                       // 宽度默认撑满360px;
            try {
                // 获取图片的真实路径(并判断是否有@);
                const imgSrc = item.firstChild.src;             // 获取原app中图片的src
                const imgSrcAtIndex = imgSrc.indexOf("@");      // 判断是否有@符
                const imageTrueUrl =
                    imgSrcAtIndex !== -1 ? imgSrc.slice(0, imgSrcAtIndex) : imgSrc;
                item.firstChild.src = imageTrueUrl;             // 需要将真实的路径返回给image标签上(否则会失真)

                // 获取图片原尺寸对象
                getImageSize(imageTrueUrl).then(function (obj) {
                    // 图片大小判断逻辑部分(以长宽360px的1:1为基准)
                    if (obj.width / obj.height !== 1) {
                        const height = 360 / obj.width * obj.height;
                        item.style.height = height + "px";
                    } else {
                        item.style.height = "auto";
                    }
                });
            } catch (err) {
                item.style.height = "auto";
            }
        });
    })();
}