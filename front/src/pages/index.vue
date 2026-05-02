<template>
	<!-- 页面标题 -->
	<div class="page-header">
		<h1>文档处理系统</h1>
		<p>智能文档分析与处理平台</p>
	</div>

	<!-- 数据统计卡片 -->
	<el-row :gutter="20" class="metrics-section">
		<el-col :span="6">
			<el-card class="metric-card">
				<div class="metric-icon total-documents">
					<el-icon><Document /></el-icon>
				</div>
				<div class="metric-content">
					<h3>文档总数</h3>
					<div class="metric-value">{{ stats.totalDocuments }}</div>
				</div>
			</el-card>
		</el-col>
		<el-col :span="6">
			<el-card class="metric-card">
				<div class="metric-icon total-tasks">
					<el-icon><Operation /></el-icon>
				</div>
				<div class="metric-content">
					<h3>处理任务</h3>
					<div class="metric-value">{{ stats.totalTasks }}</div>
				</div>
			</el-card>
		</el-col>
		<el-col :span="6">
			<el-card class="metric-card">
				<div class="metric-icon total-processed">
					<el-icon><Finished /></el-icon>
				</div>
				<div class="metric-content">
					<h3>已处理文档</h3>
					<div class="metric-value">{{ stats.processedDocuments }}</div>
				</div>
			</el-card>
		</el-col>
		<el-col :span="6">
			<el-card class="metric-card">
				<div class="metric-icon total-size">
					<el-icon><FolderOpened /></el-icon>
				</div>
				<div class="metric-content">
					<h3>总存储量</h3>
					<div class="metric-value">{{ formatFileSize(stats.totalSize) }}</div>
				</div>
			</el-card>
		</el-col>
	</el-row>

	<!-- 快速导航 -->
<!--	<el-row :gutter="20" class="quick-nav-section">-->
<!--		<el-col :span="24">-->
<!--			<el-card class="nav-card">-->
<!--				<template #header>-->
<!--					<div class="nav-header">-->
<!--						<h3>快速导航</h3>-->
<!--					</div>-->
<!--				</template>-->
<!--				<div class="nav-grid">-->
<!--					<div class="nav-item" @click="router.push('/document-import')">-->
<!--						<div class="nav-icon upload-icon">-->
<!--							<el-icon><Upload /></el-icon>-->
<!--						</div>-->
<!--						<div class="nav-content">-->
<!--							<h4>文档导入</h4>-->
<!--							<p>上传并解析文档</p>-->
<!--						</div>-->
<!--					</div>-->
<!--					<div class="nav-item" @click="router.push('/text-preprocess')">-->
<!--						<div class="nav-icon preprocess-icon">-->
<!--							<el-icon><Edit /></el-icon>-->
<!--						</div>-->
<!--						<div class="nav-content">-->
<!--							<h4>文本预处理</h4>-->
<!--							<p>分词、清洗、标注</p>-->
<!--						</div>-->
<!--					</div>-->
<!--					<div class="nav-item" @click="router.push('/information-extraction')">-->
<!--						<div class="nav-icon extract-icon">-->
<!--							<el-icon><Search /></el-icon>-->
<!--						</div>-->
<!--						<div class="nav-content">-->
<!--							<h4>信息抽取</h4>-->
<!--							<p>规则与算法抽取</p>-->
<!--						</div>-->
<!--					</div>-->
<!--					<div class="nav-item" @click="router.push('/keyword-summary')">-->
<!--						<div class="nav-icon keyword-icon">-->
<!--							<el-icon><Key /></el-icon>-->
<!--						</div>-->
<!--						<div class="nav-content">-->
<!--							<h4>关键词摘要</h4>-->
<!--							<p>自动生成关键词和摘要</p>-->
<!--						</div>-->
<!--					</div>-->
<!--					<div class="nav-item" @click="router.push('/result-display')">-->
<!--						<div class="nav-icon result-icon">-->
<!--							<el-icon><DataLine /></el-icon>-->
<!--						</div>-->
<!--						<div class="nav-content">-->
<!--							<h4>结果导出</h4>-->
<!--							<p>查看并导出结果</p>-->
<!--						</div>-->
<!--					</div>-->
<!--				</div>-->
<!--			</el-card>-->
<!--		</el-col>-->
<!--	</el-row>-->

	<!-- 最近处理的文档 -->
	<el-row :gutter="20" class="charts-section">
		<el-col :span="12">
			<el-card class="chart-card">
				<template #header>
					<div class="card-header">
						<span class="card-title">📄 最近上传的文档</span>
					</div>
				</template>
				<div class="recent-list">
					<div class="recent-item" v-for="(item, idx) in recentDocuments" :key="item.id">
						<div class="recent-icon">
							<el-icon v-if="item.file_type === 'pdf'"><Document /></el-icon>
							<el-icon v-else-if="item.file_type === 'docx'"><Document /></el-icon>
							<el-icon v-else><Document /></el-icon>
						</div>
						<div class="recent-content">
							<div class="recent-title">{{ item.original_filename || '未知文件' }}</div>
							<div class="recent-meta">
								<span class="recent-type">{{ item.file_type.toUpperCase() }}</span>
								<span class="recent-size">{{ formatFileSize(item.file_size) }}</span>
								<span class="recent-time">{{ formatTime(item.created_at) }}</span>
							</div>
						</div>
						<div class="recent-status" :class="getStatusClass(item.status)">
							{{ getStatusText(item.status) }}
						</div>
					</div>
					<div v-if="recentDocuments.length === 0" class="empty-state">暂无文档</div>
				</div>
			</el-card>
		</el-col>
		<el-col :span="12">
			<el-card class="chart-card" style="height: 100%">
				<template #header>
					<div class="card-header">
						<span class="card-title">📊 处理任务统计</span>
					</div>
				</template>
				<div ref="taskChart" style="width: 100%;height: 350px"></div>
			</el-card>
		</el-col>
	</el-row>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { Document, Operation, Finished, FolderOpened, Upload, Edit, Search, Key, DataLine } from '@element-plus/icons-vue'
import { adminRequest } from '@/composables/adminRequest'

const router = useRouter()

// 统计数据
const stats = reactive({
	totalDocuments: 0,
	totalTasks: 0,
	processedDocuments: 0,
	totalSize: 0
})

// 最近文档列表
const recentDocuments = ref<any[]>([])
// 任务统计图表
const taskChart = ref<HTMLElement>()

// 格式化文件大小
const formatFileSize = (bytes: number | null | undefined): string => {
	if (!bytes) return '0 B'
	const k = 1024
	const sizes = ['B', 'KB', 'MB', 'GB']
	const i = Math.floor(Math.log(bytes) / Math.log(k))
	return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

// 格式化时间
const formatTime = (time: string | null | undefined): string => {
	if (!time) return ''
	const date = new Date(time)
	const now = new Date()
	const diff = now.getTime() - date.getTime()
	const minutes = Math.floor(diff / 60000)
	if (minutes < 1) return '刚刚'
	if (minutes < 60) return `${minutes}分钟前`
	const hours = Math.floor(minutes / 60)
	if (hours < 24) return `${hours}小时前`
	const days = Math.floor(hours / 24)
	if (days < 7) return `${days}天前`
	return date.toLocaleDateString()
}

// 获取状态文本
const getStatusText = (status: string): string => {
	const statusMap: Record<string, string> = {
		'uploaded': '已上传',
		'parsed': '已解析',
		'processed': '已处理',
		'error': '处理失败'
	}
	return statusMap[status] || status
}

// 获取状态样式类
const getStatusClass = (status: string): string => {
	const classMap: Record<string, string> = {
		'uploaded': 'status-uploaded',
		'parsed': 'status-parsed',
		'processed': 'status-processed',
		'error': 'status-error'
	}
	return classMap[status] || ''
}

// 获取统计数据
const fetchStats = async () => {
	try {
		const res: any = await adminRequest.get('/api/document/stats')
		if (res?.data) {
			stats.totalDocuments = res.data.total_documents || 0
			stats.totalTasks = res.data.total_tasks || 0
			stats.processedDocuments = res.data.processed_documents || 0
			stats.totalSize = res.data.total_size || 0
		}
	} catch (e) {
		console.error('获取统计数据失败:', e)
	}
}

// 获取最近文档
const fetchRecentDocuments = async () => {
	try {
		const res: any = await adminRequest.get('/api/document/recent?limit=5')
		recentDocuments.value = Array.isArray(res?.data) ? res.data : (res?.data ? [res.data] : [])
	} catch (e) {
		console.error('获取最近文档失败:', e)
	}
}

// 获取任务统计并渲染图表
const fetchTaskStats = async () => {
	try {
		const res: any = await adminRequest.get('/api/task/stats')
		if (res?.data && taskChart.value) {
			renderTaskChart(res.data)
		}
	} catch (e) {
		console.error('获取任务统计失败:', e)
	}
}

// 渲染任务统计图表
const renderTaskChart = (data: any) => {
	if (!taskChart.value) return
	const chart = echarts.init(taskChart.value)

	const taskTypes = data.task_types || []
	const taskCounts = data.task_counts || []

	chart.setOption({
		tooltip: {
			trigger: 'axis',
			axisPointer: {
				type: 'shadow'
			}
		},
		grid: {
			left: '3%',
			right: '4%',
			bottom: '3%',
			containLabel: true
		},
		xAxis: {
			type: 'category',
			data: taskTypes,
			axisTick: {
				alignWithLabel: true
			}
		},
		yAxis: {
			type: 'value'
		},
		series: [{
			name: '任务数量',
			type: 'bar',
			barWidth: '60%',
			data: taskCounts,
			itemStyle: {
				color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
					{ offset: 0, color: '#83bff6' },
					{ offset: 0.5, color: '#188df0' },
					{ offset: 1, color: '#188df0' }
				])
			}
		}]
	})
	window.addEventListener('resize', () => chart.resize())
}

// 初始化
onMounted(() => {
	fetchStats()
	fetchRecentDocuments()
	nextTick(() => {
		fetchTaskStats()
	})
})
</script>

<style scoped>
.dashboard-container {
	padding: 20px;
	background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
	min-height: 100vh;
}


.page-header h1 {
	color: #2c3e50;
	margin-bottom: 10px;
	font-size: 32px;
	font-weight: bold;
}

.page-header p {
	color: #7f8c8d;
	font-size: 16px;
}

.quick-nav-section {
	margin-bottom: 30px;
}

.nav-card {
	border-radius: 12px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
	border: none;
}

.nav-header {
	margin-bottom: 20px;
}

.nav-header h3 {
	margin: 0;
	color: #2c3e50;
	font-size: 20px;
	font-weight: 600;
}

.nav-grid {
	display: grid;
	grid-template-columns: repeat(5, 1fr);
	gap: 20px;
}

@media (max-width: 1400px) {
	.nav-grid {
		grid-template-columns: repeat(4, 1fr);
	}
}

@media (max-width: 1100px) {
	.nav-grid {
		grid-template-columns: repeat(3, 1fr);
	}
}

@media (max-width: 800px) {
	.nav-grid {
		grid-template-columns: repeat(2, 1fr);
	}
}

@media (max-width: 560px) {
	.nav-grid {
		grid-template-columns: 1fr;
	}
}

.nav-item {
	display: flex;
	align-items: center;
	gap: 15px;
	padding: 20px;
	background: white;
	border-radius: 12px;
	cursor: pointer;
	transition: all 0.3s ease;
	border: 2px solid transparent;
}

.nav-item:hover {
	transform: translateY(-5px);
	box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
	border-color: #4caf50;
}

.nav-icon {
	width: 50px;
	height: 50px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 20px;
	color: white;
}

.crop-icon {
	background: linear-gradient(135deg, #4caf50, #2e7d32);
}

.region-icon {
	background: linear-gradient(135deg, #2196f3, #1565c0);
}

.soil-icon {
	background: linear-gradient(135deg, #ff9800, #f57c00);
}

.yield-icon {
	background: linear-gradient(135deg, #f44336, #d32f2f);
}

.trend-icon {
	background: linear-gradient(135deg, #9c27b0, #7b1fa2);
}

.climate-icon {
	background: linear-gradient(135deg, #00bcd4, #0097a7);
}

.growth-icon {
	background: linear-gradient(135deg, #8bc34a, #689f38);
}

.nav-content h4 {
	margin: 0 0 5px 0;
	color: #2c3e50;
	font-size: 16px;
	font-weight: 600;
}

.nav-content p {
	margin: 0;
	color: #7f8c8d;
	font-size: 14px;
}

.metric-icon {
	width: 50px;
	height: 50px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24px;
	color: white;
}

.total-documents {
	background: linear-gradient(135deg, #3498db, #2980b9);
}

.total-tasks {
	background: linear-gradient(135deg, #4caf50, #2e7d32);
}

.total-processed {
	background: linear-gradient(135deg, #ff9800, #f57c00);
}

.total-size {
	background: linear-gradient(135deg, #9c27b0, #7b1fa2);
}

.upload-icon {
	background: linear-gradient(135deg, #3498db, #2980b9);
}

.preprocess-icon {
	background: linear-gradient(135deg, #4caf50, #2e7d32);
}

.extract-icon {
	background: linear-gradient(135deg, #ff9800, #f57c00);
}

.keyword-icon {
	background: linear-gradient(135deg, #9c27b0, #7b1fa2);
}

.result-icon {
	background: linear-gradient(135deg, #00bcd4, #0097a7);
}

.metric-value {
	font-size: 24px;
	font-weight: bold;
	color: #2c3e50;
}

.metrics-section {
	margin-bottom: 30px;
}

.metrics-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: 20px;
}

.metric-card {
	background: white;
	border-radius: 12px;
	padding: 25px;
	display: flex;
	align-items: center;
	gap: 20px;
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
	transition: transform 0.3s ease;
}

.metric-card:hover {
	transform: translateY(-5px);
}

.metric-icon {
	width: 60px;
	height: 60px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24px;
	color: white;
}

.metric-content h3 {
	margin: 0 0 8px 0;
	color: #2c3e50;
	font-size: 16px;
	font-weight: 600;
}
.chart-card {
	border-radius: 12px;
	border: none;
	transition: transform 0.3s;
}

.chart-card:hover {
	transform: translateY(-5px);
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.card-title {
	font-size: 18px;
	font-weight: 600;
	color: #2c3e50;
}

.hot-list {
	flex: 1;
	overflow-y: auto;
	padding-right: 4px;
}

.recent-list {
	flex: 1;
	overflow-y: auto;
	padding-right: 4px;
	max-height: 400px;
}

.recent-item {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 12px;
	border-bottom: 1px dashed #eee;
	transition: background-color 0.3s;
}

.recent-item:hover {
	background-color: #f5f5f5;
}

.recent-icon {
	width: 40px;
	height: 40px;
	border-radius: 8px;
	background: #e3f2fd;
	color: #2196f3;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 20px;
}

.recent-content {
	flex: 1;
	min-width: 0;
}

.recent-title {
	font-size: 14px;
	color: #2c3e50;
	font-weight: 600;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	margin-bottom: 4px;
}

.recent-meta {
	font-size: 12px;
	color: #7f8c8d;
	display: flex;
	gap: 10px;
	flex-wrap: wrap;
}

.recent-type {
	color: #3498db;
	font-weight: 500;
}

.recent-size {
	color: #7f8c8d;
}

.recent-time {
	color: #95a5a6;
}

.recent-status {
	padding: 4px 12px;
	border-radius: 12px;
	font-size: 12px;
	font-weight: 500;
}

.status-uploaded {
	background: #e3f2fd;
	color: #2196f3;
}

.status-parsed {
	background: #fff3e0;
	color: #ff9800;
}

.status-processed {
	background: #e8f5e9;
	color: #4caf50;
}

.status-error {
	background: #ffebee;
	color: #f44336;
}

.empty-state {
	text-align: center;
	padding: 40px;
	color: #999;
}

.hot-heat {
}

.hot-heat.top-attention {
	background: #fde2e6;
	color: #e0245e;
	padding: 2px 6px;
	border-radius: 6px;
	font-weight: 600;
}

.hot-tag {
	color: #c86b80;
}

:deep(.el-table) {
	--el-table-header-bg-color: #f8f9fa;
	--el-table-row-hover-bg-color: #f8f9fa;
}

:deep(.el-table__body tr:hover>td) {
	background-color: rgba(76, 175, 80, 0.1) !important;
}
</style>
