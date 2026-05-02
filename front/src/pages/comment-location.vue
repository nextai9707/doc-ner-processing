<template>
	<div class="source-container">
		<el-row :gutter="20">
			<el-col :span="14">
				<el-card class="chart-card">
					<template #header>
						<div class="card-header">
							<span>评论地区 Top10</span>
						</div>
					</template>
					<div ref="regionRef" class="chart"></div>
				</el-card>
			</el-col>
			<el-col :span="10">
				<el-card class="chart-card">
					<template #header>
						<div class="card-header">
							<span>评论点赞分布</span>
						</div>
					</template>
					<div ref="genderRef" class="chart"></div>
				</el-card>
			</el-col>
		</el-row>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { adminRequest } from '@/composables/adminRequest'

const regionRef = ref<HTMLElement>()
const genderRef = ref<HTMLElement>()

const fetchRegion = async () => {
	const sql = `SELECT 
		location as name, 
		COUNT(*) as value 
	FROM bili_food_comments 
	WHERE location IS NOT NULL AND location != ''
	GROUP BY location
	ORDER BY value DESC
	LIMIT 10`
	const res: any = await adminRequest.post('/api/mysql', { sql })
	return Array.isArray(res) ? res : (res?.data || [])
}

const fetchGender = async () => {
	// 由于 bili_food_comments 表没有性别字段，这里返回空数据或使用其他数据源
	// 如果需要性别分布，可能需要从其他表获取或使用默认数据
	return []
}
const renderRegion = async () => {
	const data = await fetchRegion()
	if (!regionRef.value) return
	const chart = echarts.init(regionRef.value)
	chart.setOption({
		tooltip: { trigger: 'axis' },
		grid: { left: '3%', right: '4%', bottom: '10%', top: '10%', containLabel: true },
		xAxis: { type: 'category', data: data.map((d: any) => d.name), axisLabel: { interval: 0, rotate: 30 } },
		yAxis: { type: 'value', name: '评论数' },
		series: [{
			name: '评论数',
			type: 'bar',
			data: data.map((d: any) => d.value),
			itemStyle: {
				color: new (echarts as any).graphic.LinearGradient(0, 0, 0, 1, [
					{ offset: 0, color: '#42a5f5' },
					{ offset: 1, color: '#1e88e5' }
				]),
				borderRadius: [6, 6, 0, 0]
			}
		}]
	})
	window.addEventListener('resize', () => chart.resize())
}

const renderGender = async () => {
	if (!genderRef.value) return
	try {
		const sql = `SELECT 
			CASE 
				WHEN like_count = 0 THEN '0点赞'
				WHEN like_count BETWEEN 1 AND 10 THEN '1-10点赞'
				WHEN like_count BETWEEN 11 AND 50 THEN '11-50点赞'
				WHEN like_count BETWEEN 51 AND 100 THEN '51-100点赞'
				ELSE '100+点赞'
			END as name,
			COUNT(*) as value
		FROM bili_food_comments
		GROUP BY 
			CASE 
				WHEN like_count = 0 THEN '0点赞'
				WHEN like_count BETWEEN 1 AND 10 THEN '1-10点赞'
				WHEN like_count BETWEEN 11 AND 50 THEN '11-50点赞'
				WHEN like_count BETWEEN 51 AND 100 THEN '51-100点赞'
				ELSE '100+点赞'
			END
		ORDER BY 
			CASE 
				WHEN name = '0点赞' THEN 1
				WHEN name = '1-10点赞' THEN 2
				WHEN name = '11-50点赞' THEN 3
				WHEN name = '51-100点赞' THEN 4
				ELSE 5
			END`
		const res: any = await adminRequest.post('/api/mysql', { sql })
		const data = Array.isArray(res) ? res : (res?.data || [])
		
		const chart = echarts.init(genderRef.value)
		chart.setOption({
			tooltip: { trigger: 'item' },
			legend: { bottom: 0, icon: 'circle' },
			color: ['#00A1D6', '#4db8e0', '#80c9e6', '#b3daed', '#ff9800'],
			series: [{
				name: '点赞分布',
				type: 'pie',
				roseType: 'area',
				radius: ['30%', '85%'],
				center: ['50%', '45%'],
				data,
				label: {
					show: true,
					formatter: '{b}\n{c}条 ({d}%)'
				},
				labelLine: { length: 15, length2: 12, smooth: true },
				itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2, shadowBlur: 18, shadowColor: 'rgba(0,0,0,0.2)' },
				emphasis: { scale: true, scaleSize: 8, itemStyle: { shadowBlur: 28, shadowColor: 'rgba(0,0,0,0.35)' } }
			}],
			animationEasing: 'elasticOut',
			animationDelay: (idx) => idx * 60
		})
		window.addEventListener('resize', () => chart.resize())
	} catch (e) {
		console.error('获取点赞分布失败:', e)
	}
}

onMounted(() => {
	nextTick(() => {
		renderRegion()
		renderGender()
	})
})
</script>

<style scoped>
.source-container {
	padding: 20px;
}
.chart-card {
	border-radius: 12px;
}
.card-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
}
.chart {
	width: 100%;
	height: 360px;
}
</style>

