<template>
		<!-- B站评论词云图 -->
		<el-card class="chart-card main-chart" style="margin-bottom: 10px;">
			<div class="chart-header">
				<h3>B站用户词云图</h3>
			</div>
			<div class="chart-content">
				<div ref="wordCloudRef" class="chart"></div>
			</div>
		</el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import { adminRequest } from '@/composables/adminRequest'

// 词云图引用
const wordCloudRef = ref<HTMLElement>()
const renderWordCloud = async () => {
    const res: any = await adminRequest.get('/api/user_wordcloud')
    const data = Array.isArray(res?.data) ? res.data : (res || [])
    if (!wordCloudRef.value) return
    const chart = echarts.init(wordCloudRef.value)
    chart.setOption({
        tooltip: { show: true },
        series: [{
            type: 'wordCloud',
            shape: 'circle',
            gridSize: 8,
            sizeRange: [12, 48],
            rotationRange: [-45, 90],
            textStyle: {
                color() {
                    const colors = ['#e0245e', '#c86b80', '#9c27b0', '#2196f3', '#ff9800', '#2e7d32']
                    return colors[Math.floor(Math.random() * colors.length)]
                }
            },
            data
        }]
    })
    window.addEventListener('resize', () => chart.resize())
}
onMounted(() => {
	// 使用nextTick确保DOM完全渲染后再初始化图表
	nextTick(() => {
        renderWordCloud()
	})
})
</script>

<style scoped>
.page-header h1 {
	color: #2c3e50;
	margin-bottom: 10px;
	font-size: 28px;
}
.page-header p {
	color: #7f8c8d;
	font-size: 16px;
}
.crop-info h3 {
	margin: 0 0 10px 0;
	color: #2c3e50;
	font-size: 18px;
}
.chart-card {
	background: white;
	border-radius: 12px;
	padding: 20px;

}
.main-chart {
	min-height: 350px;
}
.chart-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.chart-header h3 {
	margin: 0;
	color: #2c3e50;
	font-size: 18px;
}
.chart-content {
	height: 350px;
}
.chart {
	width: 100%;
	height: 100%;
}
.analysis-header h3 {
	margin: 0;
	color: #2c3e50;
	font-size: 16px;
}
.details-header h3 {
	margin: 0;
	color: #2c3e50;
	font-size: 18px;
}
</style>

