//整个函数是一个立即执行函数
//(function abx(){})();
(function flexible(window, document) {
    // 获取html
    var docEl = document.documentElement
        //获取设备像素比 pc端是1 移动端是2  这里用了逻辑中断 如果浏览器不是1 表示unfinded 那么dpr=1
        //window是浏览器窗口  window.devicePixelRatio如果没有定义 就给给他1
    var dpr = window.devicePixelRatio || 1

    // adjust body font size   修改body的文字大小
    function setBodyFontSize() {
        if (document.body) {
            document.body.style.fontSize = (12 * dpr) + 'px'
        } else {
            //DOMContentLoaded  dom加载完毕之后（无需等待图片、样式表）
            //这里用了一个递归 如果document.body没有加载完成 那么监听document 重新去给body的font设置大小
            document.addEventListener('DOMContentLoaded', setBodyFontSize)
        }
    }
    setBodyFontSize();

    // set 1rem = viewWidth / 10
    // 设置成24等份，设计稿时1920px的，这样1rem就是80px
    function setRemUnit() {
        // docEl是HTMLElement（HTMLElement 接口表示所有的 HTML 元素） 首先将clientWidth，即可视窗口分成10等分
        //clientWidth = 宽度+padding  offsetWidth =宽度+padding+border
        var rem = docEl.clientWidth / 10
            //改成像素
        docEl.style.fontSize = rem + 'px'
        docEl.setAttribute("dpr-data",dpr)
    }

    setRemUnit()

    // reset rem unit on page resize
    //监听窗口的尺寸大小的变化 如何发生变化 重新去获取rem
    window.addEventListener('resize', setRemUnit)
        //pageshow会在以下几种情况下触发：①a标签超链接 ②F5或者刷新按钮 ③前进或者后退
        //解决兼容性问题-火狐浏览器 其中，有一个‘往返缓存’,这里面不仅存放着页面，还有dom js，实际上就是将他们存放到内存中
        //我们点击后退按钮时，不会进行刷新，这时候可以通过触发pageshow来实现
        //pageshow会在页面显示时，触发，无论页面是否来自缓存，在重新加载页面中，pageshow会在load事件出发之后进行触发，根据事件对象persisted
        //来判断pageshow的触发是否来自缓存 e.persisted为true表示页面来自缓存，这时候就需要 重新计算rem
    window.addEventListener('pageshow', function(e) {
        if (e.persisted) {
            setRemUnit()
        }
    })

    // detect 0.5px supports 让代码支持0.5px
    if (dpr >= 2) {
        var fakeBody = document.createElement('body')
        var testElement = document.createElement('div')
        testElement.style.border = '.5px solid transparent'
        fakeBody.appendChild(testElement)
        docEl.appendChild(fakeBody)
        if (testElement.offsetHeight === 1) {
            docEl.classList.add('hairlines')
        }
        docEl.removeChild(fakeBody)
    }
}(window, document))
