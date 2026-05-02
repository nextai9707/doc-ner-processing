<template>

	<el-card shadow="never">
		<el-form :inline="true" @submit.prevent>
			<el-form-item label="评论地区">
				<el-input v-model="querySource" placeholder="请输入评论地区" clearable @keyup.enter="doSearch" />
			</el-form-item>
			<el-form-item label="情感倾向">
				<el-select v-model="queryNlp" placeholder="选择情感" clearable style="width: 160px;">
					<el-option label="积极" value="positive" />
					<el-option label="中性" value="neutral" />
					<el-option label="消极" value="negative" />
				</el-select>
			</el-form-item>
			<el-form-item>
				<el-button type="primary" @click="doSearch">查询</el-button>
				<el-button @click="resetSearch">重置</el-button>
			</el-form-item>
		</el-form>
		<!-- 统计积极 中性 消极 -->
		<div class="stats-bar">
			<div class="stat-item positive">
				<div class="stat-label">积极评论</div>
				<div class="stat-value">{{ stats.positive }}</div>
				<div class="stat-desc">点赞数 > 10</div>
			</div>
			<div class="stat-item neutral">
				<div class="stat-label">中性评论</div>
				<div class="stat-value">{{ stats.neutral }}</div>
				<div class="stat-desc">点赞数 1-10</div>
			</div>
			<div class="stat-item negative">
				<div class="stat-label">消极评论</div>
				<div class="stat-value">{{ stats.negative }}</div>
				<div class="stat-desc">点赞数 = 0</div>
			</div>
		</div>

	</el-card>
	<div style="height: 20px"></div>
	<el-card shadow="never">

		<el-table :data="tableData" style="width: 100%" stripe>
			<el-table-column prop="user" label="用户" width="160" align="center" />
			<el-table-column prop="location" label="评论地区" width="160" align="center" />
			<el-table-column prop="content" label="评论内容" align="center" show-overflow-tooltip />
			<el-table-column label="情感倾向" width="160" align="center">
				<template #default="scope">
					<el-tag :type="emotionTagType(scope.row.like_count)">
						{{ emotionLabel(scope.row.like_count) }}
					</el-tag>
				</template>
			</el-table-column>
			<el-table-column prop="like_count" label="点赞数" width="120" align="center" />
			<el-table-column prop="ctime" label="评论时间" width="180" align="center">
				<template #default="scope">
					{{ formatDate(scope.row.ctime) }}
				</template>
			</el-table-column>
		</el-table>
		<div class="pager">
			<el-pagination
				background
				layout="prev, pager, next, jumper, sizes, total"
				:total="total"
				:current-page="current"
				:page-size="size"
				:page-sizes="[10, 20, 50, 100]"
				@current-change="onPageChange"
				@size-change="onSizeChange"
			/>
		</div>
	</el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminRequest } from '@/composables/adminRequest'

const tableData = ref<any[]>([])
const total = ref(0)
const current = ref(1)
const size = ref(20)
const querySource = ref('')
const queryNlp = ref('')
const stats = ref({ positive: 0, neutral: 0, negative: 0 })

const buildSql = () => {
	const offset = (current.value - 1) * size.value
	// 统计总数与分页数据分两次查询，避免复杂 SQL 分页统计
	const where: string[] = []
	if (querySource.value && querySource.value.trim()) {
		where.push(`location LIKE '%${querySource.value.trim().replaceAll('\'', '\\\'')}%'`)
	}
	// 根据点赞数判断情感倾向
	if (queryNlp.value && queryNlp.value.trim()) {
		const s = queryNlp.value.trim()
		if (s === 'negative') where.push(`like_count = 0`)
		if (s === 'neutral') where.push(`like_count BETWEEN 1 AND 10`)
		if (s === 'positive') where.push(`like_count > 10`)
	}
	const whereSql = where.length ? `WHERE ${where.join(' AND ')}` : ''
	return {
		countSql: `SELECT COUNT(1) AS c FROM bili_food_comments ${whereSql}`,
		statsSql: `SELECT
			SUM(CASE WHEN like_count = 0 THEN 1 ELSE 0 END) AS negative,
			SUM(CASE WHEN like_count BETWEEN 1 AND 10 THEN 1 ELSE 0 END) AS neutral,
			SUM(CASE WHEN like_count > 10 THEN 1 ELSE 0 END) AS positive
			FROM bili_food_comments ${whereSql}`,
		pageSql: `SELECT id, user, content, location, like_count, ctime
				  FROM bili_food_comments
				  ${whereSql}
				  ORDER BY ctime DESC
				  LIMIT ${size.value} OFFSET ${offset}`
	}
}
const loadData = async () => {
	const { countSql, statsSql, pageSql } = buildSql()
	// 获取总数
	const countRes: any = await adminRequest.post('/api/mysql', { sql: countSql })
	const countRow = Array.isArray(countRes) ? countRes[0] : countRes?.data?.[0]
	total.value = Number(countRow?.c || 0)
	// 获取情感统计
	const statsRes: any = await adminRequest.post('/api/mysql', { sql: statsSql })
	const sRow = Array.isArray(statsRes) ? statsRes[0] : statsRes?.data?.[0]
	stats.value = {
		positive: Number(sRow?.positive || 0),
		neutral: Number(sRow?.neutral || 0),
		negative: Number(sRow?.negative || 0)
	}
	// 获取分页数据
	const pageRes: any = await adminRequest.post('/api/mysql', { sql: pageSql })
	tableData.value = Array.isArray(pageRes) ? pageRes : (pageRes?.data || [])
}

const onPageChange = (p: number) => {
	current.value = p
	loadData()
}
const onSizeChange = (s: number) => {
	size.value = s
	current.value = 1
	loadData()
}

const pad2 = (n: number) => (n < 10 ? `0${n}` : `${n}`)
const formatDate = (val: any) => {
	if (!val) return ''
	const d = new Date(val)
	if (isNaN(d.getTime())) return String(val)
	const yyyy = d.getFullYear()
	const mm = pad2(d.getMonth() + 1)
	const dd = pad2(d.getDate())
	const hh = pad2(d.getHours())
	const mi = pad2(d.getMinutes())
	const ss = pad2(d.getSeconds())
	return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
}

const emotionLabel = (likeCount: any) => {
	const v = Number(likeCount)
	if (isNaN(v)) return '未知'
	if (v === 0) return '消极'
	if (v <= 10) return '中性'
	return '积极'
}

const emotionTagType = (likeCount: any): 'danger' | 'warning' | 'success' | '' => {
	const v = Number(likeCount)
	if (isNaN(v)) return ''
	if (v === 0) return 'danger'
	if (v <= 10) return 'warning'
	return 'success'
}

onMounted(loadData)
const doSearch = () => {
	current.value = 1
	loadData()
}
const resetSearch = () => {
	querySource.value = ''
	queryNlp.value = ''
	current.value = 1
	loadData()
}
</script>

<style scoped>
.emotion-container {
	padding: 20px;
}

.toolbar {
	margin-bottom: 12px;
}

.card-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.pager {
	margin-top: 16px;
	display: flex;
	justify-content: flex-end;
}

.stats-bar {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 12px;
	margin-top: 8px;
	margin-bottom: 4px;
	background: #fff;
	padding: 8px 0;
}
.stat-item {
	border-radius: 8px;
	padding: 10px 12px;
	text-align: center;
	background: #f8f9fa;
}
.stat-item .stat-label {
	font-size: 12px;
	color: #7f8c8d;
	margin-bottom: 6px;
}
.stat-item .stat-value {
	font-size: 24px;
	font-weight: 700;
}
.stat-item .stat-desc {
	font-size: 12px;
	color: #999;
	margin-top: 4px;
}
.stat-item.positive .stat-value { color: #2e7d32; }
.stat-item.neutral .stat-value { color: #ff9800; }
.stat-item.negative .stat-value { color: #d32f2f; }
</style>
