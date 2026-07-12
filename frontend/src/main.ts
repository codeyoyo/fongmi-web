import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createDiscreteApi } from 'naive-ui'

const app = createApp(App)
app.use(router)
app.mount('#app')

const { message } = createDiscreteApi(['message'])
window.$message = message
