import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'
// 1. 创建实例：baseURL 指向后端根地址，设置一个合理的超时时间
const request = axios.create({
    baseURL: 'http://localhost:8000',
    timeout: 10000,
})

// 2. 请求拦截器：每次请求发出前，把 accessToken 塞进请求头
request.interceptors.request.use((config) => {
    const authStore = useAuthStore()  
    const access_token=authStore.accessToken
    if (access_token){
        config.headers.set("Authorization",`Bearer ${access_token}`)
    }
    
    return config
})

// 3. 响应拦截器：统一处理 401 → 自动刷新 → 重发原请求
request.interceptors.response.use(
    (response) => response,                    // 正常响应直接放行
    async (error) => {
        if (error.response === undefined){throw error}
        if (error.response.status !== 401){
            throw error
        }
        if (error.config._retry === true){
            router.push('/login')
            return
        }
        error.config._retry=true
        const authStore = useAuthStore()  
        try {
            const originalRequest = error.config 
            const res= await request.post('/refresh',{
                refresh_token:authStore.refreshToken
            })
            
            authStore.setToken(res.data.access_token,res.data.refresh_token)
            originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`
            return request(originalRequest)   
        } catch (error) {
            throw error
        }
        
        //调 /refresh 换新 token，
        // 更新 store，然后用新 token 重发 error.config，你写
        // 刷新失败就跳回登录页
        
        
    },
)

export default request