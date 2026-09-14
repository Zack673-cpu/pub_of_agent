<template>
    <el-form
        :model="form"
        label-width="80px"
        @submit.prevent="handleLogin"
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
            <el-button type="primary" @click="handleLogin">登录</el-button>
        </el-form-item>
            <!-- type="primary"表示这个按钮是主要按钮 -->
    </el-form>


</template>

<script setup lang="ts">
import {ref} from 'vue'
    const form =ref({'username':'','password':''})
    const handleLogin =()=>{
        console.log(form.value.username,form.value.password)
    }
</script>
