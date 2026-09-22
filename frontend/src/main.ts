import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
// 分页、日期选择器显示中文
import App from './App.vue'
import router from './router'
import './styles/tokens.css'
const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
// 作用：给整个应用注册插件。
app.mount('#app')
// 作用：把应用渲染到页面上指定的 DOM 容器里。
// 就是D:\Learning\pub_of_agent\frontend\index.html替换这个原生的html