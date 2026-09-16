import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import { useAuthStore } from '@/stores/auth.ts'
import Writing from '../views/Writing.vue'
import RegisterView from '@/views/RegisterView.vue'
const router = createRouter({
	history: createWebHistory(import.meta.env.BASE_URL),
	routes: [
		{ path: '/login', component: LoginView ,name:'login'},
		{ path: '/writing', component: Writing , meta:{requiresAuth:true}},
		{ path:	'/register',component: RegisterView,name:'register'},
	],
})

//目标页面该不该登录
//登录了没有
router.beforeEach((to,from)=>{
	const authstore=useAuthStore()
	if(to.meta?.requiresAuth){
		
		if(authstore.accessToken){
			return true
		}
		return '/login'
	}	
	if (authstore.accessToken && to.path ==='/login'){
		return '/writing'
	}
	return true
})

export default router
