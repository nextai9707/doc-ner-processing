// https://unocss.dev/ 原子 css 库
import '@unocss/reset/tailwind-compat.css' // unocss reset
import 'virtual:uno.css'
import 'virtual:unocss-devtools'
// 你自定义的 css
import './styles/main.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// Element Plus 全局主题配置
import './styles/element-plus-theme.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
const app = createApp(App)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
	app.component(key, component)
}
app.use(ElementPlus)

app.mount('#app')
