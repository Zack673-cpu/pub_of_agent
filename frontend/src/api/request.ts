import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'
const request=axios.create({
    baseURL:"http://localhost:8000",
    timeout: 10000
})


request.interceptors.request.use((config)=>{
    const authstore=useAuthStore()
    const access_token=authstore.accessToken
    if(access_token){
        config.headers.set("Authorization",`Bearer ${access_token}`) 
    }
    return config

})



request.interceptors.response.use(
    (response)=>response,
    async (error)=>{
        if (error.response === undefined){
            throw error
        }
        if(error.response.status !==401){
            throw error
        }
        if (error.config._retry===true){
            router.push('/login')
            throw error
        }
        if (error.config?.url?.includes('/refresh')){
            router.push('/login')
            throw error
        }
        error.config._retry=true
        const authstore=useAuthStore()
        const refresh_token=authstore.refreshToken
        const originalRequest=error.config
        try {
            
            const response=await request.post('/refresh',{
                refresh_token:refresh_token
            })
            const newAccess=response.data.access_token
            const newRefresh=response.data.refresh_token
            authstore.setToken(newAccess,newRefresh)
            return request(originalRequest)
            //这里重发也会走请求拦截器，那里加新token就好了
        } catch (error) {
            throw error
        }
        
        

    },

)

export default request