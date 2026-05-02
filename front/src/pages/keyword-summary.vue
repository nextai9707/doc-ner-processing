<template>
	<div class="keyword-summary-container">
		<el-card class="main-card">
			<template #header>
				<div class="card-header">
					<span class="card-title">🔑 关键词与摘要生成</span>
					<span class="card-subtitle">支持TF-IDF、TextRank算法；摘要使用TextRank句子级抽取</span>
				</div>
			</template>

			<!-- 文档选择 -->
			<div class="section">
				<h3>选择文档</h3>
				<el-select
					v-model="selectedDocumentId"
					placeholder="请选择要处理的文档"
					style="width: 100%"
					@change="onDocumentChange"
				>
					<el-option
						v-for="doc in documentList"
						:key="doc.id"
						:label="doc.original_filename"
						:value="doc.id"
						:disabled="doc.status !== 'parsed' && doc.status !== 'processed'"
					/>
				</el-select>
			</div>

			<!-- 算法配置 -->
			<div class="section" v-if="selectedDocumentId">
				<h3>算法配置</h3>
				<el-form :model="config" label-width="140px">
					<el-form-item label="生成类型">
						<el-checkbox-group v-model="config.types">
							<el-checkbox label="keyword">关键词</el-checkbox>
							<el-checkbox label="summary">摘要</el-checkbox>
						</el-checkbox-group>
					</el-form-item>
					<el-form-item label="关键词算法">
						<el-radio-group v-model="config.keyword_algorithm">
							<el-radio label="tfidf">TF-IDF</el-radio>
							<el-radio label="textrank">TextRank</el-radio>
						</el-radio-group>
					</el-form-item>
					<el-form-item label="关键词数量">
						<el-slider v-model="config.keyword_count" :min="5" :max="50" show-input />
					</el-form-item>
					<el-form-item label="摘要长度（字符）">
						<el-slider v-model="config.summary_length" :min="100" :max="1000" show-input />
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="generate" :loading="processing">
							开始生成
						</el-button>
					</el-form-item>
				</el-form>
			</div>

			<!-- 结果展示 -->
			<div class="section" v-if="result">
				<div class="result-header">
					<h3>生成结果</h3>
					<div class="export-actions">
						<el-button size="small" @click="exportResult('json')">导出JSON</el-button>
						<el-button size="small" type="success" @click="exportResult('excel')">导出Excel</el-button>
						<el-button size="small" type="warning" @click="exportResult('csv')">导出CSV</el-button>
					</div>
				</div>

				<el-tabs v-model="activeTab">
					<!-- 关键词结果 -->
					<el-tab-pane label="关键词" name="keyword" v-if="result.keywords">
						<div class="result-content">
							<div class="keywords-visual">
								<div
									v-for="(item, idx) in result.keywords"
									:key="idx"
									class="keyword-item"
								>
									<div class="keyword-rank">{{ idx + 1 }}</div>
									<div class="keyword-body">
										<el-tag
											:type="idx < 3 ? 'danger' : idx < 10 ? 'warning' : 'info'"
											size="large"
											class="keyword-tag"
										>
											{{ item.word }}
										</el-tag>
										<div class="keyword-bar-container">
											<el-progress
												:percentage="Math.min(100, (item.score / result.keywords[0].score) * 100)"
												:color="getKeywordColor(idx)"
												:stroke-width="12"
												:text-inside="true"
											/>
										</div>
										<span class="keyword-score">{{ item.score?.toFixed(4) }}</span>
									</div>
								</div>
							</div>
							<el-divider />
							<div class="keywords-table">
								<el-table :data="result.keywords" stripe size="small" border>
									<el-table-column type="index" label="排名" width="60" align="center" />
									<el-table-column prop="word" label="关键词" min-width="150" />
									<el-table-column prop="score" label="权重" width="120">
										<template #default="{ row }">
											<el-progress :percentage="Math.min(100, row.score * 100)" :stroke-width="8" />
										</template>
									</el-table-column>
								</el-table>
							</div>
						</div>
					</el-tab-pane>

					<!-- 摘要结果 -->
					<el-tab-pane label="抽取式摘要" name="summary" v-if="result.summary">
						<div class="result-content">
							<div class="summary-info">
								<el-descriptions :column="3" border size="small">
									<el-descriptions-item label="算法">TextRank 句子级抽取</el-descriptions-item>
									<el-descriptions-item label="目标长度">{{ config.summary_length }} 字符</el-descriptions-item>
									<el-descriptions-item label="实际长度">{{ result.summary_length_actual }} 字符</el-descriptions-item>
								</el-descriptions>
							</div>
							<div class="summary-text-box">
								<p class="summary-label">摘要内容：</p>
								<p class="summary-text">{{ result.summary }}</p>
							</div>
							<div class="summary-features">
								<el-alert
									title="摘要特性"
									type="success"
									:closable="false"
								>
									<div class="feature-list">
										<li>✅ 已自动过滤页眉页脚</li>
										<li>✅ 已自动过滤乱码和特殊符号</li>
										<li>✅ 已自动去除重复文本</li>
										<li>✅ 基于句子重要性排序抽取</li>
									</div>
								</el-alert>
							</div>
						</div>
					</el-tab-pane>
				</el-tabs>
			</div>
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminRequest } from '@/composables/adminRequest'

const selectedDocumentId = ref<number | null>(null)
const documentList = ref<any[]>([])
const processing = ref(false)
const activeTab = ref('keyword')
const result = ref<any>(null)
const currentTaskId = ref<number | null>(null)


const sortedSentences = computed(() => {
    if (!result.value?.summary_all_sentences || !result.value?.summary_sentence_scores) return []
    return result.value.summary_all_sentences
        .map((text: string, index: number) => ({
            index,
            text,
            score: result.value.summary_sentence_scores[index] || 0
        }))
        .sort((a: any, b: any) => b.score - a.score)
        .slice(0, 20)  // 只展示前 20 句
})

const maxScore = computed(() => {
    const scores = result.value?.summary_sentence_scores || []
    return scores.length ? Math.max(...scores) : 1
})

const isSelected = (index: number): boolean => {
    return (result.value?.summary_selected_indices || []).includes(index)
}

const config = reactive({
	types: ['keyword', 'summary'],
	keyword_algorithm: 'tfidf',
	keyword_count: 20,
	summary_length: 200
})

const getKeywordColor = (idx: number) => {
	if (idx < 3) return '#f56c6c'
	if (idx < 10) return '#e6a23c'
	return '#909399'
}

const onDocumentChange = () => {
	result.value = null
	currentTaskId.value = null
}

const fetchDocuments = async () => {
	try {
		const res: any = await adminRequest.get('/api/document/list?limit=100')
		if (res?.data?.list) {
			documentList.value = res.data.list.filter((doc: any) => doc.status === 'parsed' || doc.status === 'processed')
		}
	} catch (e) {
		ElMessage.error('获取文档列表失败')
	}
}

const generate = async () => {
	if (!selectedDocumentId.value) {
		ElMessage.warning('请先选择文档')
		return
	}

	processing.value = true
	try {
		const res: any = await adminRequest.post('/api/keyword-summary/generate', {
			document_id: selectedDocumentId.value,
			config: config
		})

		result.value = res.data
		currentTaskId.value = res.data?.task_id || null
		ElMessage.success('生成完成')
		if (result.value.keywords) {
			activeTab.value = 'keyword'
		} else if (result.value.summary) {
			activeTab.value = 'summary'
		}
	} catch (e: any) {
		ElMessage.error(e?.message || '生成失败')
	} finally {
		processing.value = false
	}
}

const exportResult = async (format: string) => {
	if (!currentTaskId.value) {
		ElMessage.warning('请先生成结果')
		return
	}
	try {
		const res: any = await adminRequest.get(`/api/task/${currentTaskId.value}/export?format=${format}`, {
			responseType: 'blob'
		})
		const blob = new Blob([res])
		const url = window.URL.createObjectURL(blob)
		const link = document.createElement('a')
		link.href = url
		const extMap: Record<string, string> = { json: 'json', excel: 'xlsx', csv: 'csv' }
		link.download = `keyword_summary_result.${extMap[format]}`
		link.click()
		window.URL.revokeObjectURL(url)
		ElMessage.success('导出成功')
	} catch (e) {
		ElMessage.error('导出失败')
	}
}

onMounted(() => {
	fetchDocuments()
})
</script>

<style scoped>
.keyword-summary-container {
	padding: 20px;
}

.main-card {
	border-radius: 8px;
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

.card-subtitle {
	font-size: 14px;
	color: #7f8c8d;
}

.section {
	margin-bottom: 30px;
}

.section h3 {
	margin-bottom: 15px;
	color: #2c3e50;
	font-size: 16px;
}

.result-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.result-header h3 {
	margin: 0;
	color: #2c3e50;
	font-size: 16px;
}

.export-actions {
	display: flex;
	gap: 8px;
}

.result-content {
	padding: 20px;
	background: #f5f5f5;
	border-radius: 4px;
	min-height: 200px;
}

.keywords-visual {
	display: flex;
	flex-direction: column;
	gap: 12px;
	margin-bottom: 20px;
}

.keyword-item {
	display: flex;
	align-items: center;
	gap: 12px;
	background: white;
	padding: 12px 16px;
	border-radius: 8px;
}

.keyword-rank {
	width: 32px;
	height: 32px;
	border-radius: 50%;
	background: #3498db;
	color: white;
	display: flex;
	align-items: center;
	justify-content: center;
	font-weight: 600;
	font-size: 14px;
	flex-shrink: 0;
}

.keyword-body {
	flex: 1;
	display: flex;
	align-items: center;
	gap: 12px;
}

.keyword-tag {
	flex-shrink: 0;
	min-width: 80px;
	text-align: center;
}

.keyword-bar-container {
	flex: 1;
}

.keyword-score {
	color: #909399;
	font-size: 13px;
	width: 70px;
	text-align: right;
	flex-shrink: 0;
}

.summary-info {
	margin-bottom: 20px;
}

.summary-text-box {
	background: white;
	padding: 20px;
	border-radius: 8px;
	margin-bottom: 20px;
}

.summary-label {
	font-weight: 600;
	color: #2c3e50;
	margin-bottom: 12px;
	font-size: 14px;
}

.summary-text {
	line-height: 1.8;
	font-size: 15px;
	color: #2c3e50;
	margin: 0;
	text-indent: 2em;
}
.sentences-visualization {
    margin-top: 24px;
    padding: 16px;
    background: white;
    border-radius: 8px;
    border: 1px solid #e4e7ed;
}
.sent-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    margin-bottom: 4px;
    border-radius: 4px;
    transition: background 0.2s;
    border-left: 3px solid transparent;
}
.sent-row.sent-selected {
    background: #f0f9eb;
    border-left-color: #67c23a;
    font-weight: 500;
}
.sent-rank {
    width: 40px;
    color: #909399;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    flex-shrink: 0;
}
.sent-score-bar {
    width: 140px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 6px;
}
.sent-score-text {
    font-size: 11px;
    color: #909399;
    font-family: 'Courier New', monospace;
    width: 56px;
}
.sent-text {
    flex: 1;
    font-size: 13px;
    color: #2c3e50;
    line-height: 1.6;
}
.summary-features {
	.feature-list {
		margin: 0;
		padding-left: 20px;
	}
	.feature-list li {
		margin-bottom: 6px;
		color: #67c23a;
	}
}
</style>
