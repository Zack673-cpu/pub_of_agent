<template>
    <el-form
        :model="form"
        label-width="80px"
        @submit.prevent="handleRegister"
    >
        <el-form-item label="用户名">
            <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                clearable
               
            />
            <!-- clearable一键清空功能 -->
        </el-form-item>
            

        <el-form-item label="密码">
           <el-input
                v-model="form.password"
                placeholder="请输入密码"
                clearable
                type="password"
                show-password
            />

        </el-form-item>

        <el-form-item>
            <el-button type="primary" @click="handleRegister">注册</el-button>
        </el-form-item>
        <el-form-item>
            <el-button type="primary" @click="goLogin">返回登录</el-button>
        </el-form-item>
            <!-- type="primary"表示这个按钮是主要按钮 -->
    </el-form>


</template>

<script setup lang="ts">
    import {ref} from 'vue'
    import request from '@/api/request'
    import { useAuthStore } from '@/stores/auth'
    import { ElMessage } from 'element-plus'
    import { useRouter } from 'vue-router'
    import axios from 'axios'  

    const router=useRouter()
    const form =ref({'username':'','password':''})
    const handleRegister = async ()=>{
        
        const store=useAuthStore()
        try{
            const response=await request.post('/register',form.value)
            const access_token=response.data.access_token
            const refresh_token=response.data.refresh_token
            store.setToken(access_token,refresh_token)
            store.setUsername(form.value.username)
            router.push('/writing')
        }catch (error){
            if(axios.isAxiosError(error)){
                if (error.response){
                    const detail=error.response.data.detail
                    ElMessage.error(detail||'请求失败，请稍后重试')
                }else{
                    ElMessage.error('登录失败，网络异常')
                }
            
            }else{
                const msg = error instanceof Error ? error.message : String(error)
                ElMessage.error(`未知错误：${msg}`)
            }

            
        }

        

    }
    const goLogin=()=>{
        router.push({name:'login'})
    }

</script>
