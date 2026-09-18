<template>
    <el-container class="layout">
        <el-aside width="90px" class="app-sidebar">
            <div class="brand">logo占位</div>
            <div class="new-button-div">
                <el-button type="primary" class="new-button" @click="handleNew">
                    <el-icon><Plus/></el-icon>
                    <span class="new-button-text">新写一本</span>
                </el-button>
            </div>            
            <el-menu
                :default-active="activeMenu"
                class="menu"
                @select="(index: string) => router.push(index)"
            >
                <el-menu-item index="/writing">写作</el-menu-item>
                <el-menu-item index="/history">历史记录</el-menu-item>

            </el-menu>
            <div class="logout-button-div">
                    <el-button text class="logout-button" @click="handleLogout">
                        <el-icon><SwitchButton/></el-icon>
                        <span class="logout-button-text">退出登录</span>
                    </el-button>
            </div>
        </el-aside>
        <el-main> 
            <router-view/> 
        </el-main>
    </el-container>



</template>


<script setup lang="ts">
    import { useRouter,useRoute } from 'vue-router'
    import { useAuthStore } from '@/stores/auth'
    import {Plus,SwitchButton } from '@element-plus/icons-vue'
    import { computed } from 'vue'
    const router=useRouter()
    const route=useRoute()
    const authstore=useAuthStore()

    const activeMenu=computed(()=>route.path)

    const handleLogout=()=>{
        authstore.clearToken()
        router.push({name: 'login'})
    }
    const handleNew=()=>{
        console.log("新开一本")
    }
</script>

<style scoped>
.layout{
    height: 100vh;
}
.app-sidebar{
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--el-border-color-light);
    width:clamp(200px, 18vw, 280px)
}
.brand{
    height: 56px;
    display: flex;
    align-items: center;
    padding:0 16px;
    font-weight: 600;
}
.new-button-div{
    padding: 12px 16px;
}
.new-button{
    width:100%
}

.menu{
    flex:1;
    border-right: None;
}


.logout-button-div{
    padding:12px 16px;
    border-top:1px solid var(--el-border-color-light)
}
.logout-button{
    width:100%
}

</style>