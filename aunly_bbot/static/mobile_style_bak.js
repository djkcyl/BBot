// 去除打开app按钮
function getNode(node) {
    node.childNodes.forEach((child) => {
        if (child.nodeName === "SCRIPT") return;
        if (!child.hasChildNodes()) {
            if (child.textContent.startsWith("打开APP")) {
                child.parentNode.parentNode.remove();
            }
            return;
        }
        getNode(child);
    });
};
getNode(document.body);
// 去除关注按钮
document.getElementsByClassName('dyn-header__following').forEach(v => v.remove());
// 修复字体与换行问题
const dyn = document.getElementsByClassName('dyn-card')[0];
dyn.style.fontFamily = 'Noto Sans CJK SC, sans-serif';
dyn.style.overflowWrap = 'break-word'