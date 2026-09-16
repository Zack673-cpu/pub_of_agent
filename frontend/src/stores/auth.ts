import { defineStore } from "pinia"
import { ref } from "vue"




export const useAuthStore= defineStore('auth',()=>{
    const accessToken=ref(localStorage.getItem('ACCESS_KEY')?? '')
    const refreshToken=ref(localStorage.getItem('REFRESH_KEY')?? '')
    const username=ref(localStorage.getItem('UNAME_KEY')?? '')
    function setUsername(name: string) {
        username.value = name
        localStorage.setItem('UNAME_KEY',name)
    }   
    function setToken(newAccess:string,newRefresh:string){
        accessToken.value=newAccess
        refreshToken.value=newRefresh
        localStorage.setItem('ACCESS_KEY',newAccess)
        localStorage.setItem('REFRESH_KEY',newRefresh)
    }

    function clearToken(){
        accessToken.value=''
        refreshToken.value=''
        username.value=''
        //清理内存和磁盘的登录状态
        localStorage.removeItem('ACCESS_KEY')
        localStorage.removeItem('REFRESH_KEY')
        localStorage.removeItem('UNAME_KEY')

    }

    return {accessToken,refreshToken,username,setToken,clearToken,setUsername}
})