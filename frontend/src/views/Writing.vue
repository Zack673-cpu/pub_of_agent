<template>
    <el-form
        :model="form"
        ref="formRef"
        :rules="rules"
    >
        <el-form-item prop="name">
            <el-input 
                placeholder="书名" 
                clearable 
                v-model="form.name"
            />
        </el-form-item>

        <el-form-item prop="requirement">
            <el-input 
                placeholder="大致要求" 
                clearable
                v-model="form.requirement" 
                type="textarea"
            />

        </el-form-item>

        <el-form-item>
            <el-button type="primary" @click="handleCreate">
                开始生成大纲
            </el-button>



        </el-form-item>

    </el-form>
</template>



<script setup lang="ts">
    import type{ FormInstance } from 'element-plus'
    import { ref } from 'vue'
    const form =ref({name:'',requirement:''})
    const rules={
        name:[{required:true,message:'书名不能为空',trigger:'blur'}],
        requirement:[]
    }
    const formRef=ref<FormInstance>()
    const handleCreate=async ()=>{
        if (!formRef.value) return
        const res=await formRef.value.validate()
    }



</script>













