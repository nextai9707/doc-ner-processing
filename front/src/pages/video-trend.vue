<template>
	<div class="yield-trend-container">


		<!-- 关键指标 -->
		<div class="metrics-section">
			<div class="metric-card">
				<div class="metric-icon">
					<el-icon>
						<VideoPlay />
					</el-icon>
				</div>
				<div class="metric-content">
					<h3>视频总数</h3>
					<div class="metric-value">{{ stats.totalVideos }}</div>
				</div>
			</div>
			<div class="metric-card">
				<div class="metric-icon">
					<el-icon>
						<View />
					</el-icon>
				</div>
				<div class="metric-content">
					<h3>总播放量</h3>
					<div class="metric-value">{{ formatNumber(stats.totalViews) }}</div>
				</div>
			</div>

			<div class="metric-card">
				<div class="metric-icon">

				</div>
				<div class="metric-content">
					<h3>总点赞数</h3>
					<div class="metric-value">{{ formatNumber(stats.totalLikes) }}</div>
				</div>
			</div>
			<div class="metric-card">
				<div class="metric-icon">
					<el-icon>
						<ChatLineRound />
					</el-icon>
				</div>
				<div class="metric-content">
					<h3>总评论数</h3>
					<div class="metric-value">{{ formatNumber(stats.totalComments) }}</div>
				</div>
			</div>
		</div>

		<!-- 图表区域 -->
		<div class="charts-section">
			<!-- 视频播放量趋势 -->
			<div class="chart-card">
				<div class="chart-header">
					<h3>视频播放量趋势</h3>
				</div>
				<div class="chart-content">
					<div ref="trendChart" class="chart"></div>
				</div>
			</div>

			<!-- 视频标签分布 -->
			<div class="chart-card">
				<div class="chart-header">
					<h3>视频标签分布</h3>
				</div>
				<div class="chart-content">
					<div ref="seasonalChart" class="chart"></div>
				</div>
			</div>
		</div>


	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, reactive } from 'vue'
import * as echarts from 'echarts'
import { VideoPlay, View, ChatLineRound } from '@element-plus/icons-vue'
import { adminRequest } from '@/composables/adminRequest'

// 图表引用
const trendChart = ref<HTMLElement>()
const seasonalChart = ref<HTMLElement>()

// 统计数据
const stats = reactive({
	totalVideos: 0,
	totalViews: 0,
	totalLikes: 0,
	totalComments: 0
})

// 格式化数字
const formatNumber = (num: number | string | null | undefined): string => {
	if (!num) return '0'
	const n = Number(num)
	if (isNaN(n)) return '0'
	if (n >= 10000) {
		return (n / 10000).toFixed(1) + '万'
	}
	return n.toString()
}

// 获取统计数据
const fetchStats = async () => {
	try {
		const sql = `SELECT * FROM ods_video_tongji`
		const res: any = await adminRequest.post('/api/mysql', { sql })
		const data = Array.isArray(res) ? res[0] : (res?.data?.[0] || {})
		stats.totalVideos = Number(data.total_videos || 0)
		stats.totalViews = Number(data.total_views || 0)
		stats.totalLikes = Number(data.total_likes || 0)
		stats.totalComments = Number(data.total_comments || 0)
	} catch (e) {
		console.error('获取统计数据失败:', e)
	}
}

// 初始化图表
const initCharts = () => {
	nextTick(() => {
		initTrendChart()
		initSeasonalChart()
	})
}

// 初始化视频播放量趋势
const initTrendChart = async () => {
	if (!trendChart.value) return
	try {
		const sql = `SELECT * FROM ods_video_total`
		const res: any = await adminRequest.post('/api/mysql', { sql })
		const data = Array.isArray(res) ? res : (res?.data || [])

		const dates = data.map((d: any) => {
			const date = new Date(d.date);
			return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
		}).reverse();
		const views = data.map((d: any) => Number(d.total_views || 0)).reverse()
		const trendChartInstance = echarts.init(trendChart.value)
		trendChartInstance.setOption({
			tooltip: { trigger: 'axis' },
			grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
			xAxis: {
				type: 'category',
				data: dates,
				axisLabel: {
					interval: 0,
					rotate: 45,
					fontSize: 12
				}
			},
			yAxis: { type: 'value', name: '播放量' },
			series: [{
				name: '播放量',
				type: 'line',
				data: views,
				smooth: true,
				itemStyle: { color: '#00A1D6' },
				lineStyle: { width: 3 },
				areaStyle: {
					color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
						{ offset: 0, color: 'rgba(0, 161, 214, 0.3)' },
						{ offset: 1, color: 'rgba(0, 161, 214, 0.1)' }
					])
				}
			}]
		})

		window.addEventListener('resize', () => {
			trendChartInstance.resize()
		})
	} catch (e) {
		console.error('获取播放量趋势失败:', e)
	}
}

// 初始化视频标签分布图
const initSeasonalChart = async () => {
	if (!seasonalChart.value) return
	try {
		const sql = `SELECT * FROM ods_video_tags`
		const res: any = await adminRequest.post('/api/mysql', { sql })
		const data = Array.isArray(res) ? res : (res?.data || [])
		const seasonalChartInstance = echarts.init(seasonalChart.value)
		seasonalChartInstance.setOption({
			tooltip: { trigger: 'item' },
			legend: { orient: 'vertical', left: 'left' },
			series: [{
				name: '视频标签分布',
				type: 'pie',
				radius: ['40%', '70%'],
				center: ['50%', '50%'],
				data: data,
				label: {
					show: true,
					formatter: '{b|{b}}\n{hr|}\n{d|{d}%}',
					rich: {
						b: { fontSize: 14, fontWeight: 'bold', color: '#333' },
						hr: { borderColor: '#aaa', width: '100%', borderWidth: 0.5, height: 0, lineHeight: 10 },
						d: { fontSize: 12, color: '#999' }
					}
				},
				labelLine: { length: 10, length2: 15, smooth: true },
				itemStyle: {
					borderRadius: 8,
					borderColor: '#fff',
					borderWidth: 2,
					shadowBlur: 10,
					shadowColor: 'rgba(0,0,0,0.2)'
				},
				emphasis: {
					scale: true,
					scaleSize: 10,
					itemStyle: { shadowBlur: 25, shadowColor: 'rgba(0,0,0,0.5)' }
				}
			}]
		})

		window.addEventListener('resize', () => {
			seasonalChartInstance.resize()
		})
	} catch (e) {
		console.error('获取标签分布失败:', e)
	}
}

onMounted(() => {
	fetchStats()
	initCharts()
})
</script>

<style scoped>
.yield-trend-container {
	padding: 20px;
	background: #f5f5f5;
	min-height: 100vh;
}

.page-header {
	text-align: center;
	margin-bottom: 30px;
}

.page-header h1 {
	color: #2c3e50;
	margin-bottom: 10px;
	font-size: 28px;
}

.page-header p {
	color: #7f8c8d;
	font-size: 16px;
}

.metrics-section {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
	gap: 20px;
	margin-bottom: 30px;
}

.metric-card {
	background: white;
	border-radius: 12px;
	padding: 20px;

	display: flex;
	align-items: center;
	gap: 15px;
}

.metric-icon {
	width: 60px;
	height: 60px;
	border-radius: 12px;
	background: linear-gradient(135deg, #4caf50, #2e7d32);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24px;
	color: white;
}

.metric-content h3 {
	margin: 0 0 8px 0;
	color: #666;
	font-size: 14px;
	font-weight: 500;
}

.metric-value {
	font-size: 24px;
	font-weight: bold;
	color: #2c3e50;
	margin-bottom: 4px;
}

.charts-section {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 20px;
	margin-bottom: 30px;
}

.chart-card {
	background: white;
	border-radius: 12px;
	padding: 20px;

}

.chart-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 15px;
}

.chart-header h3 {
	margin: 0;
	color: #2c3e50;
	font-size: 16px;
}

.chart-content {
	height: 300px;
}

.chart {
	width: 100%;
	height: 100%;
}

.table-header h3 {
	margin: 0;
	color: #2c3e50;
	font-size: 18px;
}

</style>
