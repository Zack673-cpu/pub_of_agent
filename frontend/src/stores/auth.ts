import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
    // 三个状态，初始值都是空
    const accessToken = ref('')
    const refreshToken = ref('')
    const username = ref('')
    // 三个 action，只给签名和职责：
    // setToken  —— 登录/刷新成功后把新拿到的 token 存进来（参数就是后端返回的那两个字段）
    function setToken(newAccess: string, newRefresh: string) { 
        accessToken.value=newAccess
        refreshToken.value=newRefresh
    }

    // clearToken —— 退出登录时清空三样
    function clearToken() { 
        accessToken.value = ''
        refreshToken.value = ''
        username.value = ''
    }

    return { accessToken, refreshToken, username, setToken, clearToken }
})